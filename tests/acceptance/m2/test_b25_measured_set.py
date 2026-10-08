"""Amendment B-25 item 1 (audit 06) and Q-51: the measured set is Basic Latin, Latin-1
Supplement, Latin Extended-A and -B, Latin Extended Additional, General Punctuation and
Currency Symbols, minus what B-22 refuses. The fit tables take the descent room, the top
reach and the left reach over it; outside it, and for its letters a twin lacks, the pen
prints one warning per deck. Characters are written as code points."""

import sys
import unicodedata

import pytest

from keyline.config import load as load_config
from keyline.fit import WEIGHTS, load_table
from keyline.fit.text import MEASURED, MEASURED_BLOCKS, inked, measured, refused
from tests.acceptance.m2 import _lo

pytest.importorskip("pptx")

from keyline.pen import Deck

FAMILIES = [f for f, _twin in load_config().portable_fonts]
CJK = chr(0x6F22) + chr(0x5B57)
HEBREW = "".join(map(chr, (0x05E9, 0x05DC, 0x05D5, 0x05DD)))
STACKED = chr(0x1EA8)  # LATIN CAPITAL LETTER A WITH CIRCUMFLEX AND HOOK ABOVE


def test_the_measured_set():
    expected = {
        chr(c)
        for a, b in MEASURED_BLOCKS
        for c in range(a, b + 1)
        if refused(chr(c)) is None and unicodedata.category(chr(c)) != "Cn"
    }
    assert set(MEASURED) == expected and len(MEASURED) == len(expected)
    assert [(a, b) for a, b in MEASURED_BLOCKS] == [
        (0x0000, 0x007F), (0x0080, 0x00FF), (0x0100, 0x017F), (0x0180, 0x024F),
        (0x1E00, 0x1EFF), (0x2000, 0x206F), (0x20A0, 0x20CF),
    ]  # fmt: skip
    for ch in "Az09.,%" + chr(0xE9) + chr(0x1A1) + STACKED + chr(0x20AB) + chr(0x2014):
        assert measured(ch), ch
    for ch in (*CJK, *HEBREW, chr(0x1F600), "\t", chr(0x200B), chr(0x0E2A)):
        assert not measured(ch), hex(ord(ch))
    assert measured(chr(0x200D)) and not inked(chr(0x200D))  # a format control draws nothing
    assert sys.maxunicode > 0x20CF


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("weight", WEIGHTS)
def test_the_tables_hold_the_extents_over_the_measured_set(family, weight):
    t = load_table(family, weight)
    assert t.descent_em > 0 and t.top_em > 0 and t.left_em >= 0
    if family == "Georgia":  # Gelasio's stacked capitals reach about 1.2 em
        assert t.top_em > 1


def test_one_warning_names_what_the_fit_does_not_cover(tmp_path, capsys):
    cambria = _lo.voice_file(tmp_path, "Cambria")
    d = Deck(pack="swiss", mode="read", voice=cambria)
    d.add("statement", f"Cây cảnh {CJK}").text(f"Người giữ {HEBREW}")
    d.add("statement", f"Mười hai {CJK}")
    d.save(str(tmp_path / "d.pptx"))
    (line,) = capsys.readouterr().err.splitlines()
    assert line.startswith("keyline pen: warning: the fit does not cover some characters (B-25)")
    lacks = line.split("lacks: ", 1)[1].split(";", 1)[0]
    outside = line.split("outside the measured set: ", 1)[1].split(";", 1)[0]
    assert set(outside) == set(CJK + HEBREW) and len(outside) == len(set(outside))
    assert not set(lacks) & set(outside) and "ả" in lacks


def test_no_warning_inside_the_measured_set(capsys, tmp_path):
    d = Deck(pack="swiss", mode="presented", voice="field")
    d.add("statement", f"{STACKED}n số và ổn định").text("Giá 12.400 ₫, tăng 3% — đúng hạn")
    d.save(str(tmp_path / "d.pptx"))
    assert capsys.readouterr().err == ""
