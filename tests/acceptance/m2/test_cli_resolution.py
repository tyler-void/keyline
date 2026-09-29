"""Spec 002 §3.5 and B-8.8: how lint and check resolve mode, pack, voice and brief, and the
one-line conflicts (plan Q-13, Q-35)."""

import json

import pytest

from keyline.packs import resolve
from tests.acceptance._cli import keyline
from tests.conftest import FIXTURES

DRIFT = FIXTURES / "briefs/drift"
DECK = DRIFT / "base.pptx"
BRIEF = DRIFT / "base.brief.toml"
VOICES = resolve("swiss").directory / "voices"


def _one_line(proc, text):
    assert proc.returncode == 1 and proc.stdout == b""
    assert proc.stderr.decode() == f"keyline: {text}\n"


def test_brief_supplies_mode_pack_and_voice():
    proc = keyline("lint", DECK, "--brief", BRIEF, "--json")
    assert proc.returncode == 0 and json.loads(proc.stdout) == []


def test_no_flag_no_brief_is_presented_without_a_pack():
    proc = keyline("lint", DRIFT / "drift-role.pptx", "--json")
    assert proc.returncode == 0  # brief and pack rules do not run
    assert json.loads(proc.stdout) == json.loads(
        keyline("lint", DRIFT / "drift-role.pptx", "--mode", "presented", "--json").stdout
    )


@pytest.mark.parametrize("command", ["lint", "check"])
def test_mode_conflict(command):
    _one_line(
        keyline(command, DECK, "--brief", BRIEF, "--mode", "read"),
        "mode conflict: --mode read, brief says presented",
    )


def test_agreeing_flags_are_fine():
    for extra in (
        ("--mode", "presented"),
        ("--pack", "swiss"),
        ("--pack", str(resolve("swiss").directory)),  # the same directory (Q-13)
        ("--voice", "neutral"),
        ("--voice", str(VOICES / "neutral.toml")),  # the same content (Q-35)
    ):
        proc = keyline("lint", DECK, "--brief", BRIEF, *extra)
        assert proc.returncode == 0, (extra, proc.stderr)


def test_pack_conflict_compares_directories():
    other = FIXTURES / "briefs/packs/presented-only"
    _one_line(
        keyline("lint", DECK, "--brief", BRIEF, "--pack", other),
        f"pack conflict: --pack {other}, brief says swiss",
    )


def test_voice_conflict_compares_content():
    _one_line(
        keyline("lint", DECK, "--brief", BRIEF, "--voice", "night"),
        "voice conflict: --voice night, brief says neutral",
    )


def test_a_brief_schema_error_is_one_line():
    _one_line(
        keyline("lint", DECK, "--brief", FIXTURES / "briefs/missing-key.brief.toml"),
        "missing-key.brief.toml: direction.thesis: missing",
    )
