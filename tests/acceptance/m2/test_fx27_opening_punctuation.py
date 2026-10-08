"""Audit 06 FX-27 (amendment B-25 item 5, UAX #14 LB14): a piece that ends in an opening
punctuation mark (class OP: category Ps, and the inverted ! and ?) joins the next piece,
even across a space; the fullwidth closers ！ ？ ， 。 」 ） join the no-break-before list
(their LibreOffice check is test_fx17_line_breaks.py's). Before the fix the pen accepted a
headline as 2 lines that LibreOffice set in 3, clipping a bottom-anchored title at the
slide's top edge. Repro: evidence/audit06-repros/t_break.py. Characters as code points."""

import random

import pytest

from keyline.fit import WRAP_MARGIN, width, wrap
from keyline.fit.text import FULLWIDTH_CLOSERS, NO_BREAK_BEFORE, break_units, opens
from keyline.packs import resolve
from tests.acceptance.m2 import _lo

pytest.importorskip("pptx")

from keyline.pen import Deck

OPENERS = "([{" + "".join(map(chr, (0xA1, 0xBF, 0x201E, 0x201A)))  # all in the twins
WORDS = [
    *("plan", "build", "ship", "measure", "learn", "repeat", "grid", "rule", "column"),
    *("margin", "gutter", "rhythm", "type", "scale", "voice", "paper", "ink", "signal"),
]


def test_openers_join_the_next_piece():
    for ch in OPENERS + chr(0x2045) + chr(0xFF08):
        assert opens(ch), hex(ord(ch))
        assert break_units(f"see {ch} the note") == ["see", f"{ch} the", "note"]
    for ch in ")" + chr(0xAB) + chr(0x201C) + "a":  # closers and quotation marks do not open
        assert not opens(ch)
    assert set(FULLWIDTH_CLOSERS) <= set(NO_BREAK_BEFORE)
    assert break_units(f"done {chr(0xFF01)} next") == [f"done {chr(0xFF01)}", "next"]


def case(setting, box, ch, seed, space_fits):
    """A first line that holds "<words> <ch>" at the estimator's margin, followed by a word
    that cannot join it even at 1.01 x the box. With `space_fits`, the space after ch
    still fits at 1.003 x (LibreOffice's widest); without, not even at 0.998 x."""
    room = box * WRAP_MARGIN
    rng = random.Random(seed)
    for _ in range(100000):
        ws = [rng.choice(WORDS) for _ in range(20)]
        k = 1
        while k < len(ws) and width(setting, " ".join(ws[: k + 1]) + f" {ch}") <= room:
            k += 1
        first, after = " ".join(ws[:k]), ws[k]
        if width(setting, f"{first} {ch} {after}") <= box * 101 / 100:
            continue
        with_space = width(setting, f"{first} {ch} ")
        if (space_fits and with_space * 1003 / 1000 <= box) or (
            not space_fits and with_space * 998 / 1000 > box
        ):
            return first, after
    raise AssertionError(f"no case for {ch!r}")


@_lo.needs_lo("Arial")
@pytest.mark.parametrize("space_fits", [True, False], ids=["space-fits", "no-room"])
def test_libreoffice_never_sets_more_lines_than_the_estimator(space_fits, tmp_path):
    """The estimator carries each opener down with the next word: 2 lines. LibreOffice
    sets no more. With room for the space after the opener it keeps it with the next word
    too; without that room it leaves it at the end of the first line."""
    pack = resolve("swiss")
    deck = Deck(pack="swiss", mode="presented", voice="neutral")
    setting = deck._setting(pack.styles["presented"]["headline"])
    x0, _y0, x1, _y1 = _lo.region_pt(pack, "keyline:evidence", "title")
    box = x1 - x0
    for i, ch in enumerate(OPENERS):
        first, after = case(setting, box, ch, i, space_fits)
        text = f"{first} {ch} {after} end"
        assert wrap(setting, text, box) == [first, f"{ch} {after} end"]
        deck.add("evidence", text)
    deck.save(str(tmp_path / "lb14.pptx"))
    pitch = float(setting.pitch)
    for ch, page in zip(OPENERS, _lo.chars(tmp_path / "lb14.pptx", tmp_path / "lo"), strict=True):
        glyphs = [c for c in page if c[0].strip()]
        top = glyphs[0][2]
        line = lambda c, top=top: round((c[2] - top) / pitch)  # noqa: E731
        assert max(line(c) for c in glyphs) + 1 <= 2, f"LibreOffice set 3 lines for {ch!r}"
        at = next(i for i, c in enumerate(glyphs) if c[0] == ch)
        kept = line(glyphs[at]) == line(glyphs[at + 1])
        assert kept == space_fits, (ch, "kept" if kept else "broke after")
