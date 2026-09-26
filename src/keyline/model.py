"""The normalized deck model (spec §2). Lengths are integer EMU; sizes are 1/100 pt."""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

from keyline.geom import Box

KINDS = ("sp", "pic", "graphicFrame:chart", "graphicFrame:table", "graphicFrame:other", "cxnSp")


@dataclass(frozen=True, slots=True)
class Run:
    text: str
    size: int | None  # effective size in 1/100 pt: resolved `sz` × autofit (A-14)
    bold: bool = False
    italic: bool = False
    caps: str = "none"  # none | small | all
    spacing: int = 0  # hundredths of a point
    font: str | None = None  # resolved latin typeface
    color: str | None = None  # "RRGGBB", or None when unresolved
    hidden: bool = False  # a:noFill text: nothing is drawn
    autofit: int | None = None  # normAutofit@fontScale in 1/1000 % when below 100% (A-14)

    @property
    def size_pt(self) -> Fraction | None:
        return None if self.size is None else Fraction(self.size, 100)

    @property
    def has_ink(self) -> bool:
        return not self.hidden and bool(self.text.strip())


@dataclass(frozen=True, slots=True)
class Paragraph:
    runs: tuple[Run, ...]
    align: str = "l"
    level: int = 0

    @property
    def text(self) -> str:
        return "".join(r.text for r in self.runs)


@dataclass(slots=True)
class Shape:
    id: int
    name: str
    kind: str
    z: int  # position in the flattened spTree (0 = bottom)
    geometry: str | None = None  # prstGeom value, "custom", or None
    x: int | None = None
    y: int | None = None
    w: int | None = None
    h: int | None = None
    rot: int = 0
    box: Box | None = None  # axis-aligned bounding box after rotation
    fill: str = "none"  # solid:#RRGGBB | gradient | none | unknown
    ph_type: str | None = None
    ph_idx: int | None = None
    st_cxn: int | None = None
    end_cxn: int | None = None
    paragraphs: list[Paragraph] = field(default_factory=list)
    _text_bearing: bool | None = field(default=None, repr=False, compare=False)

    @property
    def text(self) -> str:
        return "\n".join(p.text for p in self.paragraphs)

    @property
    def runs(self) -> list[Run]:
        return [r for p in self.paragraphs for r in p.runs]

    @property
    def fill_rgb(self) -> str | None:
        return self.fill[len("solid:#") :] if self.fill.startswith("solid:#") else None


@dataclass(slots=True)
class Slide:
    index: int  # 1-based
    layout_name: str | None
    background: str  # solid:#RRGGBB | unknown
    shapes: list[Shape] = field(default_factory=list)
    has_notes: bool = False

    @property
    def background_rgb(self) -> str | None:
        b = self.background
        return b[len("solid:#") :] if b.startswith("solid:#") else None


@dataclass(slots=True)
class Deck:
    width: int
    height: int
    theme_colors: dict[str, str] = field(default_factory=dict)
    major_font: str | None = None
    minor_font: str | None = None
    slides: list[Slide] = field(default_factory=list)
