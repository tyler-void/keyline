"""Fit (spec 002 §6.4, amendment B-21): width tables of the metric twins, and the
estimator the pen uses to refuse text that does not fit (T-22).

A table per portable family and weight holds the twin's advance widths (font units per
em, per codepoint), its maximum advance (used for a character the twin lacks),
`line_pitch_em` with the LibreOffice versions that measured it, and the Vietnamese letters
the twin lacks. Tables are data, written by `tools/gen_fit_tables.py`; lint never imports
this package.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

TABLES = Path(__file__).resolve().parent / "tables"
WEIGHTS = ("regular", "bold")

# the 134 precomposed Vietnamese letters: ă â đ ê ô ơ ư, and the twelve vowels with each
# of the five tones (grave, acute, hook above, tilde, dot below), lower and upper case
_TONES = "̣̀́̉̃"
_LOWER = list("ăâđêôơư") + [
    unicodedata.normalize("NFC", v + t) for v in "aăâeêioôơuưy" for t in _TONES
]
VIETNAMESE = "".join(_LOWER + [c.upper() for c in _LOWER])


class FitError(ValueError):
    """A fit table is missing or unreadable."""


def slug(twin: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", twin.casefold()).strip("-")


def table_path(twin: str, weight: str) -> Path:
    return TABLES / f"{slug(twin)}-{weight}.json"


@dataclass(frozen=True)
class Table:
    family: str  # the portable family (Arial)
    twin: str  # its metric twin (Liberation Sans)
    weight: str
    units_per_em: int
    max_advance: int
    line_pitch_em: Fraction
    measured_on: tuple[str, ...]  # the LibreOffice versions behind line_pitch_em (Q-44b)
    missing_vietnamese: str
    source: dict = field(repr=False)
    advances: dict[int, int] = field(repr=False)

    def advance(self, char: str) -> int:
        """The advance of one character in font units; the maximum for a missing one."""
        return self.advances.get(ord(char), self.max_advance)


_cache: dict[tuple[str, str], Table] = {}


def load_table(family: str, weight: str) -> Table:
    """The table for a portable family (as a voice names it) and a weight."""
    from keyline.config import load as load_config

    if weight not in WEIGHTS:
        raise FitError(f"unknown weight {weight!r}")
    twins = {f.casefold(): (f, t) for f, t in load_config().portable_fonts}
    if family.casefold() not in twins:
        raise FitError(f"{family!r} is not a portable font")
    fam, twin = twins[family.casefold()]
    key = (fam, weight)
    if key not in _cache:
        path = table_path(twin, weight)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise FitError(f"fit table {path.name} cannot be read: {exc}") from exc
        _cache[key] = Table(
            family=data["family"],
            twin=data["twin"],
            weight=data["weight"],
            units_per_em=data["units_per_em"],
            max_advance=data["max_advance"],
            line_pitch_em=Fraction(data["line_pitch_em"]),
            measured_on=tuple(data["measured_on"]),
            missing_vietnamese=data["missing_vietnamese"],
            source=data["source"],
            advances={cp: adv for cp, adv in data["advances"]},
        )
    return _cache[key]
