"""Audit 03 FX-10 (amendment B-19): the OfficeCLI copy is named .pptx whatever the user's
file name, and .pptm only for a .pptm deck (principle III is about content, not names)."""

import json
import shutil

import pytest

from keyline import officecli
from tests.acceptance._cli import keyline
from tests.conftest import GOLDEN


@pytest.mark.parametrize(
    ("name", "suffix"),
    [
        ("clean v1.2", ".pptx"),
        ("deck.pptx.bak", ".pptx"),
        ("no-suffix", ".pptx"),
        ("x.PPTX", ".pptx"),
        ("x.pptm", ".pptm"),
        ("x.PPTM", ".pptm"),
    ],
)
def test_the_copy_suffix(tmp_path, monkeypatch, name, suffix):
    monkeypatch.setattr(officecli.shutil, "which", lambda n: None)  # no close call needed
    deck = tmp_path / name
    shutil.copyfile(GOLDEN / "editorial.pptx", deck)
    with officecli.private_copy(deck) as copy:
        assert copy.suffix == suffix and copy.name.startswith("deck-")


@pytest.mark.officecli
@pytest.mark.parametrize("name", ["clean v1.2", "deck.pptx.bak"])
def test_odd_names_validate_like_pptx(tmp_path, name):
    deck = tmp_path / name
    shutil.copyfile(GOLDEN / "editorial.pptx", deck)
    blocker = tmp_path / "no-render"
    blocker.touch()
    proc = keyline("check", deck, "--json", "-o", blocker)
    assert [f for f in json.loads(proc.stdout) if f["rule"] == "ooxml-invalid"] == []
    assert "validate: passed" in proc.stderr.decode()
