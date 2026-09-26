"""AC-8: three runs on each golden fixture produce byte-identical JSON."""

import pytest

from tests.acceptance._cli import keyline
from tests.conftest import GOLDEN

DECKS = ["kpi-recipe.pptx", "editorial.pptx"]


@pytest.mark.parametrize("mode", ["presented", "read"])
@pytest.mark.parametrize("deck", DECKS)
def test_three_runs_byte_identical(deck, mode):
    runs = [keyline("lint", GOLDEN / deck, "--mode", mode, "--json") for _ in range(3)]
    assert {r.returncode for r in runs} == {2}
    assert runs[0].stdout == runs[1].stdout == runs[2].stdout
    assert runs[0].stderr == runs[1].stderr == runs[2].stderr
