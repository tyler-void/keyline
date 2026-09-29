"""Spec 002 §6.1–§6.2 and AC-10 (task T-24): text, bullets, source, note, notes and
attribution fill one named region each, with styles and components the role allows,
caption caps, and the fit check."""

import pytest

pytest.importorskip("pptx")

from keyline.brief import load as load_brief
from keyline.context import LintContext
from keyline.lint import lint_path
from keyline.ooxml.adapter import load_deck
from keyline.pen import Deck, DoesNotFit, PenError
from tests.conftest import FIXTURES

BRIEF = FIXTURES / "briefs/drift/base.brief.toml"
EVIDENCE = str(FIXTURES / "briefs/evidence.toml")


def deck(mode="presented"):
    return Deck(pack="swiss", mode=mode, voice="neutral", evidence=EVIDENCE)


def test_a_pen_built_deck_lints_clean_against_its_brief(tmp_path):
    d = Deck.from_brief(str(BRIEF))
    d.next().text("A slow dating app for trees and their keepers", style="lede")
    d.next()
    d.next().text("12,400 trees are waiting for a keeper").source()
    d.next().text("71% of keepers are still active after 90 days").source()
    d.next().text("Join the waitlist as a keeper this season", style="lede").note()
    out = tmp_path / "base.pptx"
    d.save(str(out), author="Tyler")
    brief = load_brief(BRIEF)
    ctx = LintContext(brief.pack, brief.voice, brief, brief.evidence)
    result = lint_path(out, brief.mode, ctx)
    assert result.findings == [] and result.exit_code == 0


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda s: s.text("Words", style="#CC3322"), "looks like a raw value"),
        (lambda s: s.text("Words", style="caption"), "unknown style 'caption'"),
        (lambda s: s.text("Words", region="2cm"), "looks like a raw value"),
        (lambda s: s.text("Words", region="aside"), "has no region 'aside'"),
        (lambda s: s.text("Words", style="lede"), "style 'lede' is not allowed for text"),
        (lambda s: s.attribution("Ada"), "does not allow attribution"),
        (lambda s: s.text("One").text("Two"), "region 'main' already holds a component"),
        (lambda s: s.bullets(["a", "b", "c", "d", "e"]), "5 bullets; at most 4"),
        (lambda s: s.note(), "no disclosure to write here"),
    ],
)
def test_pen_errors_on_an_evidence_slide(call, message):
    s = deck().add("evidence", "Most returned tools need a repair")
    with pytest.raises(PenError, match=message):
        call(s)


def test_read_mode_allows_lede_on_evidence():
    deck("read").add("evidence", "Most returned tools need a repair").text("Lede", style="lede")


def test_components_the_role_does_not_allow():
    with pytest.raises(PenError, match="role cover does not allow bullets"):
        deck().add("cover", "Toolshed Commons").bullets(["a"])
    with pytest.raises(PenError, match="role section does not allow source"):
        deck().add("section", "What the bench does").source("Log")


def test_a_six_word_attribution_is_refused():
    s = deck().add("quote", "I came to borrow a saw", notes="n")
    with pytest.raises(PenError, match="attribution has 6 words; at most 5"):
        s.attribution("A member of the tool library")
    s.attribution("A member, spring 2026")


def test_footer_holds_the_source_then_the_note(tmp_path):
    d = deck()
    d.add("close", "Build the second bench", notes="n").note().source("Return log, 2026")
    d.save(str(tmp_path / "f.pptx"))
    model, _ = load_deck(tmp_path / "f.pptx")
    (footer,) = [s for s in model.slides[0].shapes if s.name == "footer"]
    assert [p.text for p in footer.paragraphs] == [
        "Source: Return log, 2026",
        "Note: Toolshed Commons is fictional, and so is every number in this deck.",
    ]
    assert {r.size for r in footer.runs} == {1200}  # the source style


def test_note_gets_its_prefix_and_source_keeps_a_given_one(tmp_path):
    d = deck()
    s = d.add("statement", "Repairs bring members back", notes="n")
    s.note("figures are illustrative").source("Sources: two surveys")
    d.save(str(tmp_path / "n.pptx"))
    model, _ = load_deck(tmp_path / "n.pptx")
    (footer,) = [x for x in model.slides[0].shapes if x.name == "footer"]
    assert [p.text for p in footer.paragraphs] == [
        "Sources: two surveys",
        "Note: figures are illustrative",
    ]


def test_bullets_carry_the_marker_and_indent(tmp_path):
    d = deck()
    d.add("evidence", "What members ask for", notes="n").bullets(["Saws", "Clamps", "Advice"])
    d.save(str(tmp_path / "b.pptx"))
    model, _ = load_deck(tmp_path / "b.pptx")
    (main,) = [x for x in model.slides[0].shapes if x.name == "main"]
    assert [p.text for p in main.paragraphs] == ["Saws", "Clamps", "Advice"]
    assert {r.size for r in main.runs} == {2400}


def test_text_that_does_not_fit():
    s = deck().add("section", "What the bench does")
    with pytest.raises(DoesNotFit, match=r"^text needs \d+ lines, region holds 1"):
        s.text(
            "Part one of the talk, about benches, repairs, tags and the members who return",
            style="label",
        )
