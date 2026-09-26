"""AC-17: d20 slide 6 gets an off-slide error on the table (A-13)."""

import json

from tests.acceptance._cli import keyline
from tests.acceptance._golden import has
from tests.conftest import FOREIGN

D20 = FOREIGN / "stress" / "d20_pgx_slop.pptx"


def test_table_and_chart_off_slide_are_errors():
    proc = keyline("lint", D20, "--json")
    assert proc.returncode == 2
    found = json.loads(proc.stdout)
    (table,) = has(found, "off-slide", slide=6, shape="Table 0")
    assert table["severity"] == "error" and table["measured"] == 5.0
    assert "right edge" in table["message"] and "bleed" not in table["message"]
    (chart,) = has(found, "off-slide", slide=6, shape="Chart 0")
    assert chart["severity"] == "error"
