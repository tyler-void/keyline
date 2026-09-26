from fractions import Fraction

from keyline.ooxml.numbers import MAX_ABS, collect, integer, number


def test_accepted_forms():
    assert integer("25000", "a") == 25000
    assert integer("25000.0", "a") == 25000
    assert integer("1.5e6", "a") == 1500000
    assert integer("-914400", "a") == -914400
    assert number("75%", "lumMod@val", percent=True) == 75000
    assert number("12.5%", "x", percent=True) == Fraction(12500)
    assert integer(None, "a") is None


def test_rejected_values_are_recorded():
    with collect() as dropped:
        assert integer("first", "stCxn@id") is None
        assert integer("75%", "cNvPr@id") is None  # a percentage where none is allowed
        assert integer("9" * 40, "ext@cx") is None  # outside ST_Coordinate
        assert integer(str(MAX_ABS), "ext@cx") == MAX_ABS
    assert dropped == ['stCxn@id="first"', 'cNvPr@id="75%"', 'ext@cx="999999999999999999999..."']


def test_nothing_recorded_outside_collect():
    assert integer("nope", "a") is None  # no sink: silently None
