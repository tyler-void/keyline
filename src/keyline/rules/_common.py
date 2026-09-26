"""Shared predicates for rules (plan §4, A-1, A-2, A-7)."""

from __future__ import annotations

from collections.abc import Iterator
from fractions import Fraction

from keyline.config import Config
from keyline.model import Deck, Paragraph, Shape, Slide
from keyline.units import EMU_PER_CM

RESEARCH_CANON = 'research §The canon agrees on "one claim per slide" and disagrees on density'
RESEARCH_NICHE = (
    "research §The niche is open at only one point: an anti-slop linter that runs on any .pptx file"
)
RESEARCH_TELLS = (
    "research §ANTI-TELLS.md should start from about 30 tells with measurable signatures"
)


def cm_emu(cm: Fraction) -> int | Fraction:
    """A threshold in cm as exact EMU; a plain int when it is whole (A-18: integer EMU)."""
    emu = cm * EMU_PER_CM
    return emu.numerator if emu.denominator == 1 else emu


def words(text: str) -> int:
    """Whitespace-separated tokens that contain at least one letter or digit (A-7)."""
    return sum(1 for tok in text.split() if any(ch.isalnum() for ch in tok))


def is_text_bearing(shape: Shape) -> bool:
    """A `sp` with at least one run of visible, non-whitespace text (P-16). Cached on the
    shape: rules ask this for every shape many times (A-18)."""
    cached = shape._text_bearing
    if cached is None:
        cached = shape.kind == "sp" and any(r.has_ink for r in shape.runs)
        shape._text_bearing = cached
    return cached


def is_visible(shape: Shape) -> bool:
    """Text-bearing, filled, a picture, or any graphic frame (A-3)."""
    return (
        is_text_bearing(shape)
        or shape.fill != "none"
        or shape.kind == "pic"
        or shape.kind.startswith("graphicFrame")
    )


def is_background(shape: Shape, deck: Deck, cfg: Config) -> bool:
    """A visible shape covering at least `background_coverage_min` of the slide area."""
    if shape.box is None or not is_visible(shape):
        return False
    b = shape.box
    ox = min(b.right, deck.width) - max(b.left, 0)
    oy = min(b.bottom, deck.height) - max(b.top, 0)
    if ox <= 0 or oy <= 0:
        return False
    # exact integer form of ox*oy / (W*H) >= threshold (A-18: integer EMU)
    t = cfg.background_coverage_min
    return ox * oy * t.denominator >= t.numerator * deck.width * deck.height


def is_content_slide(slide: Slide) -> bool:
    """M1 treats slide 1 as the cover (spec §5)."""
    return slide.index > 1


def max_size(shape: Shape) -> int | None:
    """Largest resolved run size (1/100 pt) among runs with ink."""
    sizes = [r.size for r in shape.runs if r.has_ink and r.size is not None]
    return max(sizes) if sizes else None


def paragraph_max_size(p: Paragraph) -> int | None:
    sizes = [r.size for r in p.runs if r.has_ink and r.size is not None]
    return max(sizes) if sizes else None


def is_kpi_numeral(shape: Shape, cfg: Config) -> bool:
    """Per shape: max run size >= kpi_numeral_min_pt and <= kpi_numeral_max_words words."""
    size = max_size(shape)
    if size is None:
        return False
    return Fraction(size, 100) >= cfg.kpi_numeral_min_pt and words(shape.text) <= cfg.as_int(
        "kpi_numeral_max_words"
    )


def pick_title(slide: Slide, cfg: Config) -> Shape | None:
    """A-1: a title/ctrTitle placeholder with text; otherwise the non-KPI text-bearing
    shape with the largest max run size, ties to the earliest in z-order."""
    for s in slide.shapes:
        if s.ph_type in ("title", "ctrTitle") and is_text_bearing(s):
            return s
    best: Shape | None = None
    best_size = -1
    for s in slide.shapes:
        if not is_text_bearing(s) or is_kpi_numeral(s, cfg):
            continue
        size = max_size(s)
        if size is not None and size > best_size:
            best, best_size = s, size
    return best


def body_paragraphs(
    slide: Slide, title: Shape | None, cfg: Config
) -> Iterator[tuple[Shape, Paragraph]]:
    """A-2: paragraphs with more than caption_exempt_words words, in text-bearing shapes
    other than the title."""
    limit = cfg.as_int("caption_exempt_words")
    for s in slide.shapes:
        if s is title or not is_text_bearing(s):
            continue
        for p in s.paragraphs:
            if words(p.text) > limit:
                yield s, p
