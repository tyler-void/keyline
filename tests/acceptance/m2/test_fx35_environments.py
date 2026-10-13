"""Audit 07 FX-35 (amendment B-27 item 5): `missing_glyph_em` and `missing_line_em` take the
largest value measured in any environment Tyler or the auditor has run, and each
environment is recorded with the data (fit/tables/environments.json, written by
tools/gen_measured.py from tools/measure_lo.py outputs). In the auditor's environment
fontconfig's Thai fallback is Loma, hhea 1.589 em, above the 1.52 measured on Tyler's
machine, where it is Noto Sans Thai. Evidence: audit07-repros/pytest-24.2-failure.txt."""

import importlib.util
import json
import math
import sys
from fractions import Fraction as F

from keyline.config import load as load_config
from keyline.fit import cell_data
from tests.conftest import ROOT

ENVIRONMENTS = ROOT / "src/keyline/fit/tables/environments.json"
DATA = json.loads(ENVIRONMENTS.read_text(encoding="utf-8"))


def gen_measured():
    spec = importlib.util.spec_from_file_location("gen_measured", ROOT / "tools/gen_measured.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_measured"] = module
    spec.loader.exec_module(module)
    return module


def ceil2(values):
    return F(math.ceil(max(F(v) for v in values) * 100), 100)


def test_the_data_is_rederived():
    """From the committed measure_lo outputs alone: no LibreOffice, no fonts."""
    assert gen_measured().environments() == ENVIRONMENTS.read_text(encoding="utf-8")


def test_every_environment_is_recorded():
    envs = DATA["environments"]
    assert [(e["who"], e["version"].split()[1]) for e in envs] == [
        ("Tyler", "26.8.0.3"),
        ("Tyler", "26.8.1.1"),
        ("the auditor", "24.2.7.2"),
    ]
    for e in envs:
        assert (ROOT / e["source"]).is_file() and e["platform"] and e["date"]
        assert set(e["fallback_fonts"]) == {"cjk", "emoji", "thai"}
    auditor = envs[2]["fallback_fonts"]["thai"]
    assert auditor == {"file": "Loma.otf", "hhea_line_em": "1.5894"}
    assert envs[0]["fallback_fonts"]["thai"]["file"] == "NotoSansThai-Regular.ttf"


def test_the_thresholds_are_the_largest_over_the_environments():
    envs = DATA["environments"]
    glyph = ceil2(e["widest_fallback_advance_em"] for e in envs)
    line = ceil2(
        [e["widest_fallback_cell_line_em"] for e in envs]
        + [f["hhea_line_em"] for e in envs for f in e["fallback_fonts"].values()]
    )
    excess = ceil2(e["cell_line_excess_mm"] for e in envs)
    assert (glyph, line, excess) == (F("1.49"), F("1.59"), F("0.05"))
    assert (F(DATA["missing_glyph_em"]), F(DATA["missing_line_em"])) == (glyph, line)
    assert F(DATA["cell_line_allowance_mm"]) == excess
    config = load_config()
    assert config.missing_glyph_em == glyph and config.missing_line_em == line
    assert config.cell_line_allowance_mm == excess
    assert cell_data() == (excess * F(72, 254) * 10, line)


def test_the_value_before_the_fix_did_not_cover_the_auditors_fallback():
    loma = F(DATA["environments"][2]["fallback_fonts"]["thai"]["hhea_line_em"])
    assert F("1.52") < loma <= load_config().missing_line_em
