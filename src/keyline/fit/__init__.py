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

from keyline.fit.text import break_units, code_point, refused

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
    hhea_line_em: Fraction  # the twin's hhea line height; table cells use it above 1.2
    measured_on: tuple[str, ...]  # the LibreOffice versions behind line_pitch_em (Q-44b)
    missing_vietnamese: str
    source: dict = field(repr=False)
    advances: dict[int, int] = field(repr=False)

    def advance(self, char: str) -> int:
        """The advance of one character in font units; the maximum for a missing one."""
        return self.advances.get(ord(char), self.max_advance)


_cache: dict[tuple[str, str], Table] = {}


def load_table(family: str, weight: str) -> Table:
    """The table for a portable family (as a voice names it) and a weight. Cached before
    the config is read: the estimator asks for it once per width."""
    from keyline.config import load as load_config

    key = (family.casefold(), weight)
    if key in _cache:
        return _cache[key]
    if weight not in WEIGHTS:
        raise FitError(f"unknown weight {weight!r}")
    twins = {f.casefold(): t for f, t in load_config().portable_fonts}
    if family.casefold() not in twins:
        raise FitError(f"{family!r} is not a portable font")
    path = table_path(twins[family.casefold()], weight)
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
        hhea_line_em=Fraction(data["hhea_line_em"]),
        measured_on=tuple(data["measured_on"]),
        missing_vietnamese=data["missing_vietnamese"],
        source=data["source"],
        advances={cp: adv for cp, adv in data["advances"]},
    )
    return _cache[key]


# ---------------------------------------------------------------------------------------
# the estimator (§6.4 as amended by B-21): refuse, never shrink

WRAP_MARGIN = Fraction(99, 100)  # a line fits when its width ≤ 0.99 × the available width
LINE_ALLOWANCE_PT = Fraction(72, 2540)  # 0.01 mm per line, LibreOffice's layout unit (B-21)
# a table row: LibreOffice rounds each row up by one more unit (26.8.0.3, A2 fixes)
ROW_ALLOWANCE_PT = LINE_ALLOWANCE_PT
EMU_PER_PT = 12700


class DoesNotFit(ValueError):
    """Text that would not fit its region at its token size. The message says what, and
    how many lines it needs against how many the region holds."""


@dataclass(frozen=True)
class Setting:
    """How a style sets text: everything the estimate needs, in points."""

    family: str
    weight: str
    size: Fraction
    caps: bool = False
    tracking: Fraction = Fraction(0)  # a fraction of the size, per character
    line_spacing: Fraction = Fraction(1)
    space_before: Fraction = Fraction(0)
    space_after: Fraction = Fraction(0)
    indent: Fraction = Fraction(0)  # marL, taken from the available width

    @property
    def table(self) -> Table:
        return load_table(self.family, self.weight)

    @property
    def pitch(self) -> Fraction:
        return self.size * self.table.line_pitch_em * self.line_spacing + LINE_ALLOWANCE_PT

    @property
    def cell_pitch(self) -> Fraction:
        """A line's pitch in a table cell (B-22 item 5): LibreOffice 24.2.7.2 sets cells at
        the twin's hhea line height where that exceeds 1.2 em (audit 05)."""
        em = max(self.table.line_pitch_em, self.table.hhea_line_em)
        return self.size * em * self.line_spacing + LINE_ALLOWANCE_PT


def as_set(setting: Setting, text: str) -> str:
    """The text as rendered: upper-cased for caps styles, NFC."""
    return unicodedata.normalize("NFC", text.upper() if setting.caps else text)


def width(setting: Setting, text: str) -> Fraction:
    """§6.4's width: the advance sum (no kerning; a missing character counts as the
    twin's maximum advance) plus tracking × size per character."""
    shown = as_set(setting, text)
    table = setting.table
    units = sum(table.advance(ch) for ch in shown)
    return Fraction(units, table.units_per_em) * setting.size + (
        setting.tracking * setting.size * len(shown)
    )


def missing(setting: Setting, text: str) -> str:
    """The characters of `text` the twin lacks, in first-seen order (no spaces)."""
    table = setting.table
    shown = as_set(setting, text)
    return "".join(
        dict.fromkeys(c for c in shown if not c.isspace() and ord(c) not in table.advances)
    )


def wrap(setting: Setting, text: str, available: Fraction, what: str = "text") -> list[str]:
    """Greedy wrapping of the normalized text (B-22) at its spaces, U+0020 only, and
    never before closing punctuation (item 4): a line fits when its width ≤ 0.99 × the
    available width (after the indent). A single word, a run joined by no-break spaces,
    or a word with the punctuation kept to it, wider than that does not fit. A character
    the pen refuses (item 3) cannot be estimated: FitError."""
    bad = refused(text)
    if bad is not None:
        raise FitError(f"{what} contains {code_point(bad)}, which cannot be estimated")
    room = (available - setting.indent) * WRAP_MARGIN
    lines: list[str] = []
    current = ""
    for word in break_units(text):
        if width(setting, word) > room:
            raise DoesNotFit(f"{what}: the word {word!r} is wider than its region")
        candidate = f"{current} {word}" if current else word
        if width(setting, candidate) <= room:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def lines_held(setting: Setting, height: Fraction, paragraphs: int = 1) -> int:
    """How many lines of this setting a region of `height` holds."""
    spacing = (setting.space_before + setting.space_after) * paragraphs
    return max(int((height - spacing) // setting.pitch), 0)


def fit(
    setting: Setting,
    paragraphs: list[str],
    box_width: Fraction,
    box_height: Fraction,
    what: str = "text",
) -> list[list[str]]:
    """The wrapped lines of each paragraph, or DoesNotFit. A region holds n lines when
    n × (size × line_pitch_em × line spacing + 0.01 mm) plus the paragraphs' spacing is at
    most its height (B-21)."""
    wrapped = [wrap(setting, p, box_width, what) for p in paragraphs]
    needed = sum(len(w) for w in wrapped)
    spacing = (setting.space_before + setting.space_after) * len(paragraphs)
    if needed * setting.pitch + spacing > box_height:
        held = lines_held(setting, box_height, len(paragraphs))
        raise DoesNotFit(
            f"{what} needs {needed} lines, region holds {held}: shorten it or split the slide"
        )
    return wrapped


def coverage_warning(family: str, chars: str) -> str:
    """The one warning per deck when text uses characters the voice's twin lacks
    (audit 04); the build goes ahead."""
    twin = load_table(family, "regular").twin
    return (
        f"{twin} (for {family}) lacks: {chars}; LibreOffice renders them in a fallback "
        "font, so the check render is not faithful"
    )
