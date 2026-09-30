"""The writer-neutral slide plan (D-015): what the pen decided, in values, with no writer
type. `_writer_pptx` turns it into python-pptx calls; a second writer would read the same
plan."""

from __future__ import annotations

from dataclasses import dataclass, field

from keyline.geom import Box


@dataclass(frozen=True)
class RunSpec:
    text: str
    size: int  # hundredths of a point
    bold: bool
    caps: bool
    spacing: int  # tracking, hundredths of a point
    color: str  # RRGGBB
    font: str  # a theme font slot: "+mj-lt" (display) or "+mn-lt" (text)


@dataclass(frozen=True)
class ParaSpec:
    runs: tuple[RunSpec, ...]
    line_spacing: int  # a:spcPct, 1/1000 %: 100000 = 100 %
    space_before: int  # hundredths of a point
    space_after: int
    indent: int = 0  # marL, EMU
    bullet: str = ""  # the marker, or "" for none


@dataclass(frozen=True)
class TextSpec:
    name: str
    box: Box
    paragraphs: tuple[ParaSpec, ...]
    placeholder: int | None = None  # the layout placeholder idx it fills (0 = title)
    anchor: str = "t"


@dataclass(frozen=True)
class RectSpec:
    name: str
    box: Box
    fill: str  # RRGGBB


@dataclass
class SlidePlan:
    layout: str
    shapes: list = field(default_factory=list)
    notes: str = ""


@dataclass(frozen=True)
class TableSpec:
    name: str
    box: Box
    col_widths: tuple[int, ...]  # EMU; they sum to the box width
    row_heights: tuple[int, ...]  # EMU
    cells: tuple[tuple[tuple[ParaSpec, ...], ...], ...]  # rows × columns × paragraphs
    margins: tuple[int, int, int, int]  # left, right, top, bottom (EMU)
    rule: str  # RRGGBB of the hairline under each row
    rule_width: int  # EMU


@dataclass(frozen=True)
class ChartSpec:
    name: str
    box: Box
    categories: tuple[str, ...]
    values: tuple[float, ...]
    number_format: str
    bar: str  # RRGGBB, muted bars
    highlight: int | None  # the category index drawn in the accent
    accent: str
    text: str  # RRGGBB of labels
    rule: str  # RRGGBB of the light horizontal rules
    font: str  # the voice's text family
    size: int  # hundredths of a point


@dataclass(frozen=True)
class PictureSpec:
    name: str
    box: Box
    data: bytes  # the file as image() read it (B-23)
    descr: str
