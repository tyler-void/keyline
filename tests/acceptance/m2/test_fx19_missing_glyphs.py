"""Audit 05 FX-19 (amendment B-22 item 6): a character the voice's twin lacks counts as
max(the twin's maximum advance, `missing_glyph_em`), measured on LibreOffice (CJK, emoji,
Thai; tools/measure_lo.py). Liberation Mono's maximum advance is 0.6 em, and before the
fix 330 CJK words in a Courier New voice were accepted and ended 82 pt below the region.
Repro: evidence/audit05-repros/attack_fit2.py. Characters are written as code points."""

from fractions import Fraction

import pytest

from keyline.config import load as load_config
from keyline.fit import WEIGHTS, Setting, load_table, width
from keyline.packs import resolve
from tests.acceptance.m2 import _lo

pytest.importorskip("pptx")

from keyline.pen import Deck, DoesNotFit

FAMILIES = [f for f, _twin in load_config().portable_fonts]
CJK = chr(0x6F22) + chr(0x5B57)
EMOJI = chr(0x1F600)
THAI = "".join(map(chr, (0x0E2A, 0x0E27, 0x0E31, 0x0E2A, 0x0E14, 0x0E35)))


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("weight", WEIGHTS)
def test_a_missing_character_counts_as_missing_glyph_em_at_least(family, weight):
    t = load_table(family, weight)
    em = load_config().missing_glyph_em
    assert t.missing_advance == max(Fraction(t.max_advance), em * t.units_per_em)
    assert t.advance(CJK[0]) == t.missing_advance >= em * t.units_per_em
    assert t.advance("H") == t.advances[ord("H")]


def test_the_monospace_twin_no_longer_counts_cjk_at_0_6_em():
    mono = load_table("Courier New", "regular")
    assert Fraction(mono.max_advance, mono.units_per_em) < Fraction(61, 100)
    setting = Setting("Courier New", "regular", Fraction(13))
    assert width(setting, CJK * 2) == 4 * load_config().missing_glyph_em * 13


def longest(accepts, unit, limit=600):
    """The longest " ".join([unit] * n) that `accepts` takes (it is monotonic in n)."""
    lo, hi = 0, 1
    while hi <= limit and accepts(" ".join([unit] * hi)):
        lo, hi = hi, hi * 2
    hi = min(hi, limit + 1)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if accepts(" ".join([unit] * mid)) else (lo, mid)
    assert lo > 0
    return " ".join([unit] * lo)


def headline_accepts(deck):
    def accepts(text):
        try:
            deck.add("evidence", text)
        except DoesNotFit:
            return False
        deck._slides.pop()
        return True

    return accepts


def text_accepts(deck):
    def accepts(text):
        trial = deck.add("evidence", "Scratch")
        try:
            trial.text(text)
        except DoesNotFit:
            return False
        finally:
            deck._slides.pop()
        return True

    return accepts


CASES = [  # name, mode, family, headline or text, unit
    ("courier-cjk-body", "read", "Courier New", "text", CJK * 2),
    ("courier-emoji-body", "read", "Courier New", "text", "ok" + EMOJI * 2),
    ("arial-cjk-headline", "presented", "Arial", "headline", CJK * 2),
    ("arial-thai-headline", "presented", "Arial", "headline", THAI),
    ("arial-emoji-headline", "presented", "Arial", "headline", "ok" + EMOJI * 3),
    ("arial-mixed-body", "read", "Arial", "text", "a" + "a".join(CJK * 2)),
    ("calibri-cjk-body", "read", "Calibri", "text", CJK * 2),
    ("georgia-cjk-body", "presented", "Georgia", "text", CJK * 2),
]


@_lo.needs_lo("Arial", "Courier New", "Calibri", "Georgia")
def test_the_longest_texts_the_pen_accepts_stay_in_their_region(tmp_path):
    """attack_fit2.py's cases, and Latin and CJK alternating (the widest measured cost)."""
    pack = resolve("swiss")
    built = []
    for name, mode, family, kind, unit in CASES:
        voice = "neutral" if family == "Arial" else _lo.voice_file(tmp_path, family)
        deck = Deck(pack="swiss", mode=mode, voice=voice)
        if kind == "headline":
            deck.add("evidence", longest(headline_accepts(deck), unit))
            region = _lo.region_pt(pack, "keyline:evidence", "title")
        else:
            deck.add("evidence", "Text").text(longest(text_accepts(deck), unit))
            region = _lo.region_pt(pack, "keyline:evidence", "main")
        path = tmp_path / f"{name}.pptx"
        deck.save(str(path))
        built.append((name, path, kind, region))
    for name, path, kind, region in built:
        (page,) = _lo.chars(path, tmp_path / f"lo-{name}")
        mine = [c for c in page if region[1] - 1.5 <= c[2] and c[4] >= region[1]]
        if kind == "headline":
            mine = [c for c in page if c[2] < region[3] + 60]  # the title, and any spill
        assert mine, name
        assert max(c[4] for c in mine) <= region[3] + 1.5, name  # 2 px at 1280 px
        assert max(c[3] for c in mine) <= region[2] + 1.5, name
