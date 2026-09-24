"""AC-6: each child's absolute geometry equals the hand-derived values within 1 EMU.
The derivation is in fixtures/foreign/src/build_foreign.py."""

import pytest

from keyline.ooxml.adapter import load_deck
from tests.conftest import FOREIGN

#            unrotated x, y, w, h            rot         bounding box x, y, w, h
EXPECTED = {
    "A": ((720000, 720000, 720000, 360000), 0, (720000, 720000, 720000, 360000)),
    "B": ((1440000, 1080000, 360000, 360000), 0, (1440000, 1080000, 360000, 360000)),
    "C": ((2520000, 1440000, 720000, 360000), 0, (2520000, 1440000, 720000, 360000)),
    "D": ((3150000, 450000, 360000, 180000), 5400000, (3240000, 360000, 180000, 360000)),
}


@pytest.fixture(scope="module")
def shapes():
    deck, diags = load_deck(FOREIGN / "nested-groups.pptx")
    assert not [f for f in diags if f.rule == "adapter-unresolved"]
    return {s.name: s for s in deck.slides[0].shapes}


def test_only_leaves_are_shapes(shapes):
    assert sorted(shapes) == ["A", "B", "C", "D"]


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_child_geometry_within_one_emu(shapes, name):
    rect, rot, box = EXPECTED[name]
    s = shapes[name]
    for got, want in zip((s.x, s.y, s.w, s.h), rect, strict=True):
        assert abs(got - want) <= 1, (name, (s.x, s.y, s.w, s.h), rect)
    assert s.rot == rot
    for got, want in zip((s.box.x, s.box.y, s.box.w, s.box.h), box, strict=True):
        assert abs(got - want) <= 1, (name, s.box, box)
