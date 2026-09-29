"""Audit 03 FX-14 (amendment B-20): invisible reasons, `schema` types, one error per
line whatever the user typed, and messages that name the file once."""

import json
import shutil

import pytest

from keyline.brief import BriefError, load
from keyline.escape import esc
from keyline.packs import PackError, check_accepted, resolve
from keyline.packs.voices import VoiceError
from keyline.packs.voices import load as load_voice
from keyline.packs.voices import parse as parse_voice
from tests.acceptance._cli import keyline
from tests.conftest import FIXTURES

BRIEFS = FIXTURES / "briefs"
PACK = resolve("swiss")
PACK_TOML = (PACK.directory / "pack.toml").read_text(encoding="utf-8")
DECK = BRIEFS / "drift/base.pptx"


@pytest.mark.parametrize("reason", ["\u200b", "\ufeff", "\u3000\t", "\x00", " \u2060 "])
def test_an_invisible_reason_is_empty(reason):
    with pytest.raises(ValueError, match="the reason must not be empty"):
        check_accepted([{"rule": "accent-overuse", "reason": reason}])
    assert check_accepted([{"rule": "accent-overuse", "reason": "\u200bposter"}])


def _brief(tmp_path, text, evidence=None):
    for name in ("evidence.toml", "extra-evidence.toml"):
        shutil.copyfile(BRIEFS / name, tmp_path / name)
    if evidence is not None:
        (tmp_path / "evidence.toml").write_text(evidence, encoding="utf-8")
    path = tmp_path / "b.brief.toml"
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize("value", ["true", "1.0", '"1"', "2"])
def test_schema_is_the_integer_one_everywhere(tmp_path, value):
    valid = (BRIEFS / "valid.brief.toml").read_text(encoding="utf-8")
    with pytest.raises(BriefError, match="schema: must be 1"):
        load(_brief(tmp_path, valid.replace("schema = 1", f"schema = {value}", 1)))
    evidence = (BRIEFS / "evidence.toml").read_text(encoding="utf-8")
    bad = evidence.replace("schema = 1", f"schema = {value}", 1)
    with pytest.raises(BriefError, match=r"evidence file evidence\.toml: schema must be 1"):
        load(_brief(tmp_path, valid, evidence=bad))
    (tmp_path / "pk").mkdir(exist_ok=True)
    (tmp_path / "pk/pack.toml").write_text(PACK_TOML.replace("schema = 1", f"schema = {value}", 1))
    with pytest.raises(PackError, match="schema: must be the integer 1"):
        resolve(tmp_path / "pk")
    voice = (PACK.directory / "voices/neutral.toml").read_text(encoding="utf-8")
    (tmp_path / "neutral.toml").write_text(voice.replace("schema = 1", f"schema = {value}", 1))
    with pytest.raises(VoiceError, match="schema must be the integer 1"):
        load_voice(PACK, tmp_path / "neutral.toml")
    with pytest.raises(VoiceError, match="schema must be the integer 1"):
        parse_voice({"schema": json.loads(value) if value != '"1"' else "1"}, PACK)


@pytest.mark.parametrize(
    "args",
    [
        ["lint", DECK, "--pack", "swiss\nkeyline: all clear", "--voice", "neutral"],
        ["lint", DECK, "--pack", "swiss", "--voice", "dusk\u2028ok"],
        ["lint", "no\nsuch.pptx"],
        ["render", "no\rsuch.pptx", "-o", "out"],
    ],
)
def test_user_text_cannot_forge_a_second_line(args):
    proc = keyline(*args)
    lines = proc.stderr.decode().splitlines()
    assert proc.returncode == 1
    assert len([x for x in lines if x.startswith("keyline:")]) == 1
    assert not any(x.startswith("keyline: all clear") for x in lines)


def test_a_briefs_pack_value_with_a_line_break(tmp_path):
    valid = (BRIEFS / "valid.brief.toml").read_text(encoding="utf-8")
    path = _brief(tmp_path, valid.replace('pack = "swiss"', 'pack = "swiss\\n"'))
    proc = keyline("brief", path)
    assert proc.returncode == 1
    assert proc.stderr.decode() == "keyline: b.brief.toml: pack not found: swiss\\n\n"


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("accepted = []\n", "", "pack.toml: top level: missing key 'accepted'"),
        ('dk1 = "ink"', "dk1 = 5", "pack.toml: theme.dk1: must be a palette role name"),
    ],
)
def test_pack_messages_name_the_key_once(tmp_path, old, new, message):
    (tmp_path / "pk").mkdir()
    (tmp_path / "pk/pack.toml").write_text(PACK_TOML.replace(old, new, 1))
    with pytest.raises(PackError) as err:
        resolve(tmp_path / "pk")
    assert str(err.value) == message


def test_file_messages_name_the_file_once(tmp_path):
    (tmp_path / "p-deep").mkdir()
    (tmp_path / "p-deep/pack.toml").write_text("a = " + "[" * 5000 + "]" * 5000)
    with pytest.raises(PackError) as err:
        resolve(tmp_path / "p-deep")
    message = str(err.value)  # "nests too deeply", or a TOML error on newer Pythons
    assert message.startswith("pack file p-deep/pack.toml ") and message.count("pack.toml") == 1
    (tmp_path / "tmp").mkdir()
    proc = keyline("brief", tmp_path / "tmp")
    assert proc.stderr.decode() == "keyline: tmp: brief is a directory, not a file\n"


def test_esc_is_idempotent_and_keeps_printable_text():
    assert esc("Nguồn: khảo sát") == "Nguồn: khảo sát"
    assert esc("a\nb\u2028c\x85d\u200be") == "a\\nb\\u2028c\\x85d\\u200be"
    assert esc(esc("a\nb")) == esc("a\nb")
