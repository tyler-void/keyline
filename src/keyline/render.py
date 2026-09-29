"""keyline render: one PNG per slide, then a contact sheet (spec 001 §7, spec 002 §7).

Two engines. `libreoffice` converts the deck to PDF with soffice and rasterizes it with
pypdfium2 (imported lazily) or pdftoppm; `officecli` screenshots each slide. `auto` uses
LibreOffice when soffice and a rasterizer are both found, else OfficeCLI. Both are
optional and needed only here, never by `keyline lint`. Every render prints the known
limits of its engine and, for LibreOffice, the version it ran on (amendment B-7).
"""

from __future__ import annotations

import contextlib
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ENGINES = ("auto", "libreoffice", "officecli")
INSTALL = "npm install -g @officecli/officecli"
LO_INSTALL = (
    "install LibreOffice (https://www.libreoffice.org/download/) and a rasterizer: "
    "pip install pypdfium2, or poppler's pdftoppm"
)
L002 = (
    "note (L-002): OfficeCLI renders fall back to sans-serif for any font that is not "
    "installed, so these PNGs cannot verify typography.\n"
)
L010 = (
    "note (L-010): LibreOffice re-fits stored autofit text and substitutes fonts through "
    "fontconfig, so line breaks can differ from PowerPoint's.\n"
)
SOFFICE_PATHS = (
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    r"C:\Program Files\LibreOffice\program\soffice.exe",
)
PNG_WIDTH = 1280
LO_TIMEOUT_S = 120
# B-13: hidden slides are exported too, so page N of the PDF is deck slide N
LO_PDF_FILTER = 'pdf:impress_pdf_Export:{"ExportHiddenSlides":{"type":"boolean","value":"true"}}'
COLUMNS = 3
TILE_WIDTH = 480
GUTTER = 16
LABEL_HEIGHT = 20
SLIDE_TIMEOUT_S = 120


class RenderError(Exception):
    """Rendering failed; the message is a one-line reason."""


@dataclass(frozen=True)
class RenderResult:
    slides: list[Path]
    contact: Path
    engine: str = "officecli"
    version: str = ""  # LibreOffice's `soffice --version` line (B-7)


def slide_count(deck: Path) -> int:
    from keyline.ooxml.ns import NS
    from keyline.ooxml.package import Package, ScanError

    try:
        with Package(deck) as pkg:
            return len(pkg.xml(pkg.main_part).findall("p:sldIdLst/p:sldId", NS))
    except ScanError as exc:
        raise RenderError(f"cannot read {deck.name}: {exc}") from exc


