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


# ---------- dead-band ----------
def _top_heavy(s):
    d.text(s, 2, 1.5, 29.867, 2, "A title in the top band", size=36, name="title")
    d.rect(s, 2, 4, 29.867, 4.5, "CADCFC", name="block")


@deck("dead-band--pos")
def dead_band_pos():
    prs = d.new_deck()
    _top_heavy(d.slide(prs, bg="FFFFFF", notes="cover"))
    _top_heavy(d.slide(prs, bg="FFFFFF", notes="content"))  # bottom 10.55 cm empty (55%)
    return prs


@deck("dead-band--neg")
def dead_band_neg():
    prs = d.new_deck()
    _top_heavy(d.slide(prs, bg="FFFFFF", notes="cover"))  # slide 1 is the cover: exempt
    s = d.slide(prs, bg="FFFFFF", notes="content")
    d.rect(s, 0, 0, 33.867, 19.05, "F2F2F0", name="full-background")  # does not count
    d.text(s, 2, 1.5, 29.867, 2.5, "Spread evenly", size=36, name="title")
    d.rect(s, 2, 5, 29.867, 4, "CADCFC", name="band-1")
    d.rect(s, 2, 10, 29.867, 4, "CADCFC", name="band-2")
    d.text(s, 2, 15, 29.867, 2.5, "A closing line near the bottom", name="footer")
    return prs


# ---------- box-overlap ----------
@deck("box-overlap--pos")
def box_overlap_pos():
    prs = d.new_deck()
    s = d.slide(prs, bg="FFFFFF")
    d.text(s, 3, 3, 8, 3, "First text box", name="first")
    d.text(s, 10, 5, 8, 3, "Second text box overlapping", name="second")  # 1.0 x 1.0 cm
    return prs


@deck("box-overlap--neg")
def box_overlap_neg():
    prs = d.new_deck()
    s = d.slide(prs, bg="FFFFFF")
    d.text(s, 3, 3, 8, 3, "Left box", name="left")
    d.text(s, 10.95, 3, 8, 3, "Right box touching", name="right")  # 0.05 cm overlap on x
    d.rect(s, 3, 9, 10, 5, "1E2761", name="card")
    d.text(s, 3.5, 10, 9, 2, "Inside a card", color="FFFFFF", name="in-card")
    return prs


# ---------- body-too-small ----------
EIGHT = "Eight words of body text sit on this slide"


@deck("body-too-small--pos")
def body_too_small_pos():
    prs = d.new_deck()
    s = d.slide(prs, bg="FFFFFF")
    d.text(s, 2, 2, 29.867, 2.5, "A clear title", size=40, name="title")
    d.text(s, 2, 6, 29.867, 2, EIGHT, size=14, name="body")  # presented floor is 18 pt
    s = d.slide(prs, bg="FFFFFF", notes="n")
    d.text(s, 2, 2, 29.867, 2.5, "A clear title", size=40, name="title")
    d.text(s, 2, 6, 29.867, 2, EIGHT, size=12, name="read-body")  # read floor is 11 pt
    s = d.slide(prs, bg="FFFFFF", notes="n")
    d.text(s, 2, 2, 29.867, 2.5, "A clear title", size=40, name="title")
    d.text(s, 2, 6, 29.867, 2, EIGHT, size=10, name="tiny")  # below both floors
    return prs


@deck("body-too-small--neg")
def body_too_small_neg():
    prs = d.new_deck()
    s = d.slide(prs, bg="FFFFFF")
    d.text(s, 2, 2, 29.867, 2.5, "A clear title", size=40, name="title")
    d.text(s, 2, 6, 29.867, 2, "Only five words in caption", size=14, name="caption")
    d.text(s, 2, 9, 29.867, 2, "a · b | c — d · e", size=10, name="separators")
    return prs


# ---------- title-not-dominant ----------
TEN = "Ten words of body text that compete with the title"


@deck("title-not-dominant--pos")
def title_not_dominant_pos():
    prs = d.new_deck()
    s = d.slide(prs, bg="FFFFFF")
    d.text(s, 2, 2, 29.867, 2.5, "A timid title", size=24, name="title")
    d.text(s, 2, 6, 29.867, 3, TEN, size=18, name="body")  # 24 < 2.0 x 18
    return prs


@deck("title-not-dominant--neg")
def title_not_dominant_neg():
    prs = d.new_deck()
    s = d.slide(prs, bg="FFFFFF")
    d.text(s, 2, 2, 29.867, 2.5, "A dominant title", size=44, name="title")
    d.text(s, 2, 6, 29.867, 3, TEN, size=18, name="body")
    s = d.slide(prs, bg="FFFFFF", notes="n")
    d.text(s, 2, 2, 10, 4, "61", size=72, bold=True, name="kpi")  # a KPI is not the title
    d.text(s, 14, 2, 17.867, 2.5, "The real title", size=24, name="title")
    d.text(s, 2, 8, 29.867, 3, TEN, size=10, name="body")  # 24 >= 2.0 x 10
    s = d.slide(prs, bg="FFFFFF", notes="n")
    d.text(s, 2, 2, 29.867, 2.5, "Title", size=20, name="title")
    d.text(s, 2, 6, 29.867, 3, "Short label only", size=20, name="label")  # no body
    return prs


# ---------- text-contrast ----------
@deck("text-contrast--pos")
def text_contrast_pos():
    prs = d.new_deck()
    s = d.slide(prs, bg="F2F2F0")
    d.text(s, 2, 2, 10, 1, "THEN IT STOPS", size=9.5, color="E8422E", name="label")
    s = d.slide(prs, bg="1E2761", notes="n")
    d.rect(s, 3, 3, 12, 6, "FFFFFF", name="white-card")
    # CADCFC reads well on the dark slide but not on the white card beneath it
    d.text(s, 4, 4, 10, 2, "Pale text on a white card", size=14, color="CADCFC", name="on-card")
    return prs


@deck("text-contrast--neg")
def text_contrast_neg():
    prs = d.new_deck()
    s = d.slide(prs, bg="F2F2F0")
    d.text(s, 2, 2, 8, 4, "3", size=76, bold=True, color="E8422E", name="large")  # 3.57 >= 3.0
    d.rect(s, 12, 2, 10, 7, "1E2761", name="card")
    d.text(s, 12, 2, 10, 3, "White on navy", size=14, color="FFFFFF", name="card-text")
    s = d.slide(prs, notes="n")
    s.background.fill.gradient()
    d.text(s, 2, 2, 20, 2, "Text on a gradient", size=14, color="777777", name="on-gradient")
    return prs


# ---------- notes-missing ----------
@deck("notes-missing--pos")
def notes_missing_pos():
    prs = d.new_deck()
    d.text(d.slide(prs, bg="FFFFFF"), 2, 2, 20, 3, "Cover", size=40)
    d.text(d.slide(prs, bg="FFFFFF"), 2, 2, 20, 3, "No notes", size=40)
    d.text(d.slide(prs, bg="FFFFFF", notes="   "), 2, 2, 20, 3, "Blank notes", size=40)
    return prs


@deck("notes-missing--neg")
def notes_missing_neg():
    prs = d.new_deck()
    d.text(d.slide(prs, bg="FFFFFF"), 2, 2, 20, 3, "Cover without notes", size=40)
    d.text(d.slide(prs, bg="FFFFFF", notes="Say this."), 2, 2, 20, 3, "With notes", size=40)
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
