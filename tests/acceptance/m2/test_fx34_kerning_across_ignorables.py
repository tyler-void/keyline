"""Audit 07 FX-34 (amendment B-27 item 4): kerning pairs are looked up across
default-ignorable code points. Carlito (Calibri) has U+200C, U+200D and U+200E at zero
advance; HarfBuzz skips a joiner between V and ĩ and LibreOffice applies the pair, which
the estimator dropped: a presented body estimated at 8 lines was set in 9, +23.8 px below
its region. LRM does split the pair in LibreOffice; counting it there too only adds width.
Repro: evidence/audit07-repros/f3_ignorable.py. Characters as code points."""

from fractions import Fraction as F

import pytest

from keyline.fit import Setting, load_table, width
from keyline.fit.text import ignorable
from keyline.packs import resolve
from tests.acceptance.m2 import _lo

pytest.importorskip("pptx")

from keyline.pen import Deck, DoesNotFit

I_TILDE = chr(0x129)
JOINERS = {"none": "", "ZWNJ": chr(0x200C), "ZWJ": chr(0x200D), "LRM": chr(0x200E)}


def words(j):
    """f3_ignorable.py's two words, every letter followed by the joiner."""
    v, t = f"V{j}{I_TILDE}", f"T{j}{I_TILDE}"
    return [j.join([v, t, v]), j.join([t, v, t])]


def test_the_default_ignorables():
    for cp in (0x200C, 0x200D, 0x200E, 0x200F, 0x2061, 0xFE0F, 0x034F, 0x00AD, 0xE0100):
        assert ignorable(chr(cp)), hex(cp)
    for ch in "V" + I_TILDE + " " + chr(0xA0) + chr(0x2019):
        assert not ignorable(ch), hex(ord(ch))


@pytest.mark.parametrize("name", [n for n in JOINERS if n != "none"])
def test_a_joiner_does_not_split_a_pair(name):
    j = JOINERS[name]
    carlito = load_table("Calibri", "regular")
    assert carlito.advances[ord(j)] == 0 and carlito.kern[ord("V"), 0x129] == 130
    s = Setting("Calibri", "regular", F(24))
    assert width(s, f"V{j}{I_TILDE}") == width(s, f"V{I_TILDE}")
    assert width(s, f"V{j}{j}{I_TILDE}") == width(s, f"V{I_TILDE}")
    assert width(s, " ".join(words(j))) == width(s, " ".join(words("")))


def longest(accepts, units, limit=600):
    best = None
    for n in range(1, limit):
        text = " ".join(units[i % len(units)] for i in range(n))
        if not accepts(text):
            return best
        best = text
    raise AssertionError("no text was refused")


@_lo.needs_lo("Calibri")
@pytest.mark.parametrize("mode", ["presented", "read"])
def test_the_longest_joined_texts_stay_in_their_region(mode, tmp_path):
    """f3_ignorable.py: per joiner, the longest body and lede the pen accepts, word by
    word. Every glyph ends within 1.5 pt (2 px at 1280 px) of its region's bottom."""
    pack = resolve("swiss")
    voice = _lo.voice_file(tmp_path, "Calibri")
    cases = []
    for name, j in JOINERS.items():
        for role, style in (("evidence", "body"), ("statement", "lede")):

            def accepts(text, role=role, style=style):
                try:
                    Deck(pack="swiss", mode=mode, voice=voice).add(role, "x").text(
                        text, style=style
                    )
                except DoesNotFit:
                    return False
                return True

            cases.append((name, role, style, longest(accepts, words(j))))
    d = Deck(pack="swiss", mode=mode, voice=voice)
    for _name, role, style, text in cases:
        d.add(role, "x").text(text, style=style)
    path = tmp_path / "joined.pptx"
    d.save(str(path))
    pages = _lo.chars(path, tmp_path / "lo")
    for (name, role, style, _text), page in zip(cases, pages, strict=True):
        box = _lo.region_pt(pack, pack.roles[role].layouts[0], "main")
        body = [c for c in page if c[2] >= box[1] - 1.5]
        assert body and max(c[4] for c in body) <= box[3] + 1.5, (mode, name, role, style)
