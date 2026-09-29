"""Voices (spec 002 amendment B-8, T-08r): loading, the B-8.5 schema errors, the checks."""

import copy
import tomllib

import pytest

from keyline.config import load as load_cfg
from keyline.packs import resolve
from keyline.packs.voices import (
    VoiceError,
    claude_look,
    contrast_pairs,
    is_path,
    load,
    low_contrast,
    missing_why,
    parse,
)

PACK = resolve("swiss")
VOICES = PACK.directory / "voices"
RAW = tomllib.loads((VOICES / "neutral.toml").read_text(encoding="utf-8"))
RAW.pop("name")  # parse() is the inline form; `name` belongs to a voice file (B-18)
CFG = load_cfg()


def voice(mutate=lambda d: None):
    data = copy.deepcopy(RAW)
    mutate(data)
    return parse(data, PACK, where="voice test")


def test_stock_voices_load_by_name_and_by_file(tmp_path):
    assert [load(PACK, n).name for n in PACK.voices()] == ["field", "neutral", "night"]
    by_file = load(PACK, VOICES / "night.toml")
    assert by_file.same_as(load(PACK, "night")) and by_file.path == VOICES / "night.toml"
    rel = load(PACK, "voices/field.toml", base=PACK.directory)
    assert rel.display == "Georgia" and rel.fonts == ("Georgia",)


def test_name_or_file():
    assert not is_path("night")
    assert is_path("my.toml") and is_path("voices/night") and is_path("a\\b")


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda d: d["palette"].pop("muted"), "missing the role 'muted'"),
        (lambda d: d["palette"].update(gold="D4A017"), "extra role 'gold'"),
        (lambda d: d["palette"].update(ink="11111G"), "palette.ink '11111G' is not 6-digit hex"),
        (lambda d: d["palette"].update(ink="#111111"), "palette.ink '#111111' is not 6-digit"),
        (lambda d: d["palette"].update(ink="111"), "is not 6-digit hex"),
        (lambda d: d["fonts"].update(display="Verdana"), "fonts.display 'Verdana' is not a"),
        (lambda d: d["fonts"].update(text="Calibri Light"), "fonts.text 'Calibri Light'"),
        (lambda d: d["fonts"].pop("text"), "fonts.text must be a font family"),
        (lambda d: d.pop("fonts"), r"missing \[fonts\] table"),
        (lambda d: d.pop("palette"), r"missing \[palette\] table"),
        (lambda d: d["palette"].update(accent="111111"), "accent has the same value as ink"),
        (lambda d: d.update(accepted=["voice-claude-look"]), "rule, reason"),
        (
            lambda d: d.update(accepted=[{"rule": "fiction-undisclosed", "reason": "x"}]),
            r"accepted\[1\]: 'fiction-undisclosed' cannot be accepted",
        ),
        (
            lambda d: d.update(accepted=[{"rule": "voice-claude-look", "reason": ""}]),
            r"accepted\[1\]: the reason must not be empty",
        ),
    ],
)
def test_schema_errors_are_one_line(mutate, message):
    with pytest.raises(VoiceError, match=message) as err:
        voice(mutate)
    assert "\n" not in str(err.value)


def test_unknown_voice_name_lists_the_known_ones():
    with pytest.raises(VoiceError, match=r"unknown voice 'dusk' .*field, neutral, night"):
        load(PACK, "dusk")
    with pytest.raises(VoiceError, match="voice file not found"):
        load(PACK, "missing.toml")


def test_file_name_must_match_and_schema_is_required(tmp_path):
    text = (VOICES / "night.toml").read_text(encoding="utf-8")
    (tmp_path / "dusk.toml").write_text(text, encoding="utf-8")
    with pytest.raises(VoiceError, match="name 'night' must equal the file name 'dusk'"):
        load(PACK, tmp_path / "dusk.toml")
    (tmp_path / "night.toml").write_text(text.replace("schema = 1", ""), encoding="utf-8")
    with pytest.raises(VoiceError, match="schema must be the integer 1"):
        load(PACK, tmp_path / "night.toml")


