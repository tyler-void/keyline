"""AC-15: d15 slide 2 has no text-contrast; d15 slide 3 gets text-contrast at 1.12:1 (A-11)."""

import json

from tests.acceptance._cli import keyline
from tests.acceptance._golden import has
from tests.conftest import FOREIGN

D15 = FOREIGN / "stress" / "d15_ppx_style_fontref.pptx"


def _findings():
    return json.loads(keyline("lint", D15, "--json").stdout)


def test_navy_card_white_style_text_is_fine():
    assert not has(_findings(), "text-contrast", slide=2)


def test_pale_card_white_style_text_is_flagged():
    (f,) = has(_findings(), "text-contrast", slide=3, severity="warning")
    assert "FFFFFF on FFF2CC" in f["message"] and "1.12:1" in f["message"]
    assert f["measured"] == 1.116


def test_explicit_black_control_is_fine():
    assert not has(_findings(), "text-contrast", slide=4)
