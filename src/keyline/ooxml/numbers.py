"""One tolerant parser for OOXML numeric attributes (A-17).

Accepted: integers, decimals ("25000.0", "1.5e6") and, where the attribute is a
percentage, "N%" as ISO/IEC 29500 Strict writes it ("75%" == 75000). A value that does
not parse, or lies outside the ST_Coordinate range, is dropped: the caller gets None and
the problem is recorded for one `adapter-unresolved` advisory.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from decimal import Decimal, InvalidOperation
from fractions import Fraction

from keyline.units import round_half_away

# ST_Coordinate is ±27273042316900 EMU; nothing numeric in DrawingML is legitimately larger.
MAX_ABS = 27273042316900
_INT = re.compile(r"^-?\d{1,14}$")  # the common case: a plain integer inside the range
_NUM = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d{1,3})?$")

_problems: ContextVar[list[str] | None] = ContextVar("keyline_number_problems", default=None)


@contextmanager
def collect() -> Iterator[list[str]]:
    """Record every dropped value inside the block."""
    found: list[str] = []
    token = _problems.set(found)
    try:
        yield found
    finally:
        _problems.reset(token)


def _drop(attr: str, raw: str) -> None:
    sink = _problems.get()
    shown = raw if len(raw) <= 24 else raw[:21] + "..."
    if sink is not None:
        sink.append(f'{attr}="{shown}"')


def number(raw: str | None, attr: str, *, percent: bool = False) -> Fraction | None:
    """None when absent; None (and a recorded problem) when unparseable or out of range.
    With percent=True, "N%" is N * 1000 (the 1/1000-percent unit of transitional OOXML)."""
    if raw is None:
        return None
    text = raw.strip()
    scale = 1
    if percent and text.endswith("%"):
        text, scale = text[:-1].strip(), 1000
    if not _NUM.match(text):
        _drop(attr, raw)
        return None
    try:
        value = Fraction(Decimal(text)) * scale
    except (InvalidOperation, ValueError):
        _drop(attr, raw)
        return None
    if abs(value) > MAX_ABS:
        _drop(attr, raw)
        return None
    return value


def integer(raw: str | None, attr: str, *, percent: bool = False) -> int | None:
    if raw is not None and _INT.match(raw):
        return int(raw)
    value = number(raw, attr, percent=percent)
    return None if value is None else round_half_away(value)
