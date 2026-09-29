"""Spec 002 §3.5 and amendment B-8.8 at the command line: --pack needs a voice, --voice
needs a pack, a voice is a name or a file, `accepted` downgrades, and a voice that fails
its own checks is named on stderr (plan Q-29c, Q-31, Q-35)."""

import json

from keyline.packs import resolve
from tests.acceptance._cli import keyline
from tests.conftest import RULES

NIGHT = RULES / "pack-voice-night.pptx"
VOICES = resolve("swiss").directory / "voices"


def _err(proc):
    return proc.stderr.decode()


def test_pack_without_voice_and_voice_without_pack_exit_1():
    for args in (("--pack", "swiss"), ("--voice", "night")):
        for command in ("lint", "check"):
            proc = keyline(command, NIGHT, *args)
            assert proc.returncode == 1 and proc.stdout == b""
            assert len(_err(proc).splitlines()) == 1
    assert "pack rules need a voice (--voice or --brief)" in _err(
        keyline("lint", NIGHT, "--pack", "swiss")
    )
    assert "--voice needs a pack (--pack or --brief)" in _err(
        keyline("lint", NIGHT, "--voice", "night")
    )


def test_unknown_pack_or_voice_exit_1_with_one_line():
    proc = keyline("lint", NIGHT, "--pack", "swiss", "--voice", "dusk")
    assert proc.returncode == 1
    assert _err(proc) == (
        "keyline: unknown voice 'dusk' for pack swiss (voices: field, neutral, night)\n"
    )
    proc = keyline("lint", NIGHT, "--pack", "nope", "--voice", "night")
    assert proc.returncode == 1 and _err(proc) == "keyline: pack not found: nope\n"


def test_voice_by_name_and_by_file_agree():
    by_name = keyline("lint", NIGHT, "--pack", "swiss", "--voice", "night", "--json")
    by_file = keyline("lint", NIGHT, "--pack", "swiss", "--voice", VOICES / "night.toml", "--json")
    assert by_name.returncode == by_file.returncode == 0
    assert json.loads(by_name.stdout) == json.loads(by_file.stdout) == []


def test_the_voice_decides_what_is_off():
    proc = keyline("lint", NIGHT, "--pack", "swiss", "--voice", "neutral", "--json")
    rules = {f["rule"] for f in json.loads(proc.stdout)}
    assert proc.returncode == 2 and rules == {"off-palette-color"}


def _voice_file(tmp_path, name, **changes):
    text = (VOICES / "neutral.toml").read_text(encoding="utf-8")
    text = text.replace('name = "neutral"', f'name = "{name}"')
    for role, value in changes.items():
        start = text.index(f"\n{role} = ") + 1
        end = text.index("\n", start)
        text = text[:start] + f'{role} = "{value}"' + text[end:]
    path = tmp_path / f"{name}.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_accepted_in_a_voice_downgrades_to_advisory(tmp_path):
    path = _voice_file(tmp_path, "loud")
    text = path.read_text(encoding="utf-8")  # top level, before the first table
    accepted = 'accepted = [{ rule = "accent-overuse", reason = "a poster deck" }]\n'
    path.write_text(text.replace("\n[fonts]", f"\n{accepted}\n[fonts]", 1), encoding="utf-8")
    deck = RULES / "accent-overuse--pos.pptx"
    plain = keyline("lint", deck, "--pack", "swiss", "--voice", "neutral", "--json")
    loud = keyline("lint", deck, "--pack", "swiss", "--voice", path, "--json")
    (before,) = [f for f in json.loads(plain.stdout) if f["rule"] == "accent-overuse"]
    (after,) = [f for f in json.loads(loud.stdout) if f["rule"] == "accent-overuse"]
    assert before["severity"] == "warning" and after["severity"] == "advisory"
    assert after["message"] == before["message"] + " (accepted: a poster deck)"


def test_a_failing_voice_is_named_on_stderr_not_in_the_findings(tmp_path):
    path = _voice_file(tmp_path, "faint", muted="9A9A98")  # 2.51 : 1 on paper
    deck = RULES / "off-palette-color--neg.pptx"
    proc = keyline("lint", deck, "--pack", "swiss", "--voice", path, "--json")
    lines = [x for x in _err(proc).splitlines() if x.startswith("voice ")]
    assert lines == [
        "voice faint: voice-contrast: muted #9A9A98 on the paper surface #F2F2F0 is "
        "2.51 : 1 (needs 4.5 : 1)"
    ]
    assert all(not f["rule"].startswith("voice-") for f in json.loads(proc.stdout))
