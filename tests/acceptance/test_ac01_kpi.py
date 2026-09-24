"""AC-1: kpi-recipe.pptx in presented mode."""

import pytest

from tests.acceptance._golden import FAILING, has, run


@pytest.fixture(scope="module")
def result():
    return run("kpi-recipe.pptx", "presented")


def test_exits_2(result):
    assert result[0] == 2


@pytest.mark.parametrize("slide", [2, 4])
def test_dead_band_bottom(result, slide):
    bands = has(result[1], "dead-band", slide=slide, severity="warning")
    assert [f for f in bands if "bottom band" in f["message"]]


@pytest.mark.parametrize(("slide", "title"), [(2, "T2"), (3, "T3"), (4, "T4")])
def test_edge_margin_on_titles(result, slide, title):
    (f,) = has(result[1], "edge-margin", slide=slide, shape=title, severity="warning")
    assert f["measured"] == 1.2 and "top edge" in f["message"]


def test_equal_card_row_on_slide_2(result):
    assert has(result[1], "equal-card-row", slide=2, severity="warning")


def test_no_overlap_on_slide_3(result):
    assert not [f for f in result[1] if f["slide"] == 3 and "overlap" in f["rule"]]


def test_no_equal_card_row_on_slide_4(result):
    assert not has(result[1], "equal-card-row", slide=4)


def test_no_dead_band_on_slide_1(result):
    assert not has(result[1], "dead-band", slide=1)


def test_no_title_not_dominant_on_slide_2(result):
    assert not has(result[1], "title-not-dominant", slide=2)


def test_failing_findings_are_exactly_the_reviewed_ones(result):
    got = sorted(
        (f["slide"], f["rule"], f["shape_name"]) for f in result[1] if f["severity"] in FAILING
    )
    assert got == [
        (2, "dead-band", None),
        (2, "edge-margin", "T2"),
        (2, "equal-card-row", "TextBox 2"),
        (3, "edge-margin", "T3"),
        (4, "dead-band", None),
        (4, "dead-band", None),
        (4, "edge-margin", "T4"),
    ]
