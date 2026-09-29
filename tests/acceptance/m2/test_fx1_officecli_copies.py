"""Audit 02 FX-1 (amendment B-14, L-016): OfficeCLI keeps a document in a resident process
for about 60 s, so keyline gives it a private copy every time. The stale sequences A and
B each run twice in a row, well inside that window."""

import json
import shutil

import pytest
from PIL import Image, ImageChops

from keyline import officecli
from keyline import validate as validate_mod
from tests.acceptance._cli import keyline
from tests.conftest import FIXTURES, GOLDEN

CLEAN = GOLDEN / "editorial.pptx"
BOGUS = FIXTURES / "validate/editorial-bogus.pptx"


def _invalid(path):
    return [f for f in validate_mod.validate(path) if f.rule == "ooxml-invalid"]


@pytest.mark.officecli
@pytest.mark.parametrize("repeat", [1, 2])
def test_sequence_a_clean_then_bogus_on_one_path(tmp_path, repeat):
    deck = tmp_path / "deck.pptx"
    shutil.copyfile(CLEAN, deck)
    assert _invalid(deck) == []
    shutil.copyfile(BOGUS, deck)
    assert len(_invalid(deck)) == 1


@pytest.mark.officecli
@pytest.mark.parametrize("repeat", [1, 2])
def test_sequence_b_bogus_then_clean_on_one_path(tmp_path, repeat):
    deck = tmp_path / "deck.pptx"
    shutil.copyfile(BOGUS, deck)
    assert len(_invalid(deck)) == 1
    shutil.copyfile(CLEAN, deck)
    assert _invalid(deck) == []


@pytest.mark.officecli
def test_check_sees_the_replaced_deck(tmp_path):
    deck = tmp_path / "deck.pptx"
    counts = []
    for source in (CLEAN, BOGUS, CLEAN, BOGUS):
        shutil.copyfile(source, deck)
        blocker = tmp_path / "no-render"  # a file: the render step is skipped (B-13)
        blocker.touch()
        proc = keyline("check", deck, "--json", "-o", blocker)
        counts.append(sum(f["rule"] == "ooxml-invalid" for f in json.loads(proc.stdout)))
    assert counts == [0, 1, 0, 1]


@pytest.mark.officecli
def test_officecli_render_sees_the_replaced_deck(tmp_path):
    deck = tmp_path / "deck.pptx"
    shutil.copyfile(GOLDEN / "kpi-recipe.pptx", deck)  # 4 slides
    first = keyline("render", deck, "-o", tmp_path / "a", "--engine", "officecli")
    assert first.returncode == 0, first.stderr.decode()
    shutil.copyfile(FIXTURES / "briefs/drift/base.pptx", deck)  # 5 slides
    second = keyline("render", deck, "-o", tmp_path / "b", "--engine", "officecli")
    assert second.returncode == 0, second.stderr.decode()
    assert len(list((tmp_path / "b").glob("slide-*.png"))) == 5
    with Image.open(tmp_path / "a/slide-01.png") as a, Image.open(tmp_path / "b/slide-01.png") as b:
        assert (
            a.size != b.size or ImageChops.difference(a.convert("RGB"), b.convert("RGB")).getbbox()
        )


def test_the_copy_is_private_released_and_deleted(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(officecli.shutil, "which", lambda name: "/usr/bin/officecli")
    monkeypatch.setattr(officecli.subprocess, "run", lambda cmd, **kw: calls.append(cmd))
    with officecli.private_copy(CLEAN) as copy:
        assert copy.is_file() and copy.parent != CLEAN.parent and copy.suffix == ".pptx"
        assert copy.read_bytes() == CLEAN.read_bytes()
        with officecli.private_copy(CLEAN) as other:
            assert other != copy  # unique per call
    assert calls[-1] == ["/usr/bin/officecli", "close", str(copy)]
    assert not copy.parent.exists()


def test_the_copy_is_released_even_when_the_call_fails(monkeypatch):
    calls = []
    monkeypatch.setattr(officecli.shutil, "which", lambda name: "/usr/bin/officecli")
    monkeypatch.setattr(officecli.subprocess, "run", lambda cmd, **kw: calls.append(cmd))
    with pytest.raises(RuntimeError), officecli.private_copy(CLEAN) as copy:
        raise RuntimeError("boom")
    assert calls == [["/usr/bin/officecli", "close", str(copy)]] and not copy.parent.exists()
