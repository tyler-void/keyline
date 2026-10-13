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
SPEC = (ROOT / "specs" / "002-skill-pack" / "spec.md").read_text(encoding="utf-8")
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


# -- craft-floor.md (T-37) --------------------------------------------------------------


def test_craft_floor_items_are_backed():
    """Only items backed by a rule, the pen or the brief: every item names its rule, or
    the pen. The type scale, the budgets and the roles are generated."""
    text = read("craft-floor.md")
    items = re.findall(r"^- .*(?:\n  .*)*", text, re.MULTILINE)
    assert len(items) >= 18
    for item in items:
        assert ANCHOR.search(item) or "pen" in item or "DoesNotFit" in item, item
    for table in ("type-scale", "budgets", "roles"):
        assert f"<!-- gen:begin {table} -->" in text, table
    for rule in ("voice-contrast", "voice-claude-look", "voice-why"):  # B-8.15
        assert f"<!-- rule:{rule} -->" in text, rule
    anchored = set(ANCHOR.findall(text))
    assert len(anchored) >= 25 and anchored <= set(RULES)
    assert "Read this right before every build" in text


def test_craft_floor_leaves_out_only_what_a_build_cannot_cause():
    """Of the rules at warning or error level, craft-floor.md leaves out only the one a
    build's content cannot cause: a schema error in the file, which `check.md` covers."""
    anchored = set(ANCHOR.findall(read("craft-floor.md")))
    assert set(GATED) - anchored == {"ooxml-invalid"}


# -- anti-tells.md (T-38) ---------------------------------------------------------------


def backlog_ids() -> set[str]:
    """The ids that spec §13 and B-8.16 list as backlog."""
    start = SPEC.index("\n## 13. Backlog created by this spec\n")
    listed = SPEC[start : SPEC.index("\n## Appendix A", start)]
    b816 = SPEC[SPEC.index("  16. **Backlog** (for spec 003") :][:600]
    return set(re.findall(r"`([a-z]+(?:-[a-z]+)+)`", listed + b816))


def anti_tell_rows() -> dict[str, list[str]]:
    """id -> [tell, enforcement, Swiss policy]."""
    rows = {}
    for line in read("anti-tells.md").splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) == 6 and cells[1] != "id" and re.fullmatch(r"[a-z]+(?:-[a-z]+)*", cells[1]):
            assert cells[1] not in rows, f"{cells[1]} is listed twice"
            rows[cells[1]] = cells[2:5]
    return rows


def test_anti_tells_holds_every_seed_row():
    """Rows may be added, never dropped: every id of Appendix A is there."""
    appendix = SPEC[SPEC.index("\n## Appendix A") : SPEC.index("\n## Lessons to append")]
    seed = re.findall(r"^\| ([a-z]+(?:-[a-z]+)*) \|", appendix, re.MULTILINE)
    seed.remove("id")  # the table's header
    assert len(seed) == 27 and "equal-cards" in seed and "mood-direction" in seed
    rows = anti_tell_rows()
    assert set(seed) <= set(rows), sorted(set(seed) - set(rows))
    assert all(what and policy for what, _enforcement, policy in rows.values())


def test_every_enforcement_is_valid():
    """`rule:<id>` and `brief:<id>` name registry ids, `backlog:<id>` names an id of §13,
    and `pen` needs none."""
    backlog = backlog_ids()
    assert {"eyebrow-caps", "centered-body", "language-tells", "diversity-fingerprint"} <= backlog
    for tell, (_what, enforcement, _policy) in anti_tell_rows().items():
        kinds = re.findall(r"`(rule|brief|backlog):([a-z0-9-]+)`", enforcement)
        assert kinds or "`pen`" in enforcement, f"{tell}: no enforcement"
        leftover = re.sub(r"`(?:rule|brief|backlog):[a-z0-9-]+`|`pen`|[;\s]", "", enforcement)
        assert leftover == "", f"{tell}: {enforcement}"
        for kind, rule in kinds:
            if kind == "backlog":
                assert rule in backlog, f"{tell}: backlog:{rule} is not in §13"
            else:
                assert rule in RULES, f"{tell}: {kind}:{rule} is not a registry id"
                from_brief = RULES[rule].requires == "brief"
                assert from_brief == (kind == "brief"), f"{tell}: {kind}:{rule}"


def test_the_one_look_row_and_the_sources():
    look = anti_tell_rows()["one-look-for-everything"][1]  # B-8.15
    assert "`brief:voice-why`" in look and "`backlog:diversity-fingerprint`" in look
    text = read("anti-tells.md")
    research = (ROOT / "docs" / "research.md").read_text(encoding="utf-8").replace("'", '"')
    cited = re.findall(r'"([^"]{30,})"', text.split("| id |")[0].replace("\n", " "))
    assert len(cited) == 3
    for heading in cited:
        assert heading.replace("'", '"') in research, heading


# -- brief.md (T-39) --------------------------------------------------------------------


def test_brief_md_covers_every_field():
    text = read("brief.md")
    fields = (
        "schema", "mode", "pack", "evidence", "audience", "decision", "thesis", "own_world",
        "motif", "role", "headline", "reads", "notes", "name", "fictional", "disclosure", "id",
        "label", "source", "value", "series", "aliases", "display", "text", "paper", "ink",
        "muted", "hairline", "accent", "accent_on_ink",
    )  # fmt: skip
    for field in fields:
        assert re.search(rf"(^|`|# ){field}(`| =)", text, re.MULTILINE), field
    roles = section(text, "The slides")
    for role in ("cover", "section", "statement", "evidence", "quote", "close"):
        assert f"| `{role}` |" in roles, role


def test_brief_md_gives_each_field_its_test():
    text = read("brief.md")
    direction = section(text, "The direction, field by field")
    for field in ("audience", "decision", "thesis", "own_world", "motif"):
        (row,) = [line for line in direction.splitlines() if line.startswith(f"| `{field}` |")]
        assert len(row.split("|")) == 5 and row.split("|")[3].strip(), field
    assert "If it reads like a mood or a topic, it is not a thesis yet." in direction
    assert "No adjectives about the deck" in direction  # own_world: nouns from the subject
    slides = section(text, "The slides")
    assert "The headline test" in slides and "has to tell the whole story" in slides
    for rule in ("brief-headline-long", "brief-reads", "unsourced-number", "brief-notes"):
        assert f"<!-- rule:{rule} -->" in slides, rule
    assert "Unknown keys are ignored" in text and "`[product.world]`" in text


def test_brief_md_examples_pass_keyline_brief(tmp_path):
    """The examples are keyline's own, and they are a valid brief with its evidence."""
    import tomllib

    from keyline.brief import findings, load

    blocks = re.findall(r"```toml\n(.*?)```", read("brief.md"), re.DOTALL)
    assert len(blocks) == 2
    evidence, brief = (tomllib.loads(block) for block in blocks)
    assert evidence["product"]["name"] == "Toolshed Commons" and len(evidence["evidence"]) == 2
    assert brief["evidence"] == ["product.toml", "deck.evidence.toml"]
    (tmp_path / "product.toml").write_text(blocks[0], encoding="utf-8")
    (tmp_path / "deck.evidence.toml").write_text("schema = 1\n", encoding="utf-8")
    (tmp_path / "deck.brief.toml").write_text(blocks[1], encoding="utf-8")
    loaded = load(tmp_path / "deck.brief.toml")
    assert [s.role for s in loaded.slides] == ["cover", "evidence"]
    assert loaded.voice.font("display") == "Georgia" and findings(loaded) == []
