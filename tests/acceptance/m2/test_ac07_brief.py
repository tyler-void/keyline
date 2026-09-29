"""Spec 002 AC-7: `keyline brief` on the valid brief, one fixture per §4.3 and B-4 schema
error (exit 1, one line, no traceback), and a positive and a negative fixture per §4.3
finding. Voice cases (B-8) are test_ac07_voice.py."""

import json

import pytest

from keyline.brief import load
from tests.acceptance._cli import keyline
from tests.acceptance.m2._briefs import BRIEFS, CASES, run_case
from tests.conftest import ROOT

BRIEF_CASES = [c for c in CASES if not c.get("voice")]
IDS = ("brief-reads", "brief-mood", "brief-notes", "brief-headline-long", "brief-no-statement")


@pytest.mark.parametrize("case", BRIEF_CASES, ids=[c["file"] for c in BRIEF_CASES])
def test_brief_case(case):
    run_case(case)


def test_valid_brief_prints_the_spine():
    proc = keyline("brief", BRIEFS / "valid.brief.toml")
    assert proc.returncode == 0 and proc.stdout == b""
    lines = proc.stderr.decode().splitlines()
    assert lines[:7] == [
        "01 cover      Toolshed Commons",
        "02 statement  Repairs bring members back",
        "03 section    What the bench does",
        "04 evidence   Most returned tools need a repair before the next loan",
        "05 evidence   Membership grew after the first bench opened",
        "06 quote      I came to borrow a saw and stayed to learn how to sharpen one for the "
        "next person",
        "07 close      Build the second bench this spring",
    ]
    data = json.loads(keyline("brief", BRIEFS / "valid.brief.toml", "--json").stdout)
    assert list(data) == ["spine", "findings"] and data["findings"] == []
    assert data["spine"][0] == {"slide": 1, "role": "cover", "headline": "Toolshed Commons"}


def test_every_finding_has_a_positive_and_a_negative_fixture():
    for rule in IDS:
        assert any(m.startswith(rule + "@") for c in BRIEF_CASES for m in c.get("must", []))
        assert any(rule in c.get("absent", []) for c in BRIEF_CASES)


def test_the_brief_is_typed():
    brief = load(BRIEFS / "valid.brief.toml")
    assert (brief.mode, brief.pack.name, brief.voice.name) == ("presented", "swiss", "inline")
    assert brief.voice.fonts == ("Cambria", "Calibri")
    assert brief.evidence.product.fictional
    assert list(brief.evidence.entries) == ["returns_repaired", "members_by_quarter", "bench_hours"]
    assert brief.evidence.entries["bench_hours"].tokens() == {"1,240", "1.2k"}
    assert brief.slides[4].evidence == ("members_by_quarter", "bench_hours")


def test_product_toml_is_valid_primary_evidence(tmp_path):
    """The demo's evidence file (read-only, §10) passes the §4.1 schema as it is."""
    text = (BRIEFS / "named-voice.brief.toml").read_text(encoding="utf-8")
    product = (ROOT / "examples/bonsaihub/product.toml").as_posix()
    text = text.replace(
        'evidence = ["evidence.toml", "extra-evidence.toml"]', f'evidence = ["{product}"]'
    )
    for ids in (
        'evidence = ["returns_repaired"]',
        'evidence = ["members_by_quarter", "bench_hours"]',
    ):
        text = text.replace(ids, 'evidence = ["waitlist_trees"]')
    brief_path = tmp_path / "demo.brief.toml"
    brief_path.write_text(text, encoding="utf-8")
    brief = load(brief_path)
    assert brief.evidence.product.name == "BonsaiHub" and brief.evidence.product.fictional
    assert brief.evidence.entries["keepers_by_month"].series[0] == ("Apr", 410)


def test_the_one_mode_pack_is_the_swiss_system_with_one_mode():
    swiss = (ROOT / "src/keyline/packs/swiss/pack.toml").read_text(encoding="utf-8")
    one = (BRIEFS / "packs/presented-only/pack.toml").read_text(encoding="utf-8")
    assert one == swiss.replace('modes = ["presented", "read"]', 'modes = ["presented"]')
