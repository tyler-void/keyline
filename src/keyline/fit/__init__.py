"""Fit (spec 002 §6.4, amendments B-21 and B-22): width tables of the metric twins, and
the estimator the pen uses to refuse text that does not fit (T-22, audit 05).

A table per portable family and weight holds the twin's advance widths (font units per
em, per codepoint), its maximum advance (with thresholds.toml's `missing_glyph_em`, the
estimate for a character the twin lacks), its hhea line height (for table cells),
`line_pitch_em` with the LibreOffice versions that measured it, and the Vietnamese letters
the twin lacks. Tables are data, written by `tools/gen_fit_tables.py`; lint never imports
this package.
"""

from __future__ import annotations

import functools
import itertools
import json
import re
import unicodedata
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

from keyline.fit.text import break_units, code_point, measured, refused

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
    descent_em: Fraction  # over B-25's measured set: the deepest descent below the baseline
    top_em: Fraction  # the highest glyph top above the baseline (B-25 item 2)
    left_em: Fraction  # the furthest a glyph reaches left of its origin (B-24, B-25 item 3)
    measured_on: tuple[str, ...]  # the LibreOffice versions behind line_pitch_em (Q-44b)
    missing_vietnamese: str
    source: dict = field(repr=False)
    advances: dict[int, int] = field(repr=False)
    kern: dict[tuple[int, int], int] = field(default_factory=dict, repr=False)  # B-25 item 4
    # B-22 item 6: a character the twin lacks counts as max(max_advance, missing_glyph_em)
    missing_advance: Fraction = Fraction(0)

    def advance(self, char: str) -> int | Fraction:
        """The advance of one character in font units; `missing_advance` for one the twin
        lacks (LibreOffice sets it in a fallback font)."""
        return self.advances.get(ord(char), self.missing_advance)


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
    config = load_config()
    twins = {f.casefold(): t for f, t in config.portable_fonts}
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
        descent_em=Fraction(data["descent_em"]),
        top_em=Fraction(data["top_em"]),
        left_em=Fraction(data["left_em"]),
        measured_on=tuple(data["measured_on"]),
        missing_vietnamese=data["missing_vietnamese"],
        source=data["source"],
        advances={cp: adv for cp, adv in data["advances"]},
        kern={(a, b): v for a, b, v in data["kern"]},
        missing_advance=max(
            Fraction(data["max_advance"]), config.missing_glyph_em * data["units_per_em"]
        ),
    )
    return _cache[key]


# ---------------------------------------------------------------------------------------
# the estimator (§6.4 as amended by B-21): refuse, never shrink

WRAP_MARGIN = Fraction(99, 100)  # a line fits when its width ≤ 0.99 × the available width
LINE_ALLOWANCE_PT = Fraction(72, 2540)  # 0.01 mm per line, LibreOffice's layout unit (B-21)
# LibreOffice sets a line's baseline 0.2 em above its bottom (B-21: the first baseline is
# 1.00 em below the top of a 1.2 em line); a glyph descending further reaches below it
BELOW_BASELINE_EM = Fraction(1, 5)
# a table row: LibreOffice rounds each row up by one more unit (26.8.0.3, A2 fixes)
ROW_ALLOWANCE_PT = LINE_ALLOWANCE_PT


