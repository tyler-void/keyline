"""Deck vs brief (spec 002 §4.5, T-13): edges the AC-8 drift decks do not reach."""

from keyline.brief import load
from keyline.config import load as load_cfg
from keyline.context import LintContext
from keyline.lint import lint_deck
from keyline.model import Deck, Paragraph, Run, Shape, Slide
from tests.conftest import FIXTURES

BRIEF = load(FIXTURES / "briefs/drift/base.brief.toml")
CTX = LintContext(BRIEF.pack, BRIEF.voice, BRIEF, BRIEF.evidence)
IDS = {
    "brief-slide-count",
    "brief-role",
    "brief-headline",
    "unsourced-number",
    "source-missing",
    "fiction-undisclosed",
}
DISCLOSURE = BRIEF.evidence.product.disclosure


def _sp(sid, *texts, ph_type=None, kind="sp"):
    paras = [Paragraph((Run(t, 2400, font="Arial", color="111111"),)) for t in texts]
    return Shape(sid, f"s{sid}", kind, sid, ph_type=ph_type, paragraphs=paras)


def _slide(i, role, title, *more):
    return Slide(i, None, "solid:#F2F2F0", [_sp(2, title, ph_type="title"), *more], True, role)


def _find(slides, ctx=CTX):
    deck = Deck(12192000, 6858000, slides=slides)
    return [
        (f.rule, f.slide, f.message) for f in lint_deck(deck, [], load_cfg(), ctx) if f.rule in IDS
    ]


def test_slide_findings_pair_over_the_common_prefix():
    got = _find([_slide(1, "cover", "BonsaiHub", _sp(3, DISCLOSURE)), _slide(2, None, "Other")])
    assert got == [
        ("brief-slide-count", 0, "deck has 2 slides, brief has 5"),
        (
            "brief-headline",
            2,
            "title is 'Other'; brief says 'Every tree deserves a patient keeper'",
        ),
        ("brief-role", 2, "slide has no role; brief says statement"),
    ]


def test_headlines_compare_after_whitespace_collapse_but_case_sensitively():
    spaced = "Every tree deserves a  patient\nkeeper"
    ok = _find(
        [_slide(1, "cover", " BonsaiHub ", _sp(3, DISCLOSURE)), _slide(2, "statement", spaced)]
    )
    assert [g for g in ok if g[0] == "brief-headline"] == []
    shouted = _find([_slide(1, "cover", "BONSAIHUB", _sp(3, DISCLOSURE))])
    assert ("brief-headline", 1, "title is 'BONSAIHUB'; brief says 'BonsaiHub'") in shouted


def _evidence_deck(*shapes):
    return [
        _slide(1, "cover", "BonsaiHub", _sp(9, DISCLOSURE)),
        _slide(2, "statement", "Every tree deserves a patient keeper"),
        _slide(3, "evidence", "The waitlist grew faster than keepers could sign up", *shapes),
    ]


def test_unsourced_number_once_per_token_and_aliases_count():
    got = _find(_evidence_deck(_sp(3, "3,180 keepers and 3,180 more"), _sp(4, "12,400 trees")))
    unsourced = [g for g in got if g[0] == "unsourced-number"]
    assert unsourced == [
        ("unsourced-number", 3, "3,180 is not in this slide's evidence (waitlist_trees)")
    ]


def test_source_missing_on_a_chart_without_numbers():
    chart = Shape(5, "chart", "graphicFrame:chart", 5)
    got = _find(_evidence_deck(chart))
    assert (
        "source-missing",
        3,
        "slide shows a chart or table from its evidence but has no source line",
    ) in got
    sourced = _find(_evidence_deck(chart, _sp(6, "Source: BonsaiHub waitlist")))
    assert [g for g in sourced if g[0] == "source-missing"] == []


def test_disclosure_on_the_first_slide_counts_and_whitespace_collapses():
    spread = DISCLOSURE.replace(" Its", "\n  Its")
    got = _find([_slide(1, "cover", "BonsaiHub", _sp(3, *spread.split("\n")))])
    assert [g for g in got if g[0] == "fiction-undisclosed"] == []
    got = _find([_slide(1, "cover", "BonsaiHub")])
    assert (
        "fiction-undisclosed",
        0,
        "the fictional-product disclosure is on neither the first nor the last slide",
    ) in got


def test_brief_rules_need_a_brief():
    got = _find([_slide(1, None, "Anything")], LintContext(BRIEF.pack, BRIEF.voice))
    assert got == []
