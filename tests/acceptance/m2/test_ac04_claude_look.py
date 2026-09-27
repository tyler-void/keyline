"""Spec 002 AC-4: the four Claude-look anchor decks."""

import json

import pytest

from tests.acceptance._cli import keyline
from tests.conftest import RULES

ROWS = [
    ("claude-look-palette--pos", "F4F3EE", "warning"),  # f4f3ee + text in c96442
    ("claude-look-palette--neg", "F2F2F0", None),  # F2F2F0 + CC3322
    ("claude-look-palette--cream-only", "FAF9F5", "advisory"),  # FAF9F5, no accent
    ("claude-look-palette--cool", "EFF1F5", None),  # EFF1F5 + D20F39
]


@pytest.mark.parametrize(("deck", "paper", "expected"), ROWS, ids=[r[0] for r in ROWS])
def test_anchor(deck, paper, expected):
    from keyline.ooxml.adapter import load_deck

    model, _ = load_deck(RULES / f"{deck}.pptx")
    assert {s.background_rgb for s in model.slides} == {paper}
    found = [
        f
        for f in json.loads(keyline("lint", RULES / f"{deck}.pptx", "--json").stdout)
        if f["rule"] == "claude-look-palette"
    ]
    assert [f["severity"] for f in found] == ([expected] if expected else [])
