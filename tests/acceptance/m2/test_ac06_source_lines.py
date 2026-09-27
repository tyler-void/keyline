"""Spec 002 AC-6 (presented mode), and B-2 for title-not-dominant."""

import json

import pytest

from tests.acceptance._cli import keyline
from tests.acceptance._golden import has
from tests.conftest import RULES

DECK = RULES / "source-lines--ac6.pptx"


@pytest.fixture(scope="module")
def findings():
    return json.loads(keyline("lint", DECK, "--json").stdout)


def test_source_line_at_12pt_is_fine(findings):
    assert not has(findings, "body-too-small", slide=1)


def test_source_line_at_10pt_fires_as_source_line(findings):
    (f,) = has(findings, "body-too-small", slide=2)
    assert "source line" in f["message"] and (f["measured"], f["threshold"]) == (10.0, 12.0)


def test_source_code_paragraph_is_body(findings):
    (f,) = has(findings, "body-too-small", slide=3)
    assert "10-word paragraph" in f["message"] and f["threshold"] == 18.0


def test_note_line_at_12pt_is_fine(findings):
    assert not has(findings, "body-too-small", slide=4)


def test_source_line_is_not_body_for_title_not_dominant(findings):
    assert not has(findings, "title-not-dominant", slide=5)  # B-2


def test_read_mode_floor_is_9pt():
    found = json.loads(keyline("lint", DECK, "--mode", "read", "--json").stdout)
    assert not has(found, "body-too-small", slide=2)  # 10 pt >= 9 pt in read mode
