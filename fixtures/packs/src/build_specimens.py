"""Build the Swiss pack specimens (spec 002 §11.13, B-8.13, Q-42; task T-28):

    python fixtures/packs/src/build_specimens.py [OUT_DIR]

Each specimen is built with the pen from its committed brief (`Deck.from_brief`): one
slide per role, every verb at least once, and real sentences about the pack. The grid
picture on the image slide is drawn here, from the pack's grid, in the deck's voice.
The same inputs give the same bytes (§6.5, AC-11).
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from keyline.brief import load
from keyline.pen import Deck

HERE = Path(__file__).resolve().parents[1]
STEMS = (
    "swiss-specimen-presented-neutral",
    "swiss-specimen-presented-night",
    "swiss-specimen-read-field",
)
TABLE = [
    ["Style", "Used for"],
    ["Headline", "Evidence and section titles"],
    ["Lede", "The line that follows a title"],
    ["Body", "Paragraphs and bullets"],
    ["Label", "Figure labels and table headers"],
    ["Source", "Source and note lines"],
]


def grid_picture(brief, path: Path) -> Path:
    """The grid's content area (twelve columns, every fourth row, the keyline rule) in
    the voice's colours, one pixel per 9525 EMU. The margins are left out, so the
    picture's edge is the grid's edge."""
    from PIL import Image, ImageDraw

    pack, voice = brief.pack, brief.voice
    g, rule = pack.grid, pack.keyline_rule
    px = 9525  # EMU per pixel: 1280 px across the slide
    w = (12192000 - 2 * g.margin_x_emu) // px
    h = (6858000 - 2 * g.margin_y_emu) // px
    img = Image.new("RGB", (w, h), "#" + voice.hex("paper"))
    draw = ImageDraw.Draw(img)
    for i in range(g.columns):
        x = i * (g.column_emu + g.gutter_emu) // px
        draw.rectangle([x, 0, x + g.column_emu // px, h], fill="#" + voice.hex("hairline"))
    for r in range(0, g.rows + 1, 4):
        y = r * g.row_emu // px
        draw.line([0, y, w, y], fill="#" + voice.hex("muted"))
    y = rule["row"] * g.row_emu // px
    draw.rectangle(
        [0, y, w, y + max(1, rule["thickness_emu"] // px)], fill="#" + voice.hex(rule["color"])
    )
    img.save(path, format="PNG")
    return path


def build(stem: str, out_dir: Path) -> Path:
    brief_path = HERE / f"{stem}.brief.toml"
    brief = load(brief_path)
    sizes = "type_sizes" if brief.mode == "presented" else "type_sizes_read"
    with tempfile.TemporaryDirectory(prefix="keyline-specimen-") as tmp:
        picture = grid_picture(brief, Path(tmp) / "grid.png")
        deck = Deck.from_brief(str(brief_path))
        deck.next().text(
            "A grid, one family per voice, one signal colour, and a single recurring rule.",
            style="lede",
        )
        deck.next().text(
            "The pen takes names, never sizes or colours, so a slide cannot drift off the system.",
            style="lede",
        )
        deck.next().text("Part one", style="label")
        deck.next(variant="figure").figure("grid_columns").text(
            "Every region spans whole columns, so text and figures line up from slide to slide.",
            region="side",
        ).source()
        deck.next().chart_bar(sizes, highlight="headline").source()
        deck.next().table(TABLE).source("pack.toml, [styles]")
        deck.next(variant="figure").image(
            str(picture), alt="The Swiss grid: twelve columns inside fixed margins"
        ).bullets(
            ["Margins keep a clear edge", "Gutters part the columns", "Rows set the rhythm"],
            region="side",
        )
        deck.next().attribution("The Swiss pack README")
        deck.next().text(
            "Start from a brief, pick a voice, and let the pen set the rest.", style="lede"
        ).note("This specimen shows the pack itself, not a product.")
        out = out_dir / f"{stem}.pptx"
        deck.save(str(out), author="Tyler")
    return out


if __name__ == "__main__":
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
    out_dir.mkdir(parents=True, exist_ok=True)
    for stem in STEMS:
        print(build(stem, out_dir))