@functools.cache
def cell_data() -> tuple[Fraction, Fraction]:
    """(each cell line's allowance in pt, missing_line_em), from thresholds.toml
    (B-25 item 6)."""
    from keyline.config import load as load_config

    config = load_config()
    return config.cell_line_allowance_mm * Fraction(72, 254) * 10, config.missing_line_em


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
    def descent_room(self) -> Fraction:
        """Room kept under a region's last line for the twin's descenders, in points: what
        they reach below LibreOffice's line box (A2 fixes, found with FX-24)."""
        return self.size * max(Fraction(0), self.table.descent_em - BELOW_BASELINE_EM)

    @property
    def first_baseline(self) -> Fraction:
        """How far below its box's top LibreOffice sets the first baseline, in points: the
        line less the 0.2 em below its baseline (B-21). Measured per line spacing on both
        versions: 1.00 em at 1.0 and 1.12 em at 1.1 (B-25 item 2)."""
        return self.size * (self.table.line_pitch_em * self.line_spacing - BELOW_BASELINE_EM)

    @property
    def top_overhang(self) -> Fraction:
        """How far the twin's highest glyph over B-25's measured set rises above the box's
        top when it sits on the first line, in points (B-25 item 3)."""
        return max(Fraction(0), self.size * self.table.top_em - self.first_baseline)

    @property
    def left_overhang(self) -> Fraction:
        """How far the twin's glyphs over the measured set reach left of the box, in points
        (B-24, B-25 item 3)."""
        return self.size * self.table.left_em

    @property
    def cell_pitch(self) -> Fraction:
        """A line's pitch in a table cell (B-22 item 5, B-25 item 6): LibreOffice 24.2.7.2
        sets cells at the twin's hhea line height where that exceeds 1.2 em (audit 05), and
        each cell line gets `cell_line_allowance_mm`, the largest excess measured."""
        return self.cell_line_pitch(fallback=False)

    def cell_line_pitch(self, fallback: bool) -> Fraction:
        """A table cell's line pitch; `fallback`: the cell has a glyph the twin lacks, set
        in a fallback font, so its lines take at least `missing_line_em` (B-25 item 6)."""
        allowance_pt, missing_line_em = cell_data()
        em = max(self.table.line_pitch_em, self.table.hhea_line_em)
        if fallback:
            em = max(em, missing_line_em)
        return self.size * em * self.line_spacing + allowance_pt


def as_set(setting: Setting, text: str) -> str:
    """The text as rendered: upper-cased for caps styles, NFC."""
    return unicodedata.normalize("NFC", text.upper() if setting.caps else text)


def width(setting: Setting, text: str) -> Fraction:
    """§6.4's width: the advance sum (a character the twin lacks counts as max(its
    maximum advance, missing_glyph_em), B-22 item 6), plus the positive kerning pairs of
    the measured set (B-25 item 4; negative pairs are ignored), plus tracking × size per
    character."""
    shown = as_set(setting, text)
    table = setting.table
    units = sum(table.advance(ch) for ch in shown)
    if table.kern:  # positive pairs only (B-25 item 4): kerning that widens the text
        units += sum(table.kern.get((ord(a), ord(b)), 0) for a, b in itertools.pairwise(shown))
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


def unmeasured(text: str) -> str:
    """The characters of `text` outside B-25's measured set, in first-seen order (no
    spaces)."""
    return "".join(dict.fromkeys(c for c in text if not c.isspace() and not measured(c)))


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
    return max(int((height - spacing - setting.descent_room) // setting.pitch), 0)


def fit(
    setting: Setting,
    paragraphs: list[str],
    box_width: Fraction,
    box_height: Fraction,
    what: str = "text",
    descent: bool = True,
) -> list[list[str]]:
    """The wrapped lines of each paragraph, or DoesNotFit. A region holds n lines when
    n × (size × line_pitch_em × line spacing + 0.01 mm) plus the paragraphs' spacing plus
    the descent room under the last line is at most its height (B-21; A2 fixes).
    `descent=False`: the box's bottom is not its region's (a figure's numeral, whose label
    box follows in the same region)."""
    wrapped = [wrap(setting, p, box_width, what) for p in paragraphs]
    needed = sum(len(w) for w in wrapped)
    spacing = (setting.space_before + setting.space_after) * len(paragraphs)
    room = setting.descent_room if descent else 0
    if needed * setting.pitch + spacing + room > box_height:
        held = lines_held(setting, box_height, len(paragraphs))
        raise DoesNotFit(
            f"{what} needs {needed} lines, region holds {held}: shorten it or split the slide"
        )
    return wrapped


def coverage_warning(missing: dict[str, str], outside: str) -> str | None:
    """The one warning per deck (audit 04; B-25 item 1) when text uses characters the fit
    does not cover: letters of the measured set a voice's twin lacks (`missing`, family
    -> characters) and characters outside the measured set. The build goes ahead."""
    parts = [
        f"{load_table(family, 'regular').twin} (for {family}) lacks: {chars}"
        for family, chars in missing.items()
        if chars
    ]
    if outside:
        parts.append(f"outside the measured set: {outside}")
    if not parts:
        return None
    return (
        "the fit does not cover some characters (B-25): " + "; ".join(parts) + "; the pen "
        "estimated them conservatively but promises nothing for them, and the check render "
        "may set them in another font"
    )
