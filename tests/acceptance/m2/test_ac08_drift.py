"""Spec 002 AC-8 in phase A1 (amendment B-3): a deck built by a fixture script that
writes what the pen will write, checked against its brief. `check --brief` exits 0 on
the base, and each of the six pinned drifts gives exactly its one expected finding.
A2 repeats this on a pen-built deck."""

import json
import subprocess
import sys

import pytest

from keyline.ooxml.adapter import load_deck
from keyline.packs import resolve
from tests.acceptance._cli import keyline
from tests.conftest import FIXTURES, ROOT

DRIFT = FIXTURES / "briefs/drift"
BRIEF = DRIFT / "base.brief.toml"
EXPECTED = {
    "drift-headline": "brief-headline",
    "drift-slide-count": "brief-slide-count",
    "drift-unsourced": "unsourced-number",
    "drift-source-missing": "source-missing",
    "drift-undisclosed": "fiction-undisclosed",
    "drift-role": "brief-role",
}


def test_check_brief_exits_0_on_the_base(tmp_path):
    proc = keyline("check", DRIFT / "base.pptx", "--brief", BRIEF, "-o", tmp_path, "--json")
    assert proc.returncode == 0, proc.stderr.decode()
    assert json.loads(proc.stdout) == []


@pytest.mark.parametrize("name", list(EXPECTED))
def test_each_drift_gives_exactly_its_one_finding(name):
    proc = keyline("lint", DRIFT / f"{name}.pptx", "--brief", BRIEF, "--json")
    rules = [f["rule"] for f in json.loads(proc.stdout)]
    assert rules == [EXPECTED[name]]


def test_the_base_is_pen_like():
    """Swiss layouts; every region placeholder on its region box; source and note lines."""
    pack = resolve("swiss")
    deck, diags = load_deck(DRIFT / "base.pptx")
    assert diags == []
    region_of = {0: "title", **{i: r for r, i in pack.placeholder_idx.items()}}
    lines = []
    for slide in deck.slides:
        assert slide.layout_name in pack.regions
        for shape in slide.shapes:
            if shape.ph_type is None and shape.ph_idx is None:
                continue
            region = region_of[shape.ph_idx or 0]
            box = pack.region_box(slide.layout_name, region)
            assert (shape.x, shape.y, shape.w, shape.h) == (box.x, box.y, box.w, box.h)
            if region == "footer":
                lines.append(shape.text.split(":")[0])
    assert lines == ["Source", "Source", "Note"]


def test_the_drift_decks_rebuild_byte_identically(tmp_path):
    pytest.importorskip("pptx")
    script = ROOT / "fixtures/briefs/src/build_drift.py"
    subprocess.run([sys.executable, script, tmp_path], check=True, capture_output=True)
    for name in ["base", *EXPECTED]:
        assert (tmp_path / f"{name}.pptx").read_bytes() == (DRIFT / f"{name}.pptx").read_bytes()
