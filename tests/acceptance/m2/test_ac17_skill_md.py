"""Spec 002 AC-17 (§8.2; task T-34; audit 07 §4.4): `skill/keyline/SKILL.md`. The
frontmatter follows the agentskills.io specification with claude.ai's stricter limit;
the body has at most 200 lines, no `${` substitution, no shell injection and no absolute
path; it says how to find the skill's folder, gives every token `doctor` can print an
action, routes to "check a deck" when python-pptx cannot be installed, and has the voice
step as a step of its own (B-8.15)."""

import re

from tests.conftest import ROOT

SKILL = ROOT / "skill" / "keyline"
TEXT = (SKILL / "SKILL.md").read_text(encoding="utf-8")
FRONT, BODY = TEXT.removeprefix("---\n").split("\n---\n", 1)
FIELDS = dict(line.split(": ", 1) for line in FRONT.splitlines())
REFERENCES = ("brief", "craft-floor", "anti-tells", "pen", "check")


def section(title: str) -> str:
    """The body of a `## title` section."""
    start = BODY.index(f"\n## {title}\n") + len(f"\n## {title}\n")
    end = BODY.find("\n## ", start)
    return BODY[start : end if end != -1 else len(BODY)]


def test_the_frontmatter():
    assert TEXT.startswith("---\n")
    assert list(FIELDS) == ["name", "description", "license", "compatibility"]
    name = FIELDS["name"]
    assert name == "keyline" == SKILL.name
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) and len(name) <= 64
    assert 0 < len(FIELDS["description"]) <= 200
    assert "deck" in FIELDS["description"] and "Use to" in FIELDS["description"]
    assert FIELDS["license"] == "Apache-2.0"
    compatibility = FIELDS["compatibility"]
    assert len(compatibility) <= 500
    for word in ("Python 3.11", "lxml", "Pillow", "python-pptx", "LibreOffice", "OfficeCLI"):
        assert word in compatibility, word
    assert "optional" in compatibility


def test_the_body_is_short_and_inert():
    lines = BODY.strip("\n").splitlines()
    assert len(lines) <= 200, len(lines)
    assert "${" not in BODY and "!`" not in BODY
    for token in re.split(r"[\s`\"'()|,;]+", BODY):  # "<skill folder>/scripts" is relative
        absolute = re.match(r"(/[A-Za-z0-9_.-]|~/|[A-Za-z]:[\\/])", token)
        assert not absolute, f"an absolute path: {token}"


def test_the_stance_is_at_most_five_lines():
    stance = [line for line in section("Stance").splitlines() if line.strip()]
    assert 1 <= len(stance) <= 5


def test_it_says_how_to_find_the_skill_folder():
    where = section("Where things are")
    assert "the folder that holds this" in where
    for surface in ("Claude Code", "claude.ai", "Claude desktop"):
        assert surface in where, surface
    assert "scripts/kl.py" in where
    assert set(re.findall(r"`references/([a-z-]+)\.md`", BODY)) == set(REFERENCES)


def test_every_doctor_token_has_an_action():
    setup = section("Setup")
    assert "kl.py doctor" in setup
    source = (ROOT / "src" / "keyline" / "doctor.py").read_text(encoding="utf-8")
    tokens = set(re.findall(r'"([A-Z]+(?:_[A-Z]+)+)"', source))
    assert len(tokens) == 18 and {"PPTX_OK", "NO_PPTX", "FONT_SUBSTITUTED"} <= tokens
    rows = [line for line in setup.splitlines() if line.startswith("| `")]
    documented = {
        t for row in rows for t in re.findall(r"`([A-Z]+(?:_[A-Z]+)+)`", row.split("|")[1])
    }
    assert documented == tokens
    for row in rows:
        assert row.split("|")[2].strip(), row  # an action, even if it is "Nothing."


def test_without_python_pptx_it_routes_to_checking():
    (row,) = [line for line in section("Setup").splitlines() if "`NO_PPTX`" in line]
    assert "python-pptx==1.0.2" in row and "route 2" in row and "say why" in row
    assert "no network" in row


def test_the_three_routes():
    routes = re.findall(r"^\d\. \*\*(.+?)\.\*\*", section("Routes"), re.MULTILINE)
    assert routes == ["New deck", "Check a deck", "Revise"]
    assert "kl.py check" in section("Routes")


def test_the_loop_has_the_voice_step_as_its_own_step():
    steps = re.findall(r"^(\d+)\. \*\*(.+?)\.\*\*", section("The loop"), re.MULTILINE)
    names = [name for _n, name in steps]
    assert [int(n) for n, _name in steps] == list(range(1, len(steps) + 1))
    assert names == [
        "Mode", "Evidence", "Brief", "Voice", "Spine", "Approval", "Build", "Check", "Look",
        "Fix once", "Report",
    ]  # fmt: skip
    loop = section("The loop")
    voice = loop[loop.index("4. **Voice.**") : loop.index("5. **Spine.**")]
    assert "own_world" in voice and "[voice.why]" in voice
    assert "coverage table" in voice and "references/brief.md" in voice
    assert "fallbacks" in voice and all(v in voice for v in ("neutral", "night", "field"))
    for command in ("kl.py brief", "kl.py run", "kl.py check"):
        assert command in loop, command
    # headlines are checked against their titles before the user sees the spine
    spine = loop[loop.index("5. **Spine.**") : loop.index("6. **Approval.**")]
    assert "every headline fits its title" in spine and "bare `deck.next()`" in spine
    assert "kl.py run" in spine and "names\n   the slide" in spine


def test_priority_and_report():
    priority = section("Priority")
    assert "DoesNotFit" in priority and "keyline pen: warning:" in priority
    assert "raw python-pptx or OfficeCLI" in priority
    report = section("Report")
    for item in ("exit code", "finding", "preview", "validated", "not embedded"):
        assert item in report, item
