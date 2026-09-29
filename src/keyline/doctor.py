"""keyline doctor (spec 002 §7, amendment B-8.12): what this machine can do, one line per
check with a token the skill reacts to, and the install command for anything missing.

Runs without lxml and Pillow (it reports them missing), so it imports nothing heavy at
module level. Exit 0 when lint can run: Python >= 3.11 with lxml and Pillow.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

# font install hints, by metric twin (Debian/Ubuntu package names; CI uses them)
TWIN_HINTS = {
    "Liberation Sans": "apt install fonts-liberation",
    "Liberation Serif": "apt install fonts-liberation",
    "Liberation Mono": "apt install fonts-liberation",
    "Carlito": "apt install fonts-crosextra-carlito",
    "Caladea": "apt install fonts-crosextra-caladea",
    "Gelasio": "Gelasio-Regular.ttf and Gelasio-Bold.ttf from fonts/ttf in "
    "https://github.com/SorkinType/Gelasio (OFL-1.1)",
}
# plan Q-40: without fc-match, look for these file names (case-insensitive)
FONT_FILES = {
    "Arial": ("arial.ttf",),
    "Times New Roman": ("times.ttf", "times new roman.ttf"),
    "Courier New": ("cour.ttf", "courier new.ttf"),
    "Georgia": ("georgia.ttf",),
    "Calibri": ("calibri.ttf",),
    "Cambria": ("cambria.ttc", "cambria.ttf"),
    "Liberation Sans": ("liberationsans-regular.ttf",),
    "Liberation Serif": ("liberationserif-regular.ttf",),
    "Liberation Mono": ("liberationmono-regular.ttf",),
    "Gelasio": ("gelasio-regular.ttf",),
    "Carlito": ("carlito-regular.ttf",),
    "Caladea": ("caladea-regular.ttf",),
}


def font_dirs() -> list[Path]:
    home = Path.home()
    dirs = [
        Path("/System/Library/Fonts"),
        Path("/System/Library/Fonts/Supplemental"),
        Path("/Library/Fonts"),
        home / "Library/Fonts",
    ]
    if os.environ.get("WINDIR"):
        dirs.append(Path(os.environ["WINDIR"]) / "Fonts")
    if os.environ.get("LOCALAPPDATA"):
        dirs.append(Path(os.environ["LOCALAPPDATA"]) / "Microsoft/Windows/Fonts")
    dirs += [Path("/usr/share/fonts"), Path("/usr/local/share/fonts"), home / ".local/share/fonts"]
    return dirs


@dataclass(frozen=True)
class Line:
    check: str
    token: str
    detail: str
    hint: str = ""


def _module(name: str, attr: str = "__version__") -> str | None:
    try:
        module = __import__(name)
    except ImportError:
        return None
    return str(getattr(module, attr, "installed"))


def _core() -> list[Line]:
    v = sys.version_info
    py = f"Python {v.major}.{v.minor}.{v.micro}"
    lines = [
        Line("python", "PYTHON_OK", py)
        if v >= (3, 11)
        else Line("python", "PYTHON_OLD", py, "keyline needs Python 3.11 or later"),
    ]
    lxml = _module("lxml")
    lines.append(
        Line("lxml", "LXML_OK", f"lxml {lxml}")
        if lxml
        else Line("lxml", "NO_LXML", "lxml is missing", "pip install lxml")
    )
    pillow = _module("PIL")
    lines.append(
        Line("pillow", "PILLOW_OK", f"Pillow {pillow}")
        if pillow
        else Line("pillow", "NO_PILLOW", "Pillow is missing", "pip install Pillow")
    )
    pptx = _module("pptx")
    lines.append(
        Line("python-pptx", "PPTX_OK", f"python-pptx {pptx}")
        if pptx
        else Line(
            "python-pptx",
            "NO_PPTX",
            "python-pptx is missing: the pen cannot build decks",
            'pip install "keyline[pen]" (or pip install python-pptx)',
        )
    )
    return lines


def _render() -> list[Line]:
    from keyline.render import INSTALL, LO_INSTALL, find_rasterizer, find_soffice

    soffice, raster = find_soffice(), find_rasterizer()
    officecli = shutil.which("officecli")
    if soffice and raster:
        engine = Line("render", "RENDER_LIBREOFFICE", f"LibreOffice at {soffice}")
    elif officecli:
        engine = Line("render", "RENDER_OFFICECLI", f"OfficeCLI at {officecli}")
    else:
        engine = Line("render", "NO_RENDERER", "no render engine", f"{LO_INSTALL}; or {INSTALL}")
    if raster == "pypdfium2":
        rline = Line("rasterizer", "RASTER_PDFIUM", "pypdfium2")
    elif raster == "pdftoppm":
        rline = Line("rasterizer", "RASTER_PDFTOPPM", f"pdftoppm at {shutil.which('pdftoppm')}")
    else:
        rline = Line(
            "rasterizer", "NO_RASTER", "no rasterizer for LibreOffice", "pip install pypdfium2"
        )
    validator = (
        Line("validator", "VALIDATE_OFFICECLI", f"officecli validate at {officecli}")
        if officecli
        else Line("validator", "NO_VALIDATOR", "check will skip validation", INSTALL)
    )
    return [engine, rline, validator]


def _fc_match(family: str) -> str | None:
    fc = shutil.which("fc-match")
    if fc is None:
        return None
    try:
        out = subprocess.run(
            [fc, "-f", "%{family}", family], capture_output=True, text=True, timeout=30
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return out.split(",")[0].strip()


def _by_file(name: str) -> bool:
    wanted = set(FONT_FILES.get(name, ()))
    for folder in font_dirs():
        if not folder.is_dir():
            continue
        for path in folder.rglob("*"):
            if path.name.casefold() in wanted:
                return True
    return False


def fonts() -> list[dict]:
    """One entry per portable_fonts family (B-8.12)."""
    from keyline.config import load

    out = []
    for family, twin in load().portable_fonts:
        match = _fc_match(family)
        if match is not None:
            ok = match.casefold() in (family.casefold(), twin.casefold())
            detail = f"{family}: fc-match gives {match or 'nothing'}"
        else:  # plan Q-40: no fc-match, so look for the files by name
            ok = _by_file(family) or _by_file(twin)
            found = "found" if ok else "not found"
            detail = f"{family}: {family} or {twin} {found} by file name (no fc-match)"
        hint = "" if ok else f"{twin} (metric-compatible with {family}): {TWIN_HINTS[twin]}"
        token = "FONT_OK" if ok else "FONT_SUBSTITUTED"
        out.append(
            {"family": family, "metric_twin": twin, "token": token, "detail": detail, "hint": hint}
        )
    return out


def _packs() -> list[str]:
    from keyline.packs import bundled

    return bundled()


def report() -> dict:
    lines = _core()
    lint_ok = all(x.token in ("PYTHON_OK", "LXML_OK", "PILLOW_OK") for x in lines[:3])
    return {
        "checks": [asdict(x) for x in [*lines, *_render()]],
        "fonts": fonts(),
        "packs": _packs(),
        "lint_can_run": lint_ok,
    }


def human(data: dict) -> str:
    rows = [(c["token"], c["detail"], c["hint"]) for c in data["checks"]]
    rows += [(f["token"], f["detail"], f["hint"]) for f in data["fonts"]]
    width = max(len(t) for t, _, _ in rows)
    out = [
        f"{t:<{width}}  {d}" + (f"\n{'':<{width}}  install: {h}" if h else "") for t, d, h in rows
    ]
    out.append(f"PACKS: {', '.join(data['packs']) or 'none'}")
    return "\n".join(out) + "\n"
