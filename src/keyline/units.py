"""Units. Lengths are integer EMU internally; cm and pt appear only in output.

All rounding for output goes through this module so JSON and messages are byte-stable.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

EMU_PER_CM = 360000
EMU_PER_PT = 12700
EMU_PER_INCH = 914400

Number = int | float | Decimal | Fraction | str


def to_fraction(value: Number) -> Fraction:
    """Exact rational value. Floats go through their shortest repr, so 0.05 means 0.05."""
    if isinstance(value, Fraction):
        return value
    if isinstance(value, float):
        return Fraction(repr(value))
    if isinstance(value, Decimal):
        return Fraction(value)
    return Fraction(value)


def round_half_away(value: Number) -> int:
    """Round to the nearest int, halves away from zero."""
    f = to_fraction(value)
    n = abs(f)
    whole = n.numerator // n.denominator
    if (n - whole) * 2 >= 1:
        whole += 1
    return whole if f >= 0 else -whole


def cm_to_emu(cm: Number) -> int:
    return round_half_away(to_fraction(cm) * EMU_PER_CM)


def pt_to_emu(pt: Number) -> int:
    return round_half_away(to_fraction(pt) * EMU_PER_PT)


def emu_to_cm(emu: Number) -> Fraction:
    return to_fraction(emu) / EMU_PER_CM


def _quantize(value: Number, places: int) -> Decimal:
    f = to_fraction(value)
    d = Decimal(f.numerator) / Decimal(f.denominator)
    return d.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def round2(value: Number) -> float:
    """Round half-up to 2 decimals and return a float with a stable repr."""
    return float(_quantize(value, 2))


def round3(value: Number) -> float:
    """Ratios in `measured`/`threshold` get 3 decimals (A-16)."""
    return float(_quantize(value, 3))


def fmt_pct(ratio: Number) -> str:
    """A ratio as a percentage with 1 decimal: 0.25197 -> '25.2%' (A-16)."""
    return f"{_quantize(to_fraction(ratio) * 100, 1)}%"


def autofit_note(scale: int | None) -> str:
    """' (autofit 28.1%)' for a shrunk run, '' otherwise (A-14)."""
    return "" if scale is None else f" (autofit {fmt_pct(Fraction(scale, 100000))})"


def cm(emu: Number) -> float:
    """EMU to cm, rounded to 2 decimals (the spec's message unit)."""
    return round2(emu_to_cm(emu))


def fmt_cm(emu: Number) -> str:
    """'1.20' style text for messages: always two decimals."""
    return f"{_quantize(emu_to_cm(emu), 2)}"


def fmt_num(value: Number) -> str:
    """Up to 2 decimals, trailing zeros dropped: 12.5, 11, 3.57."""
    q = _quantize(value, 2)
    text = f"{q:f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text
