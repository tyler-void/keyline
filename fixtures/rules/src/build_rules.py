"""Build rule fixture decks: python fixtures/rules/src/build_rules.py [OUT_DIR] [--only NAME ...]

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


# ---------- font-count ----------
@deck("font-count--pos")
def font_count_pos():
    prs = d.new_deck()
    s = d.slide(prs, bg="FFFFFF")
    d.text(s, 2, 2, 20, 2.5, "Georgia title", size=40, font="Georgia")
    d.text(s, 2, 6, 20, 2, "Calibri body", size=20, font="Calibri")
    d.text(s, 2, 9, 20, 2, "Arial caption", size=20, font="Arial")
    return prs


@deck("font-count--neg")
def font_count_neg():
    prs = d.new_deck()
    s = d.slide(prs, bg="FFFFFF")
    d.text(s, 2, 2, 20, 2.5, "Georgia title", size=40, font="Georgia")
    d.text(s, 2, 6, 20, 2, "Calibri body", size=20, font="Calibri")
    d.text(s, 2, 8.5, 20, 2, "Calibri Light is the same family", size=20, font="Calibri Light")
    d.text(s, 2, 11, 20, 2, "Theme minor font", size=20, font="+mn-lt")  # -> Calibri
    chart = _chart(s, 22, 6, 10, 8, name="chart")
    chart.chart.font.name = "Arial"  # chart text is not counted
    return prs


# ---------- title-underline ----------
def _titled(prs):
    s = d.slide(prs, bg="FFFFFF", notes="n")
    d.text(s, 2, 2, 20, 2.5, "A title with an accent", size=40, name="title")
    d.text(s, 2, 8, 29.867, 3, "Body text that is long enough to be body", size=20)
    return s


@deck("title-underline--pos")
def title_underline_pos():
    prs = d.new_deck()
    s = _titled(prs)
    d.rect(s, 2, 4.9, 3, 0.15, "E8422E", name="underline")  # 0.40 cm below the title
    return prs


@deck("title-underline--neg")
def title_underline_neg():
    prs = d.new_deck()
    d.rect(_titled(prs), 2, 4.9, 29.867, 0.03, "C9C9C2", name="hairline")  # full width
    d.rect(_titled(prs), 2, 1.5, 3, 0.15, "E8422E", name="above")
    d.rect(_titled(prs), 2, 6.0, 3, 0.15, "E8422E", name="far-below")  # 1.5 cm below
    d.rect(_titled(prs), 4, 4.9, 3, 0.15, "E8422E", name="offset")  # 2 cm right
    return prs


# ---------- equal-card-row ----------
def _cards(s, widths=(9, 9, 9), gaps=(1, 1), own_text=True, prefix="card"):
    x, shapes = 2.0, []
    for i, w in enumerate(widths):
        name = f"{prefix}-{'abcd'[i]}"
        if own_text:
            shapes.append(d.rect(s, x, 6, w, 6, "1E2761", name=name, body=f"Point {i + 1}"))
        else:
            shapes.append(d.rect(s, x, 6, w, 6, "1E2761", name=name))
            d.text(s, x, 7, w, 2, str(i + 1), size=60, color="FFFFFF", align="ctr")
            d.text(s, x, 9.5, w, 1, "label", size=14, color="CADCFC", align="ctr")
        if i < len(gaps):
            x += w + gaps[i]
    return shapes


@deck("equal-card-row--pos")
def equal_card_row_pos():
    prs = d.new_deck()
    _cards(d.slide(prs, bg="FFFFFF"))
    _cards(d.slide(prs, bg="FFFFFF", notes="n"), own_text=False, prefix="kpi")
    return prs


@deck("equal-card-row--neg")
def equal_card_row_neg():
    prs = d.new_deck()
    s = d.slide(prs, bg="FFFFFF")
    a, b, c = _cards(s)
    d.connector(s, a, b)
    d.connector(s, b, c)
    _cards(d.slide(prs, bg="FFFFFF", notes="n"), widths=(9, 9.9, 9))
    _cards(d.slide(prs, bg="FFFFFF", notes="n"), widths=(9, 9, 9), gaps=(0.5, 1.5))
    _cards(d.slide(prs, bg="FFFFFF", notes="n"), widths=(9, 9), gaps=(1,))
    return prs


# ---------- spec 002 AC-5: roles ----------
def _headline_and_numeral(s):
    """The same two shapes on every slide: content ends at 8.0 cm, so the band from 8.0 to
    19.05 cm (58 % of the height) is empty."""
    d.text(
        s,
        2,
        1.5,
        29.867,
        2.5,
        "Roles decide where composition rules apply",
        size=40,
        name="headline",
    )
    d.text(s, 2, 4.5, 12, 3.5, "61", size=96, bold=True, name="numeral")


@deck("roles--ac5")
def roles_ac5():
    prs = d.new_deck()
    # slide order statement, untagged, evidence puts the untagged slide at index 2 (Q-9)
    _headline_and_numeral(d.role_slide(prs, 0, "keyline:statement", bg="FFFFFF", notes="n"))
    _headline_and_numeral(d.slide(prs, bg="FFFFFF", notes="n"))
    _headline_and_numeral(d.role_slide(prs, 1, "keyline:evidence", bg="FFFFFF", notes="n"))
    s = d.role_slide(prs, 2, "keyline:section", bg="FFFFFF")  # no notes on purpose
    d.text(s, 2, 1.5, 29.867, 2.5, "Part two", size=40, name="headline")
    return prs


# ---------- spec 002 AC-6: source and note lines (presented mode) ----------
SOURCE_LINE = "Source: BonsaiHub waitlist, September 2026 (fictional)"
NOTE_LINE = "Note: BonsaiHub is a parody. Its trees and every number in this deck are fictional."


@deck("source-lines--ac6")
def source_lines_ac6():
    prs = d.new_deck()
    lines = [
        (SOURCE_LINE, 12, "source-12pt"),  # a source line at the floor: fine
        (SOURCE_LINE, 10, "source-10pt"),  # below source_min_pt: "source line"
        ("Source code in this repository is checked by two linters", 12, "source-code"),
        (NOTE_LINE, 12, "note-12pt"),  # a note line at the floor: fine
    ]
    for body, size, name in lines:
        s = d.slide(prs, bg="FFFFFF", notes="n")
        d.text(s, 2, 1.5, 29.867, 2.5, "Where the numbers come from", size=40, name="title")
        d.text(s, 2, 15.5, 29.867, 1.5, body, size=size, name=name)
    # B-2: a source line is not body for title-not-dominant either (20 < 2.0 x 12 if it were)
    s = d.slide(prs, bg="FFFFFF", notes="n")
    d.text(s, 2, 1.5, 29.867, 2.5, "A modest title", size=20, name="title")
    d.text(s, 2, 15.5, 29.867, 1.5, SOURCE_LINE, size=12, name="source-under-small-title")
    return prs


# ---------- spec 002 §3.4: claude-look-palette (the four AC-4 anchor decks) ----------
def _look(bg, accent):
    prs = d.new_deck()
    for _ in range(2):
        s = d.slide(prs, bg=bg, notes="n")
        d.text(
            s,
            2,
            1.5,
            29.867,
            2.5,
            "A calm deck about bonsai keepers",
            size=40,
            color="111111",
            name="title",
        )
        d.text(
            s,
            2,
            5,
            29.867,
            3,
            "Keepers visit a tree for a whole season before a match",
            size=24,
            color="111111",
            name="body",
        )
        if accent:
            d.text(s, 2, 9, 12, 2, "Seasonal Boost", size=24, color=accent, name="accent")
    return prs


@deck("claude-look-palette--pos")
def claude_look_pos():
    return _look("F4F3EE", "C96442")  # cream paper + terracotta text: warning


@deck("claude-look-palette--neg")
def claude_look_neg():
    return _look("F2F2F0", "CC3322")  # neutral paper + signal red: nothing


@deck("claude-look-palette--cream-only")
def claude_look_cream_only():
    return _look("FAF9F5", None)  # cream paper, no accent: advisory only


@deck("claude-look-palette--cool")
def claude_look_cool():
    return _look("EFF1F5", "D20F39")  # cool paper + crimson: nothing


# ---------- spec 002 §3.4: title-too-long ----------
ELEVEN = "Eleven words in this title are one more than presented allows"


@deck("title-too-long--pos")
def title_too_long_pos():
    prs = d.new_deck()
    s = d.slide(prs, bg="FFFFFF", notes="n")
    d.text(s, 2, 1.5, 29.867, 4, ELEVEN, size=40, name="long-title")
    return prs


@deck("title-too-long--neg")
def title_too_long_neg():
    prs = d.new_deck()
    s = d.slide(prs, bg="FFFFFF", notes="n")
    d.text(
        s,
        2,
        1.5,
        29.867,
        4,
        "Ten words in this title are what presented mode allows",
        size=40,
        name="ten-word-title",
    )
    # a quote slide's title is the quote itself, so it is exempt
    s = d.role_slide(prs, 3, "keyline:quote", bg="FFFFFF", notes="n")
    d.text(
        s,
        2,
        1.5,
        29.867,
        8,
        "A tree is patient with us; we can learn to be patient with the tree, one season at a time",
        size=40,
        name="quote",
    )
    return prs


# ---------- spec 002 §3.4: closing-cliche ----------
@deck("closing-cliche--pos")
def closing_cliche_pos():
    prs = d.new_deck()
    s = d.slide(prs, bg="FFFFFF", notes="n")
    d.text(s, 2, 1.5, 29.867, 2.5, "Plant the first tree this season", size=40, name="title")
    s = d.slide(prs, bg="FFFFFF", notes="n")
    d.text(s, 2, 1.5, 29.867, 2.5, "  Thank you! ", size=40, name="closing-title")
    return prs


@deck("closing-cliche--neg")
def closing_cliche_neg():
    prs = d.new_deck()
    s = d.slide(prs, bg="FFFFFF", notes="n")
    d.text(s, 2, 1.5, 29.867, 2.5, "Questions?", size=40, name="not-last")  # not the last slide
    s = d.slide(prs, bg="FFFFFF", notes="n")
    d.text(
        s, 2, 1.5, 29.867, 2.5, "Thank you, trees, for your patience", size=40, name="closing-title"
    )
    return prs


# ---------- spec 002 §3.4: the pack rules, on decks from the Swiss templates ----------
HEADLINE = "Keepers wait a season before a match"
SOURCE = "Source: BonsaiHub waitlist, September 2026 (fictional)"


def _swiss_story(voice):
    """Four slides that use only the voice's tokens: cover, section, evidence (with the
    keyline, a hairline and one accent numeral) and close."""
    from keyline.packs import resolve

    v = resolve("swiss").voice(voice)
    ink, muted, hairline, accent = (v.hex(r) for r in ("ink", "muted", "hairline", "accent"))
    font = v.text
    prs = d.swiss_deck(voice)
    d.swiss_slide(prs, "keyline:cover", title="BonsaiHub", main="Trees meet keepers", footer=SOURCE)
    d.swiss_slide(prs, "keyline:section", title="The waitlist", main="Part one")
    s = d.swiss_slide(prs, "keyline:evidence:figure", title=HEADLINE, side="Most keepers visit")
    d.keyline_rule(s, ink)
    d.rect(s, 1.5, 17.2, 30.867, 0.05, hairline, name="hairline")
    d.text(s, 1.5, 6, 20, 5, "212 years", 120, bold=True, color=accent, font=font, name="numeral")
    d.text(s, 1.5, 12, 20, 1, "OLDEST TREE", 14, bold=True, color=muted, font=font, name="label")
    d.swiss_slide(prs, "keyline:close", title="Plant the first tree", main="This season")
    return prs


@deck("off-palette-color--pos")
def off_palette_color_pos():
    prs = d.swiss_deck()
    s = d.swiss_slide(prs, "keyline:evidence", title=HEADLINE, main="Most keepers visit twice")
    d.text(s, 1.5, 12, 20, 2, "A softer grey line", size=24, color="333333", name="off-ink")
    d.rect(s, 24, 12, 6, 3, "1E2761", name="off-fill")
    d.swiss_slide(prs, "keyline:statement", bg="FFFFFF", title="One tree, one keeper")
    return prs


@deck("off-palette-color--neg")
def off_palette_color_neg():
    return _swiss_story("neutral")


@deck("off-scale-size--pos")
def off_scale_size_pos():
    prs = d.swiss_deck()
    s = d.swiss_slide(prs, "keyline:evidence", title=HEADLINE)
    d.text(s, 1.5, 6, 20, 2, "Twenty points is between steps", size=20, name="twenty")
    # 24 pt on the scale, but autofit shrinks it to 21.6 pt (A-14)
    d.autofit(d.text(s, 1.5, 10, 20, 2, "Shrunk by autofit", size=24, name="shrunk"), 90000)
    return prs


@deck("off-scale-size--neg")
def off_scale_size_neg():
    prs = d.swiss_deck()
    s = d.swiss_slide(prs, "keyline:evidence", title=HEADLINE, main="Body at 24 pt", footer=SOURCE)
    d.text(s, 1.5, 12, 20, 4, "120", size=120, bold=True, name="numeral")
    # 32 pt is off the scale, but autofit makes it 24 pt, and the effective size counts
    d.autofit(d.text(s, 20, 12, 12, 2, "Effective 24 pt", size=32, name="fitted"), 75000)
    return prs


@deck("off-pack-font--pos")
def off_pack_font_pos():
    prs = d.swiss_deck()
    # B-11: exact names, so Arial Black and Arial Narrow are not Arial
    for n, font in enumerate(("Calibri", "Calibri", "Georgia", "Arial Black", "Arial Narrow")):
        s = d.swiss_slide(prs, "keyline:evidence", title=HEADLINE)
        d.text(s, 1.5, 6, 20, 2, f"Line {n + 1} in {font}", size=24, font=font, name="line")
    return prs


@deck("off-pack-font--neg")
def off_pack_font_neg():
    prs = d.swiss_deck()
    s = d.swiss_slide(prs, "keyline:evidence", title=HEADLINE, main="Theme fonts resolve")
    d.text(s, 1.5, 12, 20, 2, "Named Arial", size=24, font="Arial", name="arial")
    # B-11: case and whitespace do not matter; a style word does (see the --pos deck)
    d.text(s, 1.5, 15, 20, 2, "Spelled loosely", size=24, font="  ARIAL ", name="loose")
    return prs


@deck("accent-overuse--pos")
def accent_overuse_pos():
    prs = d.swiss_deck()
    s = d.swiss_slide(prs, "keyline:evidence", title=HEADLINE)
    d.keyline_rule(s, "111111")
    d.text(s, 1.5, 6, 14, 5, "212", size=120, bold=True, color="CC3322", name="numeral")
    d.rect(s, 20, 6, 6, 3, "CC3322", name="red-block")
    return prs


@deck("accent-overuse--neg")
def accent_overuse_neg():
    prs = d.swiss_deck()
    s = d.swiss_slide(prs, "keyline:evidence", title=HEADLINE)
    d.keyline_rule(s, "111111")  # ink: never an accent
    # two accent runs in one shape: one accent element, not two
    d.text(s, 1.5, 6, 14, 8, "212\nYEARS", 120, bold=True, color="CC3322", name="numeral")
    s = d.swiss_slide(prs, "keyline:statement", title="One tree, one keeper")
    d.rect(s, 1.5, 15, 8, 1.5, "CC3322", name="red-tag", body="NEW", size=14, color="F2F2F0")
    d.swiss_slide(prs, "keyline:section", title="The waitlist", main="Part one")  # label
    return prs


@deck("pack-voice-night")
def pack_voice_night():
    return _swiss_story("night")


@deck("pack-voice-field")
def pack_voice_field():
    return _swiss_story("field")


def build(out_dir: Path, names: list[str] | None = None) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name in names or sorted(DECKS):
        path = out_dir / f"{name}.pptx"
        DECKS[name]().save(path)
        written.append(path)
    return written


def main(argv: list[str]) -> int:
    """build_rules.py [OUT_DIR] [--only NAME ...]. Rebuilding a committed deck only
    changes its zip timestamps, so build just the decks you add or change."""
    args = argv[1:]
    only = []
    if "--only" in args:
        i = args.index("--only")
        only, args = args[i + 1 :], args[:i]
    out = Path(args[0]) if args else Path(__file__).resolve().parents[1]
    for p in build(out, only or None):
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
