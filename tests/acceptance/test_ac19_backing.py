"""AC-19: d16 slide 6 has no text-contrast (A-15). AC-1…AC-4 are unchanged: their
tests and the golden snapshots run in the same suite."""

import json

from tests.acceptance._cli import keyline
from tests.acceptance._golden import has
from tests.conftest import FOREIGN

D16 = FOREIGN / "stress" / "d16_raw_color.pptx"


def test_text_box_slightly_larger_than_its_card_reads_the_card():
    found = json.loads(keyline("lint", D16, "--json").stdout)
    assert not has(found, "text-contrast", slide=6)
