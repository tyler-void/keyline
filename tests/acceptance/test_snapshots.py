"""Lint output for every golden deck and mode equals the reviewed JSON in
fixtures/expected/. A behavior change shows up here as a diff to review.

To regenerate after an intended change:
    keyline lint fixtures/golden/<deck>.pptx --mode <mode> --json \\
        > fixtures/expected/<deck>.<mode>.json
"""

import pytest

from tests.acceptance._cli import keyline
from tests.conftest import FIXTURES, GOLDEN

CASES = sorted(p.name for p in (FIXTURES / "expected").glob("*.json"))


@pytest.mark.parametrize("snapshot", CASES)
def test_snapshot(snapshot):
    deck, mode, _ = snapshot.rsplit(".", 2)
    proc = keyline("lint", GOLDEN / f"{deck}.pptx", "--mode", mode, "--json")
    assert proc.stdout.decode() == (FIXTURES / "expected" / snapshot).read_text("utf-8")


def test_every_golden_and_mode_has_a_snapshot():
    decks = sorted(p.stem for p in GOLDEN.glob("*.pptx"))
    assert sorted(f"{d}.{m}.json" for d in decks for m in ("presented", "read")) == CASES
