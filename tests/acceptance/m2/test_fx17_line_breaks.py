"""Audit 05 FX-17 (amendment B-22 item 4): no line break before ) ] } , . : ; ! ? / %
U+2030 U+00BB U+201D U+2019, even after a space (UAX #14, LB13); the estimator keeps them
with the word before. LibreOffice is checked with each character: a headline whose first
line is full, followed by " <char> end", must carry that line's last word down with the
character. Repro: evidence/audit05-repros/attack_uax14.py."""

import random

import pytest

from keyline.fit import WRAP_MARGIN, width, wrap
from keyline.fit.text import FULLWIDTH_CLOSERS, NO_BREAK_BEFORE, break_units
from keyline.packs import resolve
from tests.acceptance.m2 import _lo

pytest.importorskip("pptx")

from keyline.pen import Deck, DoesNotFit

WORDS = [
    *("plan", "build", "ship", "measure", "learn", "repeat", "grid", "rule", "column"),
    *("margin", "gutter", "rhythm", "type", "scale", "voice", "paper", "ink", "signal"),
    *("red", "blue", "orders", "district", "minutes", "faster"),
]
LAYOUT = "keyline:evidence"


def headline_setting(deck):
    return deck._setting(deck._pack.styles["presented"][deck._pack.roles["evidence"].title])


def test_break_units_keep_closing_punctuation_with_the_word_before():
    assert break_units("plan / district , ship . done") == [
        "plan /",
        "district ,",
        "ship .",
        "done",
    ]
    assert break_units(") opens") == [")", "opens"]  # nothing before it to keep it with
    assert break_units("( opens") == ["( opens"]  # B-25 item 5: kept with what follows
    for ch in NO_BREAK_BEFORE:
        assert break_units(f"a {ch} b") == [f"a {ch}", "b"]


def test_no_line_starts_with_closing_punctuation():
    deck = Deck(pack="swiss", mode="presented", voice="neutral")
    setting = headline_setting(deck)
    rng = random.Random(7)
    for _ in range(300):
        ch = rng.choice(NO_BREAK_BEFORE)
        text = f" {ch} ".join(rng.choice(WORDS) for _ in range(rng.randint(4, 20)))
        for line in wrap(setting, text, 600):
            assert line[:1] not in NO_BREAK_BEFORE, (text, line)


# attack_uax14.py's search (seed 7, "/"), rerun with the wrap before this fix: each was
# accepted as 2 lines. On 26.8.0.3 LibreOffice set the second in 3 lines, 53 pt below
# the title region (report A2 fixes); the auditor saw the third set in 3 on 24.2.7.2.
AUDIT_HEADLINES = [
    "minutes / column / voice / ink / signal / paper / ink / rule / minutes / ink",
    "type / red / learn / blue / grid / minutes / red / rhythm / ship / district / grid",
    "plan / district / ship / minutes / signal / learn / learn / column / voice / red",
]


@pytest.mark.parametrize("text", AUDIT_HEADLINES)
def test_the_audit_headlines_are_refused(text):
    deck = Deck(pack="swiss", mode="presented", voice="neutral")
    with pytest.raises(DoesNotFit, match="headline needs 3 lines, region holds 2"):
        deck.add("evidence", text)


LB13 = ")]},.:;!?/" + FULLWIDTH_CLOSERS  # UAX #14 classes CL, CP, EX, IS and SY


def full_line_case(setting, box_pt, ch, seed, space_fits):
    """A headline whose first line is as full as the estimator allows, then " ch end";
    " ch" cannot fit on that line even at 1.01 x the box (LibreOffice's widest one-line
    threshold is 1.003 x the advance sum, B-21). With `space_fits`, the space after the
    line's last word still fits even at 1.003 x; without, it does not even at 0.998 x,
    LibreOffice's narrowest (B-21)."""
    room = box_pt * WRAP_MARGIN
    rng = random.Random(seed)
    for _ in range(50000):
        words = [rng.choice(WORDS) for _ in range(20)]
        k = 1
        while k < len(words) and width(setting, " ".join(words[: k + 1])) <= room:
            k += 1
        first = " ".join(words[:k])
        if width(setting, f"{first} {ch}") <= box_pt * 101 / 100:
            continue
        with_space = width(setting, f"{first} ")
        if space_fits and with_space * 1003 / 1000 <= box_pt:
            return first, f"{first} {ch} end"
        if not space_fits and with_space * 998 / 1000 > box_pt:
            return first, f"{first} {ch} end"
    raise AssertionError(f"no case found for {ch!r}")


