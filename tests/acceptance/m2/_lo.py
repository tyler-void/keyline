"""LibreOffice helpers for the A2 fix tests (audit 05): convert a pen-built deck to PDF
with the render engine's own soffice command, and read each page's character boxes.

A test that uses them skips unless LibreOffice and pypdfium2 are installed and every font
it names resolves to its metric twin through fontconfig (otherwise LibreOffice would set
the text in another font, and the measurement would not be the estimator's)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from keyline import render as render_mod
from keyline.fit import load_table

EMU_PER_PT = 12700


def unready(families=("Arial",)) -> str | None:
    """Why LibreOffice cannot measure these families here, or None."""
    if render_mod.find_soffice() is None:
        return "LibreOffice is not installed"
    try:
        import pypdfium2  # noqa: F401
    except ImportError:
        return "pypdfium2 is not installed"
    if shutil.which("fc-match") is None:
        return "fc-match is not installed"
    for family in families:
        twin = load_table(family, "regular").twin
        out = subprocess.run(
            ["fc-match", "-f", "%{family}", family], capture_output=True, text=True
        )
        got = out.stdout.split(",")[0].strip()
        if got.casefold() != twin.casefold():
            return f"{family} resolves to {got or 'nothing'}, not its twin {twin}"
    return None


def needs_lo(*families):
    reason = unready(families or ("Arial",))
    return pytest.mark.skipif(reason is not None, reason=f"LibreOffice measurement: {reason}")


def chars(pptx: Path, work: Path) -> list[list[tuple[str, float, float, float, float]]]:
    """Per page, every visible character as (char, left, top, right, bottom) in pt from
    the page's top left."""
    import pypdfium2 as pdfium

    work.mkdir(parents=True, exist_ok=True)
    pdf = render_mod.convert_to_pdf(Path(pptx), render_mod.find_soffice(), work)
    doc = pdfium.PdfDocument(str(pdf))
    pages = []
    try:
        for page in doc:
            height = page.get_height()
            tp = page.get_textpage()
            found = []
            for i in range(tp.count_chars()):
                ch = tp.get_text_range(i, 1)
                if not ch.strip():
                    continue
                left, bottom, right, top = tp.get_charbox(i)
                found.append((ch, left, height - top, right, height - bottom))
            tp.close()
            pages.append(found)
    finally:
        doc.close()
    return pages


def region_pt(pack, layout: str, region: str) -> tuple[float, float, float, float]:
    b = pack.region_box(layout, region)
    return (b.x / EMU_PER_PT, b.y / EMU_PER_PT, (b.x + b.w) / EMU_PER_PT, (b.y + b.h) / EMU_PER_PT)


def voice_file(directory: Path, family: str) -> str:
    """A test-only voice: Swiss neutral's palette with `family` as its display and text
    font (inline voices may use any portable family, audit 05)."""
    from keyline.packs import resolve

    neutral = resolve("swiss").directory / "voices" / "neutral.toml"
    name = family.lower().replace(" ", "-")
    text = neutral.read_text(encoding="utf-8").replace('name = "neutral"', f'name = "{name}"')
    path = Path(directory) / f"{name}.toml"
    path.write_text(text.replace('"Arial"', f'"{family}"'), encoding="utf-8")
    return str(path)
