from decimal import Decimal
from fractions import Fraction

from keyline.units import (
    cm,
    cm_to_emu,
    emu_to_cm,
    fmt_cm,
    fmt_num,
    pt_to_emu,
    round2,
    round_half_away,
)


def test_cm_emu_roundtrip_exact():
    assert cm_to_emu("1.27") == 457200
    assert cm_to_emu(Decimal("1.22")) == 439200
    assert cm_to_emu(0.05) == 18000
    assert emu_to_cm(432000) == Fraction(6, 5)
    assert pt_to_emu(1) == 12700


def test_round_half_away():
    assert round_half_away(Fraction(5, 2)) == 3
    assert round_half_away(Fraction(-5, 2)) == -3
    assert round_half_away(Fraction(7, 3)) == 2
    assert round_half_away("0.5") == 1


def test_round2_is_half_up_and_stable():
    assert round2(Fraction(1, 8)) == 0.13  # 0.125 rounds up, unlike round(0.125, 2)
    assert round2(3.5694) == 3.57
    assert repr(round2(Fraction(439200, 360000))) == "1.22"


def test_formatting():
    assert fmt_cm(432000) == "1.20"
    assert cm(316800) == 0.88
    assert fmt_num(12.5) == "12.5"
    assert fmt_num(11) == "11"
    assert fmt_num(Fraction(357, 100)) == "3.57"
