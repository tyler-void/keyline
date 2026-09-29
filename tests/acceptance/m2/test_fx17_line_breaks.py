"""Audit 05 FX-17 (amendment B-22 item 4): no line break before ) ] } , . : ; ! ? / %
U+2030 U+00BB U+201D U+2019, even after a space (UAX #14, LB13); the estimator keeps them
with the word before. LibreOffice is checked with each character: a headline whose first
line is full, followed by " <char> end", must carry that line's last word down with the
character. Repro: evidence/audit05-repros/attack_uax14.py."""

import random

import pytest

from keyline.fit import WRAP_MARGIN, width, wrap
from keyline.fit.text import NO_BREAK_BEFORE, break_units
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
    assert break_units("( opens") == ["(", "opens"]  # opening brackets may start a line
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


def full_line_case(setting, room_pt, box_pt, ch, seed):
    """A headline whose first line is as full as the estimator allows, then " ch end",
    such that ch cannot fit on that line even at 1.01 × the box (LibreOffice's own wrap
    threshold is at most 1.003 × the advance sum, B-21)."""
    rng = random.Random(seed)
    for _ in range(20000):
        words = [rng.choice(WORDS) for _ in range(20)]
        k = 1
        while k < len(words) and width(setting, " ".join(words[: k + 1])) <= room_pt:
            k += 1
        first = " ".join(words[:k])
        if width(setting, f"{first} {ch}") > box_pt * 101 / 100:
            return first, f"{first} {ch} end"
    raise AssertionError(f"no case found for {ch!r}")


@_lo.needs_lo("Arial")
def test_libreoffice_never_sets_more_lines_than_the_estimator(tmp_path):
    """For each character, a headline whose first line is full, then " <char> end". The
    estimator carries the last word down with the character (2 lines). LibreOffice may do
    the same or break before the character (on 26.8.0.3 it keeps ) : ; ! / and breaks
    before the other ten; tools/measure_lo.py prints the table): either way it sets no
    more lines than the estimate. The audit's "/" (attack_uax14.py) must be kept."""
    pack = resolve("swiss")
    deck = Deck(pack="swiss", mode="presented", voice="neutral")
    setting = headline_setting(deck)
    x0, _y0, x1, _y1 = _lo.region_pt(pack, LAYOUT, "title")
    box_pt = x1 - x0
    cases = []
    for i, ch in enumerate(NO_BREAK_BEFORE):
        first, text = full_line_case(setting, box_pt * WRAP_MARGIN, box_pt, ch, i)
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
        if ch == "/":
            at = max(i for i, c in enumerate(glyphs) if c[0] == ch)
            assert glyphs[at - 1][0] == last_word[-1]
            assert abs(glyphs[at - 1][2] - glyphs[at][2]) < pitch / 2, "broke before '/'"


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