def test_values_are_normalised():
    v = voice(lambda d: d["palette"].update(ink="aa0b0c") or d["fonts"].update(text=" georgia "))
    assert v.hex("ink") == "AA0B0C" and v.text == "Georgia" and v.fonts == ("Arial", "Georgia")
    assert v.font("display") == "Arial" and v.font("text") == "Georgia"


def test_inline_voice_needs_no_name_or_schema():
    data = {k: v for k, v in RAW.items() if k != "schema"}
    v = parse(data, PACK)
    assert v.name == "inline" and v.path is None and missing_why(PACK, v) == []


def test_contrast_pairs_are_the_surfaces_text_roles():
    pairs = [(p.text, p.surface) for p in contrast_pairs(PACK, load(PACK, "neutral"))]
    assert pairs == [
        ("ink", "paper"),
        ("muted", "paper"),
        ("accent", "paper"),
        ("paper", "ink"),
        ("accent_on_ink", "ink"),
    ]


def test_low_contrast_names_each_pair():
    v = voice(lambda d: d["palette"].update(muted="9A9A98", accent_on_ink="5A1A10"))
    assert [(p.text, p.surface) for p in low_contrast(PACK, v, CFG)] == [
        ("muted", "paper"),
        ("accent_on_ink", "ink"),
    ]


def test_claude_look_states():
    assert not claude_look(PACK, load(PACK, "neutral"), CFG).fires
    cream = voice(lambda d: d["palette"].update(paper="F4F3EE"))
    look = claude_look(PACK, cream, CFG)
    assert look.fires and look.cream == ("paper",) and look.terracotta == ()  # advisory
    both = voice(lambda d: d["palette"].update(paper="F4F3EE", accent="C96442"))
    assert claude_look(PACK, both, CFG).terracotta == ("accent",)  # warning
    dark = voice(lambda d: d["palette"].update(paper="16181B", ink="F4F3EE"))
    assert claude_look(PACK, dark, CFG).cream == ("ink",)  # B-9: the section surface


def test_missing_why_per_role():
    v = voice(lambda d: d.update(why={"paper": "sand", "ink": "  "}))
    assert missing_why(PACK, v) == ["ink", "muted", "hairline", "accent", "accent_on_ink"]


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda d: d.update(wobble="x"), r"voice test: unknown key 'wobble'"),
        (lambda d: d.update(name="neutral"), r"voice test: unknown key 'name'"),  # inline
        (lambda d: d["fonts"].update(weight="bold"), r"fonts has an unknown key 'weight'"),
        (lambda d: d["why"].update(gold="x"), r"why has an unknown key 'gold' \(not a palette"),
        (
            lambda d: d["why"].update(accepted=[{"rule": "accent-overuse", "reason": "x"}]),
            r"why\.accepted: accepted belongs before \[fonts\]",
        ),
    ],
)
def test_the_voice_schema_is_closed(mutate, message):
    """Amendment B-18 (audit 03, FX-12): any other key is a schema error naming it."""
    with pytest.raises(VoiceError, match=message):
        voice(mutate)


def test_accepted_after_why_in_a_voice_file_is_an_error(tmp_path):
    """The audit's repro: accepted written after [why], as B-8.2's example showed it."""
    text = (
        (VOICES / "neutral.toml")
        .read_text(encoding="utf-8")
        .replace('name = "neutral"', 'name = "spec"')
    )
    path = tmp_path / "spec.toml"
    path.write_text(
        text + 'accepted = [{ rule = "unsourced-number", reason = "" }]\nwobble = "x"\n',
        encoding="utf-8",
    )
    with pytest.raises(VoiceError, match=r"why\.accepted: accepted belongs before \[fonts\]"):
        load(PACK, path)
    fixed = tmp_path / "ok.toml"
    fixed.write_text(text.replace('name = "spec"', 'name = "ok"\naccepted = []'), encoding="utf-8")
    assert load(PACK, fixed).accepted == ()
