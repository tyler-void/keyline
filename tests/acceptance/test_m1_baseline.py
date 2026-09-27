"""Spec 002 AC-2 (T-01): spec 001's output on its rule, foreign and stress decks is
unchanged. The baseline was captured on spec 001 code before any spec 002 lint change
(`tools/m1_baseline.py --write`). Golden decks keep their own snapshots
(test_snapshots.py)."""

import importlib.util

from tests.conftest import ROOT

spec = importlib.util.spec_from_file_location("m1_baseline", ROOT / "tools" / "m1_baseline.py")
m1_baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m1_baseline)


def test_baseline_covers_every_m1_deck():
    keys = m1_baseline.manifest()
    groups = {}
    for key in keys:
        groups.setdefault(key.split("/")[0], set()).add(key.split("/")[1].rsplit(".", 1)[0])
    assert {g: len(stems) for g, stems in groups.items()} == {
        "rules": 22,
        "foreign": 2,
        "stress": 13,
    }
    assert len(keys) == 74  # 37 decks x 2 modes


def test_m1_output_unchanged():
    assert m1_baseline.diff() == []
