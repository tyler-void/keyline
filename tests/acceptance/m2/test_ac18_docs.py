"""Spec 002 AC-18 (§8.3; tasks T-36 … T-42; audit 07 §4.3 and §4.9): the skill's docs.
Every `<!-- rule:ID -->` anchor resolves to a registry id; the generated tables are
current (`tools/gen_docs.py --check`); each reference stays under its line cap;
`anti-tells.md` holds every Appendix A row with a valid enforcement; `pen.md` documents
every public verb; `check.md` has a recipe, under its own heading, for every rule at
warning or error level, a section on what the pen reports, and the known limits.

The test grows with the docs: this skeleton (T-36) applies to whichever references
exist, and each doc task adds the checks of its own file."""

import importlib.util
import re
import sys

from keyline.registry import all_rules
from keyline.rules import load_all
from tests.conftest import ROOT

SKILL = ROOT / "skill" / "keyline"
REFERENCES = SKILL / "references"
# audit 07 §4.9: craft-floor.md is read before every build, so it has the tightest cap
# of the three working references
LINE_CAPS = {
    "craft-floor.md": 110,
    "anti-tells.md": 60,
    "brief.md": 210,
    "pen.md": 220,
    "check.md": 290,
}
load_all()
RULES = {r.id: r for r in all_rules()}
GATED = sorted(i for i, r in RULES.items() if r.severity in ("warning", "error"))
ANCHOR = re.compile(r"<!-- rule:([a-z0-9-]+) -->")
WARNING_PREFIX = "keyline pen: warning:"
PATH = re.compile(r"(/[A-Za-z0-9_.-]|~/|[A-Za-z]:[\\/])")


def read(name: str) -> str:
    return (REFERENCES / name).read_text(encoding="utf-8")


def docs() -> dict[str, str]:
    found = {"SKILL.md": (SKILL / "SKILL.md").read_text(encoding="utf-8")}
    if REFERENCES.is_dir():
        found.update({p.name: p.read_text(encoding="utf-8") for p in sorted(REFERENCES.iterdir())})
    return found


def gen_docs():
    spec = importlib.util.spec_from_file_location("gen_docs", ROOT / "tools" / "gen_docs.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_docs"] = module
    spec.loader.exec_module(module)
    return module


def section(text: str, title: str, level: str = "##") -> str:
    """The body of a section, up to the next heading of its level."""
    start = text.index(f"\n{level} {title}\n") + len(f"\n{level} {title}\n")
    end = text.find(f"\n{level} ", start)
    return text[start : end if end != -1 else len(text)]


# -- every doc (the skeleton, T-36) -------------------------------------------------------


def test_the_registry():
    assert len(RULES) == 35 and len(GATED) == 31


def test_only_the_five_references_are_there():
    assert set(docs()) - {"SKILL.md"} <= set(LINE_CAPS)


def test_every_rule_anchor_resolves():
    for name, text in docs().items():
        for rule in ANCHOR.findall(text):
            assert rule in RULES, f"{name}: <!-- rule:{rule} --> is not a registry id"
        assert "<!-- rule:" not in ANCHOR.sub("", text), f"{name}: a malformed rule anchor"


def test_every_reference_stays_under_its_line_cap():
    for name, text in docs().items():
        if name != "SKILL.md":  # AC-17 caps SKILL.md
            lines = len(text.splitlines())
            assert lines <= LINE_CAPS[name], f"{name}: {lines} lines, cap {LINE_CAPS[name]}"
    working = [LINE_CAPS[n] for n in ("brief.md", "pen.md", "check.md")]
    assert LINE_CAPS["craft-floor.md"] < min(working)


def test_the_generated_tables_are_current(capsys):
    assert gen_docs().main(["--check"]) == 0, capsys.readouterr().err
    for name, text in docs().items():
        assert text.count("<!-- gen:begin ") == text.count("<!-- gen:end -->"), name


def test_no_substitution_or_absolute_path_in_any_doc():
    for name, text in docs().items():
        assert "${" not in text and "!`" not in text, name
        for token in re.split(r"[\s`\"'()|,;]+", text):
            assert not PATH.match(token), f"{name}: an absolute path: {token}"


# -- the voice step, in brief.md and SKILL.md (T-35) ------------------------------------


def test_the_docs_use_the_pens_warning_prefix(tmp_path, capsys):
    """Plan Q-54 as ruled: the prefix the skill reacts to is the one the pen writes."""
    import pytest

    pytest.importorskip("pptx")
    from keyline.pen import Deck, _api

    assert _api.WARNING_PREFIX.rstrip(" ") == WARNING_PREFIX
    assert _api.WARNING_PREFIX.endswith(": ")
    deck = Deck(pack="swiss", mode="presented", voice="neutral")
    deck.add("statement", "Caf" + chr(0xE9) + " " + chr(0x6F22))  # a character outside the set
    deck.save(str(tmp_path / "deck.pptx"))
    (line,) = capsys.readouterr().err.splitlines()
    assert line.startswith(f"{WARNING_PREFIX} the fit does not cover some characters")
    found = docs()
    for name in ("SKILL.md", "brief.md", "pen.md", "check.md"):
        if name in found:
            assert f"`{WARNING_PREFIX}`" in found[name], name


def test_brief_md_has_the_voice_step():
    """B-8.14, B-8.15 and plan Q-54 as ruled: the voice comes from own_world with a why
    line per role; the family comes from the generated coverage table, before building;
    the stock voices are fallbacks; and the pen's warning is the backstop."""
    voice = section(read("brief.md") + "\n## ", "The voice")
    assert "own_world" in voice and "[product.world]" in voice and "`why`" in voice
    for role in ("paper", "ink", "muted", "hairline", "accent", "accent_on_ink"):
        assert f"| `{role}` |" in voice, role
    for rule in ("voice-why", "voice-contrast", "voice-claude-look"):
        assert f"<!-- rule:{rule} -->" in voice, rule
    assert "Pick before you build" in voice
    coverage = voice[voice.index("<!-- gen:begin coverage -->") : voice.index("<!-- gen:end -->")]
    assert "| Cambria | Caladea |" in coverage and "Every Vietnamese letter:" in coverage
    assert "fallbacks" in voice and all(f'"{v}"' in voice for v in ("neutral", "night", "field"))
    assert f"`{WARNING_PREFIX}`" in voice and "backstop" in voice
    skill = docs()["SKILL.md"]
    assert "4. **Voice.**" in skill and "coverage table in `references/brief.md`" in skill