@_lo.needs_lo("Arial")
@pytest.mark.parametrize("space_fits", [True, False], ids=["space-fits", "no-room"])
def test_libreoffice_never_sets_more_lines_than_the_estimator(space_fits, tmp_path):
    """For each character, a headline whose first line is full, then " <char> end". The
    estimator carries the last word down with the character: 2 lines. LibreOffice sets
    no more, whatever it does. With room for the space after the last word it keeps the
    ten UAX #14 LB13 characters with that word, as the estimator does (the audit's "/",
    attack_uax14.py), and breaks before % U+2030 U+00BB U+201D U+2019; without that room
    it breaks before all fifteen (tools/measure_lo.py prints the same table)."""
    pack = resolve("swiss")
    deck = Deck(pack="swiss", mode="presented", voice="neutral")
    setting = headline_setting(deck)
    x0, _y0, x1, _y1 = _lo.region_pt(pack, LAYOUT, "title")
    box_pt = x1 - x0
    cases = []
    for i, ch in enumerate(NO_BREAK_BEFORE):
        first, text = full_line_case(setting, box_pt, ch, i, space_fits)
        last_word = first.rsplit(" ", 1)[1]
        assert wrap(setting, text, box_pt) == [first.rsplit(" ", 1)[0], f"{last_word} {ch} end"]
        deck.add("evidence", text)
        cases.append((ch, last_word))
    deck.save(str(tmp_path / "lb13.pptx"))
    pages = _lo.chars(tmp_path / "lb13.pptx", tmp_path / "lo")
    pitch = float(setting.pitch)
    for (ch, last_word), page in zip(cases, pages, strict=True):
        glyphs = [c for c in page if c[0].strip()]
        top = glyphs[0][2]
        lines = {round((c[2] - top) / pitch) for c in glyphs}
        assert max(lines) + 1 <= 2, f"LibreOffice set {max(lines) + 1} lines for {ch!r}"
        at = max(i for i, c in enumerate(glyphs) if c[0] == ch)
        assert glyphs[at - 1][0] == last_word[-1]
        kept = abs(glyphs[at - 1][2] - glyphs[at][2]) < pitch / 2
        assert kept == (space_fits and ch in LB13), (ch, "kept" if kept else "broke before")


@_lo.needs_lo("Arial")
@pytest.mark.parametrize("ch", ["/", ",", "!"])
def test_headlines_filled_to_the_region_stay_inside(ch, tmp_path):
    """Headlines with the character after every word, accepted at every line the title
    region holds, stay inside it in LibreOffice."""
    pack = resolve("swiss")
    deck = Deck(pack="swiss", mode="presented", voice="neutral")
    setting = headline_setting(deck)
    title = _lo.region_pt(pack, LAYOUT, "title")
    held = int((title[3] - title[1]) // float(setting.pitch))
    rng = random.Random(7)
    found = []
    while len(found) < 4:
        text = f" {ch} ".join(rng.choice(WORDS) for _ in range(rng.randint(4, 20)))
        try:
            deck.add("evidence", text)
        except DoesNotFit:
            continue
        lines = wrap(setting, text, title[2] - title[0])
        if len(lines) == held:
            found.append(text)
        else:
            deck._slides.pop()
    deck.save(str(tmp_path / "fill.pptx"))
    for text, page in zip(found, _lo.chars(tmp_path / "fill.pptx", tmp_path / "lo"), strict=True):
        assert max(c[4] for c in page) <= title[3] + 1.5, text  # 2 px at 1280 px