def contact_sheet(pngs: list[Path], out: Path) -> Path:
    """A COLUMNS-wide grid of slide thumbnails, each labelled with its slide number."""
    from PIL import Image, ImageDraw, ImageFont  # lazy, so `keyline doctor` runs without it

    if not pngs:
        raise RenderError("no slide images to put on a contact sheet")
    thumbs = []
    for p in pngs:
        with Image.open(p) as im:
            im = im.convert("RGB")
            height = round(im.height * TILE_WIDTH / im.width)
            thumbs.append(im.resize((TILE_WIDTH, height), Image.LANCZOS))
    tile_h = max(t.height for t in thumbs) + LABEL_HEIGHT
    rows = (len(thumbs) + COLUMNS - 1) // COLUMNS
    cols = min(COLUMNS, len(thumbs))
    sheet = Image.new(
        "RGB",
        (GUTTER + cols * (TILE_WIDTH + GUTTER), GUTTER + rows * (tile_h + GUTTER)),
        (255, 255, 255),
    )
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, t in enumerate(thumbs):
        x = GUTTER + (i % COLUMNS) * (TILE_WIDTH + GUTTER)
        y = GUTTER + (i // COLUMNS) * (tile_h + GUTTER)
        draw.text((x, y + 4), f"{i + 1}", fill=(0, 0, 0), font=font)
        sheet.paste(t, (x, y + LABEL_HEIGHT))
        draw.rectangle(
            (x - 1, y + LABEL_HEIGHT - 1, x + t.width, y + LABEL_HEIGHT + t.height),
            outline=(200, 200, 200),
        )
    sheet.save(out)
    return out


# ---------------------------------------------------------------------------------------
# finding the engines


def find_soffice() -> str | None:
    """soffice on PATH, then the standard install paths (§7)."""
    found = shutil.which("soffice")
    if found:
        return found
    for candidate in SOFFICE_PATHS:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def _pdfium_available() -> bool:
    try:
        import pypdfium2  # noqa: F401
    except ImportError:
        return False
    return True


def find_rasterizer() -> str | None:
    """ "pypdfium2" if it imports, else "pdftoppm" if it is on PATH, else None."""
    if _pdfium_available():
        return "pypdfium2"
    return "pdftoppm" if shutil.which("pdftoppm") else None


def libreoffice_version(soffice: str) -> str:
    try:
        proc = subprocess.run(
            [soffice, "--version"], capture_output=True, text=True, timeout=LO_TIMEOUT_S
        )
    except (OSError, subprocess.TimeoutExpired):
        return "LibreOffice (version unknown)"
    lines = proc.stdout.strip().splitlines()
    return lines[0].strip() if lines else "LibreOffice (version unknown)"


def choose(engine: str = "auto") -> str:
    """The engine that will run, or RenderError with the install hints."""
    if engine not in ENGINES:
        raise RenderError(f"unknown engine {engine!r}; expected one of {', '.join(ENGINES)}")
    from keyline.officecli import NOT_INSTALLED, status

    lo = find_soffice() is not None and find_rasterizer() is not None
    if engine == "libreoffice":
        if find_soffice() is None:
            raise RenderError(f"libreoffice is not installed; {LO_INSTALL}")
        if find_rasterizer() is None:
            raise RenderError("no rasterizer for LibreOffice: pip install pypdfium2, or pdftoppm")
        return "libreoffice"
    if engine == "officecli" or not lo:
        runnable, reason = status()  # an officecli that cannot start counts as absent (B-15)
        if runnable:
            return "officecli"
        # the M1 wording stays first (plan Q-11); auto adds the LibreOffice hint
        hint = "" if engine == "officecli" else f"; or {LO_INSTALL}"
        if reason == NOT_INSTALLED:
            raise RenderError(f"officecli is not installed; install it with: {INSTALL}{hint}")
        raise RenderError(f"{reason}{hint}")
    return "libreoffice"


# ---------------------------------------------------------------------------------------
# rendering


def png_name(index: int, count: int) -> str:
    """slide-NN.png for deck slide NN, zero-padded to max(2, digits of the count) (B-13)."""
    return f"slide-{index:0{max(2, len(str(count)))}d}.png"


def _prepare(out_dir: Path) -> None:
    """Create the output directory and remove an earlier render's PNGs (B-13)."""
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        for old in [*out_dir.glob("slide-*.png"), out_dir / "contact.png"]:
            if old.is_file():
                old.unlink()
    except OSError as exc:
        reason = exc.strerror or type(exc).__name__
        raise RenderError(f"cannot use {out_dir} as the output directory: {reason}") from exc


def render(deck: str | Path, out_dir: str | Path, engine: str = "auto") -> RenderResult:
    deck, out_dir = Path(deck), Path(out_dir)
    # the user's inputs first: no engine can render an empty deck or write to a file (B-13)
    if not deck.is_file():
        raise RenderError(f"no such file: {deck}")
    count = slide_count(deck)
    if count == 0:
        raise RenderError("deck has no slides")
    if out_dir.exists() and not out_dir.is_dir():
        raise RenderError(f"cannot use {out_dir} as the output directory: not a directory")
    try:
        chosen = choose(engine)
    except RenderError:
        if engine != "libreoffice":
            sys.stderr.write(L002)
        raise
    _prepare(out_dir)
    try:
        if chosen == "officecli":
            sys.stderr.write(L002)
            pngs = _render_officecli(deck, out_dir, count)
            return RenderResult(pngs, contact_sheet(pngs, out_dir / "contact.png"))
        soffice, raster = find_soffice(), find_rasterizer()
        version = libreoffice_version(soffice)
        sys.stderr.write(L010)
        sys.stderr.write(f"render engine: {version}, rasterized with {raster}\n")
        pngs = _render_libreoffice(deck, out_dir, soffice, raster, count)
        contact = contact_sheet(pngs, out_dir / "contact.png")
    except OSError as exc:  # e.g. the directory became unwritable
        raise RenderError(f"cannot write to {out_dir}: {exc.strerror or exc}") from exc
    return RenderResult(pngs, contact, "libreoffice", version)


def _run(cmd: list[str], timeout: float) -> subprocess.CompletedProcess:
    """Run in a process group of its own; on timeout kill the whole group, so that
    soffice's soffice.bin child dies too (B-13)."""
    group = (
        {"start_new_session": True}
        if os.name == "posix"
        else {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    )
    with subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **group
    ) as proc:
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                with contextlib.suppress(ProcessLookupError, PermissionError):
                    os.killpg(proc.pid, signal.SIGKILL)
            else:
                proc.kill()
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.communicate(timeout=10)
            raise
    return subprocess.CompletedProcess(cmd, proc.returncode, out, err)


def _render_officecli(deck: Path, out_dir: Path, count: int) -> list[Path]:
    from keyline.officecli import private_copy

    officecli = shutil.which("officecli")
    pngs = []
    with private_copy(deck) as copy:  # B-14: never the user's path (L-016)
        for i in range(1, count + 1):
            png = out_dir / png_name(i, count)
            cmd = [officecli, "view", str(copy), "screenshot", "--page", str(i), "-o", str(png)]
            try:
                proc = _run(cmd, SLIDE_TIMEOUT_S)
            except subprocess.TimeoutExpired as exc:
                raise RenderError(f"officecli timed out on slide {i}") from exc
            if proc.returncode != 0 or not png.is_file():
                detail = (proc.stderr or proc.stdout).strip().splitlines()
                reason = detail[-1] if detail else f"exit {proc.returncode}"
                raise RenderError(f"officecli failed on slide {i}: {reason}")
            pngs.append(png)
    return pngs


def convert_to_pdf(deck: Path, soffice: str, tmp_dir: Path) -> Path:
    """The deck as a PDF, hidden slides included (B-13), in `tmp_dir`.

    soffice converts a private copy with a fixed name (`deck.pptx`, or `deck.pptm` for a
    .pptm deck; B-19), so a symlink, an odd name or a name ending in "." cannot change the
    PDF's name, and the user's path never reaches the engine. The private profile and
    --outdir are both kept (§7)."""
    suffix = ".pptm" if deck.suffix.casefold() == ".pptm" else ".pptx"
    copy = tmp_dir / f"deck{suffix}"
    shutil.copyfile(deck, copy)
    pdf_dir = tmp_dir / "pdf"
    cmd = [
        soffice,
        "--headless",
        "--norestore",
        f"-env:UserInstallation={(tmp_dir / 'profile').as_uri()}",
        "--convert-to",
        LO_PDF_FILTER,
        "--outdir",
        str(pdf_dir),
        str(copy),
    ]
    try:
        proc = _run(cmd, LO_TIMEOUT_S)
    except subprocess.TimeoutExpired as exc:
        raise RenderError(f"libreoffice timed out after {LO_TIMEOUT_S} s") from exc
    pdf = pdf_dir / "deck.pdf"
    if not pdf.is_file():
        detail = (proc.stderr or proc.stdout).strip().splitlines()
        reason = detail[-1] if detail else f"exit {proc.returncode}"
        raise RenderError(f"libreoffice wrote no PDF: {reason}")
    return pdf


def _render_libreoffice(
    deck: Path, out_dir: Path, soffice: str, raster: str, count: int
) -> list[Path]:
    """The deck to PDF (convert_to_pdf), then one PNG per page. The temp directory is
    always removed."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="keyline-lo-"))
    try:
        pdf = convert_to_pdf(deck, soffice, tmp_dir)
        pngs = rasterize(pdf, out_dir, raster, tmp_dir, count)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    if len(pngs) != count:  # slide-NN.png must be deck slide NN (B-13)
        for png in pngs:
            png.unlink(missing_ok=True)
        raise RenderError(f"the PDF has {len(pngs)} pages for {count} slides")
    return pngs


def rasterize(pdf: Path, out_dir: Path, raster: str, tmp_dir: Path, count: int) -> list[Path]:
    """One PNG per PDF page, PNG_WIDTH pixels wide, named for a deck of `count` slides."""
    pngs = []
    if raster == "pypdfium2":
        import pypdfium2 as pdfium  # lazy: the render extra (plan §1)

        doc = pdfium.PdfDocument(str(pdf))
        try:
            for i, page in enumerate(doc, 1):
                image = page.render(scale=PNG_WIDTH / page.get_width()).to_pil()
                pngs.append(_save_png(image, out_dir / png_name(i, count)))
        finally:
            doc.close()
        return pngs
    prefix = tmp_dir / "page"
    cmd = ["pdftoppm", "-png", "-scale-to-x", str(PNG_WIDTH), "-scale-to-y", "-1"]
    proc = subprocess.run([*cmd, str(pdf), str(prefix)], capture_output=True, text=True)
    pages = sorted(
        (int(m.group(1)), p)
        for p in tmp_dir.glob("page-*.png")
        if (m := re.fullmatch(r"page-(\d+)\.png", p.name))
    )
    if proc.returncode != 0 or not pages:
        raise RenderError(f"pdftoppm failed: exit {proc.returncode}")
    from PIL import Image

    for i, page in pages:
        with Image.open(page) as image:
            pngs.append(_save_png(image, out_dir / png_name(i, count)))
    return pngs


def _save_png(image, path: Path) -> Path:
    from PIL import Image

    if image.width != PNG_WIDTH:
        height = round(image.height * PNG_WIDTH / image.width)
        image = image.resize((PNG_WIDTH, height), Image.LANCZOS)
    image.save(path)
    return path
