"""Amendment B-8.4 and B-8.5 in `keyline brief`: a brief names its voice or carries an
inline one, the voice schema errors are exit 1 with one line, and each voice finding has
a positive and a negative fixture."""

import pytest

from keyline.brief import findings, load
from tests.acceptance.m2._briefs import BRIEFS, CASES, run_case

VOICE_CASES = [c for c in CASES if c.get("voice")]
IDS = ("voice-contrast", "voice-claude-look", "voice-why")


@pytest.mark.parametrize("case", VOICE_CASES, ids=[c["file"] for c in VOICE_CASES])
def test_voice_case(case):
    run_case(case)


def test_every_voice_finding_has_a_positive_and_a_negative_fixture():
    for rule in IDS:
        assert any(m.startswith(rule + "@") for c in CASES for m in c.get("must", []))
        assert any(rule in c.get("absent", []) for c in CASES)


def test_named_voice_is_the_pack_voice_and_needs_no_why():
    brief = load(BRIEFS / "named-voice.brief.toml")
    assert brief.voice.name == "night" and brief.voice.path is not None
    assert findings(brief) == []


def test_voice_finding_messages():
    (contrast,) = findings(load(BRIEFS / "voice-contrast--pos.brief.toml"))
    assert contrast.message == (
        "voice inline: muted #9A9A98 on the paper surface #EEF0F2 is 2.47 : 1 (needs 4.5 : 1)"
    )
    assert (contrast.measured, contrast.threshold) == (2.47, 4.5)
    (look,) = findings(load(BRIEFS / "voice-claude-look--pos.brief.toml"))
    assert look.message == "voice inline: paper #F4F3EE is cream and accent #A8502F is a terracotta"
    (accepted,) = findings(load(BRIEFS / "voice-claude-look--accepted.brief.toml"))
    assert accepted.message.endswith("(accepted: a pottery studio's own clay and kiln colours)")
    (why,) = findings(load(BRIEFS / "voice-why--pos.brief.toml"))
    assert why.message == "inline voice has no why line for hairline"
