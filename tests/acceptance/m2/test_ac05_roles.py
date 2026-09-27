"""Spec 002 AC-5: one slide built three times with the same shapes, varying only the
layout name (fixture script, not the pen), plus a section slide without notes."""

import json

import pytest

from tests.acceptance._cli import keyline
from tests.acceptance._golden import has
from tests.conftest import RULES

DECK = RULES / "roles--ac5.pptx"


@pytest.fixture(scope="module")
def findings():
    proc = keyline("lint", DECK, "--json")
    return json.loads(proc.stdout)


def test_statement_role_has_no_dead_band(findings):
    assert not has(findings, "dead-band", slide=1)


def test_untagged_slide_2_keeps_the_m1_dead_band(findings):
    (f,) = has(findings, "dead-band", slide=2)
    assert "from 8.00 to 19.05 cm" in f["message"]


def test_evidence_role_has_dead_band(findings):
    assert has(findings, "dead-band", slide=3)


def test_section_without_notes_has_no_notes_missing(findings):
    assert not has(findings, "notes-missing")


def test_roles_come_from_layout_names():
    from keyline.ooxml.adapter import load_deck

    deck, _ = load_deck(DECK)
    assert [(s.role, s.variant) for s in deck.slides] == [
        ("statement", None),
        (None, None),
        ("evidence", None),
        ("section", None),
    ]
