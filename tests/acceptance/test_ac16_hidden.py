"""AC-16: d17 slide 4 has no off-slide or text-contrast on the hidden shapes, and
dead-band fires on the 8.0–19.05 cm band (A-12)."""

import json

from keyline.ooxml.adapter import load_deck
from tests.acceptance._cli import keyline
from tests.acceptance._golden import has
from tests.conftest import FOREIGN

D17 = FOREIGN / "stress" / "d17_raw_geometry.pptx"
HIDDEN = {"Parked note", "Hidden white", "Hidden filler"}


def _slide4():
    return [f for f in json.loads(keyline("lint", D17, "--json").stdout) if f["slide"] == 4]


def test_hidden_shapes_raise_nothing():
    found = _slide4()
    assert not [f for f in found if f["shape_name"] in HIDDEN]
    assert not has(found, "off-slide") and not has(found, "text-contrast")


def test_dead_band_on_the_lower_band():
    (band,) = has(_slide4(), "dead-band", severity="warning")
    assert "from 8.00 to 19.05 cm" in band["message"] and band["measured"] == 0.58


def test_one_advisory_counts_the_hidden_shapes():
    (f,) = has(_slide4(), "unsupported-content")
    assert f["severity"] == "advisory" and f["message"].startswith("3 hidden shapes")


def test_hidden_shapes_are_not_in_the_model():
    deck, _ = load_deck(D17)
    assert not HIDDEN & {s.name for s in deck.slides[3].shapes}
