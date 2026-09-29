"""Spec 002 §6.1, AC-10 and Q-43 as ruled by audit 03 (task T-25): figure() writes the
numeral and its label as two shapes with their own boxes inside the figure region."""

import pytest

pytest.importorskip("pptx")

from keyline.config import load as load_config
from keyline.context import LintContext
from keyline.lint import lint_path
from keyline.ooxml.adapter import load_deck
from keyline.packs import resolve
from keyline.pen import Deck, DoesNotFit, EvidenceError, PenError
from tests.conftest import FIXTURES

EVIDENCE = [str(FIXTURES / "briefs/evidence.toml"), str(FIXTURES / "briefs/extra-evidence.toml")]
PACK = resolve("swiss")


def deck(mode="presented"):
    return Deck(pack="swiss", mode=mode, voice="neutral", evidence=EVIDENCE)


def figure_slide(d):
    return d.add("evidence", "Most returned tools need a repair first", notes="n", variant="figure")


def test_two_boxes_that_touch_inside_the_region(tmp_path):
    d = deck()
    figure_slide(d).figure("returns_repaired").text("Before the next loan", region="side").source()
    out = tmp_path / "fig.pptx"
    d.save(str(out))
    model, diags = load_deck(out)
    assert diags == []
    shapes = {s.name: s for s in model.slides[0].shapes}
    numeral, label = shapes["main-numeral"], shapes["main-label"]
    region = PACK.region_box("keyline:evidence:figure", "main")
    assert (numeral.x, numeral.w, label.x, label.w) == (region.x, region.w, region.x, region.w)
    assert numeral.y == region.y and label.y == numeral.y + numeral.h  # they touch
    assert label.y + label.h == region.y + region.h
    assert numeral.h % PACK.grid.row_emu == 0  # whole grid rows
    assert numeral.text == "62%" and label.text == "returns needing a repair"
    ctx = LintContext(PACK, PACK.voice("neutral"))
    rules = {f.rule for f in lint_path(out, "presented", ctx).findings}
    assert "box-overlap" not in rules and "title-not-dominant" not in rules and rules == set()
    footer = shapes["footer"]
    assert footer.text == "Source: Toolshed Commons return log, 2026 (fictional)"


def test_accent_sets_the_surface_accent_and_spends_the_budget(tmp_path):
    d = deck()
    s = figure_slide(d).figure("returns_repaired", accent=True)
    d.save(str(tmp_path / "a.pptx"))
    model, _ = load_deck(tmp_path / "a.pptx")
    (numeral,) = [x for x in model.slides[0].shapes if x.name == "main-numeral"]
    assert numeral.runs[0].color == "CC3322"
    assert s._accents == 1


@pytest.mark.parametrize(
    ("call", "error", "message"),
    [
        (lambda s: s.figure("members_by_quarter"), PenError, "is a series; use chart_bar"),
        (lambda s: s.figure("returns_fixed"), EvidenceError, "unknown evidence id 'returns_fixed'"),
        (
            lambda s: s.figure("returns_repaired", label="returns that needed a small repair"),
            PenError,
            "label has 6 words; at most 5",
        ),
        (
            lambda s: s.figure("returns_repaired").figure("bench_hours", region="side"),
            PenError,
            "figure 2; at most 1 per slide",
        ),
    ],
)
def test_figure_errors(call, error, message):
    with pytest.raises(error, match=message):
        call(figure_slide(deck()))


def test_a_second_accent_over_the_budget():
    d = Deck(pack="swiss", mode="read", voice="neutral", evidence=EVIDENCE)
    s = figure_slide(d).figure("returns_repaired", accent=True)
    with pytest.raises(PenError, match="would be accent 2; the budget is 1"):
        s.figure("bench_hours", region="side", accent=True)


def test_a_region_too_short_names_both_parts():
    """Presented statement and close regions are 23 rows; a 120 pt numeral takes 21."""
    s = deck().add("statement", "Repairs bring members back", notes="n")
    with pytest.raises(DoesNotFit, match=r"needs 21 rows for the numeral and one label line"):
        s.figure("returns_repaired")
    assert load_config("presented").as_int("numerals_max") == 1


def test_read_mode_statement_holds_a_figure(tmp_path):
    d = deck("read")
    d.add("statement", "Repairs bring members back", notes="n").figure("returns_repaired")
    d.save(str(tmp_path / "r.pptx"))
    model, _ = load_deck(tmp_path / "r.pptx")
    assert {s.name for s in model.slides[0].shapes} == {"title", "main-numeral", "main-label"}
