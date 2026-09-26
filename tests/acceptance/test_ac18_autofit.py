"""AC-18: d18 slide 2 gets body-too-small at about 9.0 pt and no title-not-dominant (A-14)."""

import json

import pytest

from tests.acceptance._cli import keyline
from tests.acceptance._golden import has
from tests.conftest import FOREIGN

D18 = FOREIGN / "stress" / "d18_lo_autofit.pptx"


@pytest.mark.parametrize("mode", ["presented", "read"])
def test_shrunk_body_is_too_small_and_title_dominates(mode):
    found = json.loads(keyline("lint", D18, "--mode", mode, "--json").stdout)
    (f,) = has(found, "body-too-small", slide=2, severity="warning")
    assert f["measured"] == 9.0  # 32 pt × fontScale 28.122% = 8.999 -> 9.00 pt
    assert "(autofit 28.1%)" in f["message"]
    assert not has(found, "title-not-dominant", slide=2)
