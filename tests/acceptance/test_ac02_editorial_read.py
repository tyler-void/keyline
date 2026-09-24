"""AC-2: editorial.pptx in read mode."""

import pytest

from tests.acceptance._golden import FAILING, has, run


@pytest.fixture(scope="module")
def result():
    return run("editorial.pptx", "read")


def test_exits_2(result):
    assert result[0] == 2


@pytest.mark.parametrize(("shape", "cm"), [("verdict", 0.88), ("verdicttx", 0.54)])
def test_edge_margin_bottom(result, shape, cm):
    (f,) = has(result[1], "edge-margin", shape=shape, severity="warning")
    assert f["measured"] == cm and "bottom edge" in f["message"]


def test_text_contrast_on_l3(result):
    (f,) = has(result[1], "text-contrast", shape="l3", severity="warning")
    assert (f["measured"], f["threshold"]) == (3.57, 4.5)
    assert "E8422E on F2F2F0" in f["message"] and "9.5 pt" in f["message"]


def test_no_edge_margin_on_mark(result):
    assert not has(result[1], "edge-margin", shape="mark")


def test_no_body_too_small(result):
    assert not has(result[1], "body-too-small")


def test_no_text_contrast_on_n3(result):
    assert not has(result[1], "text-contrast", shape="n3")


def test_no_title_underline_on_rule2(result):
    assert not has(result[1], "title-underline", shape="rule2")


def test_no_overlap_at_warning_or_error(result):
    assert not [f for f in result[1] if "overlap" in f["rule"] and f["severity"] in FAILING]
