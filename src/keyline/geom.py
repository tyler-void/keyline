"""Axis-aligned boxes on integer EMU."""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

from keyline.units import round_half_away

ROT_UNITS_PER_DEGREE = 60000


@dataclass(frozen=True, slots=True)
class Box:
    x: int
    y: int
    w: int
    h: int

    @property
    def left(self) -> int:
        return self.x

    @property
    def top(self) -> int:
        return self.y

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h

    @property
    def area(self) -> int:
        return max(self.w, 0) * max(self.h, 0)


def overlap(a: Box, b: Box) -> tuple[int, int]:
    """Overlap along x and y. Negative values are the gap between the boxes."""
    ox = min(a.right, b.right) - max(a.left, b.left)
    oy = min(a.bottom, b.bottom) - max(a.top, b.top)
    return ox, oy


def contains(outer: Box, inner: Box) -> bool:
    """True if `inner` lies inside `outer`. Shared edges count as inside."""
    return (
        outer.left <= inner.left
        and outer.top <= inner.top
        and inner.right <= outer.right
        and inner.bottom <= outer.bottom
    )


def slide_coverage(box: Box, width: int, height: int) -> Fraction:
    """Fraction of the slide area covered by `box` after clipping it to the slide."""
    ox = min(box.right, width) - max(box.left, 0)
    oy = min(box.bottom, height) - max(box.top, 0)
    if ox <= 0 or oy <= 0 or width <= 0 or height <= 0:
        return Fraction(0)
    return Fraction(ox * oy, width * height)


def rotated_aabb(x: int, y: int, w: int, h: int, rot: int) -> Box:
    """Bounding box of a w×h rectangle at (x, y) rotated by `rot` (60000ths of a degree)
    about its center. Multiples of 90° are exact; other angles use float trig once."""
    rot %= 360 * ROT_UNITS_PER_DEGREE
    cx = Fraction(2 * x + w, 2)
    cy = Fraction(2 * y + h, 2)
    if rot % (90 * ROT_UNITS_PER_DEGREE) == 0:
        quarter = rot // (90 * ROT_UNITS_PER_DEGREE)
        bw, bh = (w, h) if quarter % 2 == 0 else (h, w)
        bx = round_half_away(cx - Fraction(bw, 2))
        by = round_half_away(cy - Fraction(bh, 2))
        return Box(bx, by, bw, bh)
    theta = math.radians(rot / ROT_UNITS_PER_DEGREE)
    c, s = abs(math.cos(theta)), abs(math.sin(theta))
    bw_f = w * c + h * s
    bh_f = w * s + h * c
    bx = round_half_away(cx - Fraction(repr(bw_f)) / 2)
    by = round_half_away(cy - Fraction(repr(bh_f)) / 2)
    return Box(bx, by, round_half_away(repr(bw_f)), round_half_away(repr(bh_f)))
