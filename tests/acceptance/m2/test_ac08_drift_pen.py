"""Spec 002 AC-8 in phase A2 (amendment B-3, task T-29): the drift base is written by the
pen from its brief, and the six pinned drifts of A1 are re-applied to it. `check --brief`
exits 0 on the base, and each drift gives exactly its one expected finding."""

import json
import subprocess
import sys

import pytest

from keyline.ooxml.adapter import load_deck
from tests.acceptance._cli import keyline
from tests.acceptance.m2.test_ac08_drift import EXPECTED
from tests.conftest import FIXTURES, ROOT

DRIFT = FIXTURES / "briefs/drift-pen"
BRIEF = FIXTURES / "briefs/drift/base.brief.toml"


def test_check_brief_exits_0_on_the_pen_built_base(tmp_path):
    proc = keyline("check", DRIFT / "base.pptx", "--brief", BRIEF, "-o", tmp_path, "--json")
    assert proc.returncode == 0, proc.stderr.decode()
    assert json.loads(proc.stdout) == []


@pytest.mark.parametrize("name", list(EXPECTED))
def test_each_drift_gives_exactly_its_one_finding(name):
    proc = keyline("lint", DRIFT / f"{name}.pptx", "--brief", BRIEF, "--json")
    rules = [f["rule"] for f in json.loads(proc.stdout)]
    assert rules == [EXPECTED[name]]


def test_the_pen_base_says_what_the_a1_base_says():
    """Same layouts and the same texts, slide by slide; only the writer differs."""

    def texts(path):
        deck, diags = load_deck(path)
        assert diags == []
        return [(s.layout_name, sorted(sh.text for sh in s.shapes if sh.text)) for s in deck.slides]

    assert texts(DRIFT / "base.pptx") == texts(FIXTURES / "briefs/drift/base.pptx")


def test_the_pen_drift_decks_rebuild_byte_identically(tmp_path):
    pytest.importorskip("pptx")
    script = ROOT / "fixtures/briefs/src/build_drift_pen.py"
    subprocess.run([sys.executable, script, tmp_path], check=True, capture_output=True)
    for name in ["base", *EXPECTED]:
        assert (tmp_path / f"{name}.pptx").read_bytes() == (DRIFT / f"{name}.pptx").read_bytes()
