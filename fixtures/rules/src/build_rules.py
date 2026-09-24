"""Build every rule fixture deck: python fixtures/rules/src/build_rules.py [OUT_DIR]

Each builder makes one deck. Expectations for each deck live in fixtures/rules/expect.toml.
Dev dependency: python-pptx (pyproject extra `dev`).
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _deck as d

DECKS: dict[str, Callable[[], object]] = {}


def deck(name: str):
    def wrap(fn):
        DECKS[name] = fn
        return fn

    return wrap


def _chart(s, x, y, w, h, name):
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE
    from pptx.util import Cm

    data = CategoryChartData()
    data.categories = ["a", "b"]
    data.add_series("s", (1, 2))
    gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Cm(x), Cm(y), Cm(w), Cm(h), data)
    gf.name = name
    return gf


# ---------- off-slide ----------
@deck("off-slide--pos")
def off_slide_pos():
    prs = d.new_deck()
    s = d.slide(prs, bg="FFFFFF")
    d.text(s, 25, 8, 10, 2, "This line runs past the right edge", name="over-right")
    # unrotated bottom is 18.5 cm (inside); rotated 30° its bounding box reaches 20.87 cm
    d.text(s, 10, 16.5, 10, 2, "Rotated caption crossing the bottom", name="rotated", rot=30)
    d.rect(s, -2, 3, 6, 4, "CADCFC", name="bleed")
    return prs


@deck("off-slide--neg")
def off_slide_neg():
    prs = d.new_deck()
    s = d.slide(prs, bg="FFFFFF")
    # right edge at 33.907 cm: 0.04 cm past the 33.867 cm slide, within the 0.05 tolerance
    d.text(s, 23.907, 8, 10, 2, "Ends just past the edge", name="within-tolerance")
    d.text(s, 2, 2, 10, 2, "Comfortably inside", name="inside")
    d.rect(s, -2, 12, 6, 4, "CADCFC", name="bleed")
    return prs


# ---------- edge-margin ----------
@deck("edge-margin--pos")
def edge_margin_pos():
    prs = d.new_deck()
    s = d.slide(prs, bg="FFFFFF")
    d.text(s, 1.0, 5, 10, 2, "One centimetre from the left", name="near-left")
    d.rect(s, 12, 17.55, 8, 1, "1E2761", name="near-bottom")  # bottom margin 0.50 cm
    d.picture_placeholder(s, 22, 0.8, 5, 3, name="pic-top")
    _chart(s, 20, 5, 13.367, 8, name="chart-right")  # right margin 0.50 cm (A-3)
    return prs


@deck("edge-margin--neg")
def edge_margin_neg():
    prs = d.new_deck()
    s = d.slide(prs, bg="FFFFFF")
    d.rect(s, 0, 0, 33.867, 19.05, "F2F2F0", name="full-background")
    d.text(s, 1.25, 5, 10, 2, "At the tolerance", name="at-tolerance")
    a = d.rect(s, 3, 9, 4, 2, "1E2761", name="box-a")
    b = d.rect(s, 26, 9, 4, 2, "1E2761", name="box-b")
    c = d.connector(s, a, b)
    c.name = "link"
    line = d.connector(s, a, b)
    line.begin_x, line.begin_y, line.end_x, line.end_y = 72000, 72000, 72000, 3600000
    line.name = "edge-connector"  # 0.2 cm from the left edge
    d.text(s, 0.3, 14, 5, 2, "", name="empty-box")  # no text, no fill
    return prs


def build(out_dir: Path, names: list[str] | None = None) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name in names or sorted(DECKS):
        path = out_dir / f"{name}.pptx"
        DECKS[name]().save(path)
        written.append(path)
    return written


def main(argv: list[str]) -> int:
    out = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parents[1]
    for p in build(out):
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
