"""Fit tables (spec 002 §6.4, B-8.11, B-21; task T-21): one per portable family and
weight, with line_pitch_em and the LibreOffice versions behind it, the twin's missing
Vietnamese letters, and its source in NOTICE. Rebuilds are byte-identical wherever the
same font file is installed; other twins skip by name."""

import hashlib
import shutil
import subprocess
import sys
import unicodedata
from fractions import Fraction

import pytest

from keyline.config import load as load_config
from keyline.fit import VIETNAMESE, WEIGHTS, load_table, table_path
from tests.conftest import ROOT

FAMILIES = load_config().portable_fonts
NOTICE = (ROOT / "NOTICE").read_text(encoding="utf-8")


def test_the_134_vietnamese_letters():
    assert len(VIETNAMESE) == 134 and len(set(VIETNAMESE)) == 134
    assert all(unicodedata.normalize("NFC", c) == c for c in VIETNAMESE)
    assert "ự" in VIETNAMESE and "Đ" in VIETNAMESE and "ỹ" in VIETNAMESE


@pytest.mark.parametrize(("family", "twin"), FAMILIES)
@pytest.mark.parametrize("weight", WEIGHTS)
def test_every_table(family, twin, weight):
    t = load_table(family, weight)
    assert (t.family, t.twin, t.weight) == (family, twin, weight)
    assert t.line_pitch_em == Fraction(6, 5)  # B-21
    assert any("26.8.0.3" in v for v in t.measured_on)  # Q-44b
    assert t.advance("H") > 0 and t.advance("\U0010fffd") == t.max_advance
    assert max(t.advances.values()) <= t.max_advance
    assert t.source["licence"] == "OFL-1.1"
    assert f"{t.source['file']}, {t.source['version']}, OFL-1.1" in NOTICE


def test_missing_vietnamese_letters():
    """Audit 04: Caladea (for Cambria) lacks 88 of 134; the other twins lack none."""
    for family, _twin in FAMILIES:
        for weight in WEIGHTS:
            missing = load_table(family, weight).missing_vietnamese
            if family == "Cambria":
                assert len(missing) == 88 and "Ơ" in missing and "ạ" in missing
            else:
                assert missing == "", family


def test_a_known_advance():
    """Liberation Sans Regular: 'A' is 1366 of 2048 units, as Arial's."""
    t = load_table("Arial", "regular")
    assert (t.units_per_em, t.advance("A")) == (2048, 1366)


def _installed(family, weight):
    style = "Bold" if weight == "bold" else "Regular"
    out = subprocess.run(
        ["fc-match", "-f", "%{file}", f"{family}:style={style}"], capture_output=True, text=True
    )
    return out.stdout.strip()


@pytest.mark.skipif(shutil.which("fc-match") is None, reason="fc-match is not installed")
@pytest.mark.parametrize(("family", "twin"), FAMILIES)
@pytest.mark.parametrize("weight", WEIGHTS)
def test_rebuild_is_byte_identical(family, twin, weight):
    pytest.importorskip("fontTools")
    path = _installed(family, weight)
    recorded = load_table(family, weight).source["sha256"]
    try:
        with open(path, "rb") as f:
            installed = hashlib.sha256(f.read()).hexdigest()
    except OSError:
        installed = None
    if installed != recorded:
        pytest.skip(f"{twin} {weight}: the installed font file is not the one the table used")
    sys.path.insert(0, str(ROOT / "tools"))
    import gen_fit_tables

    text, _source = gen_fit_tables.table(family, twin, weight)
    assert text == table_path(twin, weight).read_text(encoding="utf-8")
