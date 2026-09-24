"""keyline render: one PNG per slide through OfficeCLI, then a contact sheet (spec §7).

OfficeCLI is optional. It is needed only here, never by `keyline lint`.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

INSTALL = "npm install -g @officecli/officecli"
L002 = (
    "note (L-002): OfficeCLI renders fall back to sans-serif for any font that is not "
    "installed, so these PNGs cannot verify typography.\n"
)
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


def render(deck: str | Path, out_dir: str | Path) -> RenderResult:
    sys.stderr.write(L002)
    deck, out_dir = Path(deck), Path(out_dir)
    officecli = shutil.which("officecli")
    if officecli is None:
        raise RenderError(f"officecli is not installed; install it with: {INSTALL}")
    if not deck.is_file():
        raise RenderError(f"no such file: {deck}")
    count = slide_count(deck)
    out_dir.mkdir(parents=True, exist_ok=True)
    pngs = []
    for i in range(1, count + 1):
        png = out_dir / f"slide-{i:02d}.png"
        cmd = [officecli, "view", str(deck), "screenshot", "--page", str(i), "-o", str(png)]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=SLIDE_TIMEOUT_S)
        except subprocess.TimeoutExpired as exc:
            raise RenderError(f"officecli timed out on slide {i}") from exc
        if proc.returncode != 0 or not png.is_file():
            detail = (proc.stderr or proc.stdout).strip().splitlines()
            reason = detail[-1] if detail else f"exit {proc.returncode}"
            raise RenderError(f"officecli failed on slide {i}: {reason}")
        pngs.append(png)
    return RenderResult(pngs, contact_sheet(pngs, out_dir / "contact.png"))
