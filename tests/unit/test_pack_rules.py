"""The four pack rules on synthetic decks (spec 002 §3.4, B-8.8): edges the fixtures do
not reach."""

from keyline.config import load as load_cfg
from keyline.context import LintContext
from keyline.lint import lint_deck
from keyline.model import Deck, Paragraph, Run, Shape, Slide
from keyline.packs import resolve

PACK = resolve("swiss")
NEUTRAL = PACK.voice("neutral")
CTX = LintContext(pack=PACK, voice=NEUTRAL)


def _text(sid, font="Arial", color="111111", size=2400, fill="none"):
    run = Run(text="Keepers wait", size=size, font=font, color=color)
    return Shape(sid, f"s{sid}", "sp", sid, fill=fill, paragraphs=[Paragraph((run,))])


def _deck(*slides):
    return Deck(
        12192000,
        6858000,
        slides=[
            Slide(i + 1, None, "solid:#F2F2F0", shapes=list(s), has_notes=True)
            for i, s in enumerate(slides)
        ],
    )


def _run(deck, ctx=CTX):
    return [f for f in lint_deck(deck, [], load_cfg(), ctx) if f.rule in RULES]


RULES = {"off-palette-color", "off-scale-size", "off-pack-font", "accent-overuse"}


def test_off_pack_font_lists_at_most_five_slides():
    deck = _deck(*[[_text(2, font="Calibri Light")] for _ in range(7)])
    (f,) = _run(deck)
    assert f.message == (
        "Calibri Light is not a font of swiss (voice neutral: Arial); slides 1, 2, 3, 4, 5 …"
    )
    assert f.measured == 7 and f.slide == 0


def test_hex_comparison_is_case_insensitive():
    assert _run(_deck([_text(2, color="cc3322")])) == []


def test_one_palette_finding_per_shape_first_value():
    shape = Shape(
        2,
        "two-offs",
        "sp",
        2,
        fill="solid:#1E2761",
        paragraphs=[Paragraph((Run("a", 2400, font="Arial", color="333333"),))],
    )
    (f,) = _run(_deck([shape]))
    assert f.message == "#333333 is not in the swiss palette (voice neutral)"


def test_accent_elements_are_counted_once_per_shape():
    both = _text(2, color="CC3322", fill="solid:#CC3322")
    assert _run(_deck([both])) == []
    (f,) = _run(_deck([both, _text(3, color="E8422E")]))
    assert (f.rule, f.measured, f.threshold) == ("accent-overuse", 2, 1)


def test_pack_rules_need_both_system_and_voice():
    deck = _deck([_text(2, font="Georgia", color="333333", size=2000)])
    assert _run(deck, LintContext(pack=PACK)) == []
    assert {f.rule for f in _run(deck)} == {"off-palette-color", "off-scale-size", "off-pack-font"}


def test_off_pack_font_matches_exact_names():
    """Amendment B-11: casefold and whitespace collapse only; a style word is a new family.
    font-count keeps A-8, so it still counts "Arial Black" as Arial."""
    found = {
        f.message.split(" is not")[0]
        for f in _run(
            _deck(
                [_text(2, font="Arial Black")],
                [_text(3, font="  ARIAL  ")],
                [_text(4, font="Arial Narrow")],
            )
        )
    }
    assert found == {"Arial Black", "Arial Narrow"}
    from keyline.rules.font_count import family as a8_family

    assert a8_family("Arial Black") == a8_family("Arial Narrow") == "arial"
