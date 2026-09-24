"""Transforms: a shape's own xfrm, group composition, rotation.

A Placement is a rectangle in slide space kept as an exact center and size, plus the
total rotation. Groups map child space to parent space (spec §2.3):
  x' = off.x + (x - chOff.x) * ext.cx / chExt.cx   (same for y; w and h scale)
then the group's flips mirror the child's center about the group's center, and the
group's rotation turns it about the same center (P-3).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

from lxml import etree

from keyline.geom import ROT_UNITS_PER_DEGREE, Box, aabb_about_center
from keyline.ooxml.ns import NS, q
from keyline.units import round_half_away

FULL_TURN = 360 * ROT_UNITS_PER_DEGREE


@dataclass(frozen=True, slots=True)
class Xfrm:
    x: int
    y: int
    cx: int
    cy: int
    rot: int = 0
    flip_h: bool = False
    flip_v: bool = False
    ch_x: int = 0
    ch_y: int = 0
    ch_cx: int = 0
    ch_cy: int = 0


def _int(el: etree._Element | None, attr: str) -> int | None:
    if el is None:
        return None
    raw = el.get(attr)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def parse_xfrm(el: etree._Element | None) -> Xfrm | None:
    """`a:xfrm`, `p:xfrm` or `a:xfrm` inside grpSpPr. None unless off and ext are complete."""
    if el is None:
        return None
    off, ext = el.find(q("a:off")), el.find(q("a:ext"))
    x, y, cx, cy = _int(off, "x"), _int(off, "y"), _int(ext, "cx"), _int(ext, "cy")
    if None in (x, y, cx, cy):
        return None
    ch_off, ch_ext = el.find(q("a:chOff")), el.find(q("a:chExt"))
    return Xfrm(
        x=x,
        y=y,
        cx=cx,
        cy=cy,
        rot=_int(el, "rot") or 0,
        flip_h=el.get("flipH") in ("1", "true"),
        flip_v=el.get("flipV") in ("1", "true"),
        ch_x=_int(ch_off, "x") or 0,
        ch_y=_int(ch_off, "y") or 0,
        ch_cx=_int(ch_ext, "cx") or 0,
        ch_cy=_int(ch_ext, "cy") or 0,
    )


def xfrm_element(shape: etree._Element) -> etree._Element | None:
    """The transform element of sp, pic, cxnSp, graphicFrame or grpSp."""
    tag = etree.QName(shape).localname
    if tag == "graphicFrame":
        return shape.find("p:xfrm", NS)
    if tag == "grpSp":
        return shape.find("p:grpSpPr/a:xfrm", NS)
    return shape.find("p:spPr/a:xfrm", NS)


@dataclass(frozen=True, slots=True)
class Placement:
    cx: Fraction
    cy: Fraction
    w: Fraction
    h: Fraction
    rot: int  # 60000ths of a degree, normalized to [0, 360°)

    @classmethod
    def from_xfrm(cls, x: Xfrm) -> Placement:
        return cls(
            Fraction(2 * x.x + x.cx, 2),
            Fraction(2 * x.y + x.cy, 2),
            Fraction(x.cx),
            Fraction(x.cy),
            x.rot % FULL_TURN,
        )

    def rect(self) -> tuple[int, int, int, int]:
        """The unrotated rectangle in slide space, rounded to EMU."""
        left = round_half_away(self.cx - self.w / 2)
        top = round_half_away(self.cy - self.h / 2)
        return left, top, round_half_away(self.w), round_half_away(self.h)

    def box(self) -> Box:
        return aabb_about_center(self.cx, self.cy, self.w, self.h, self.rot)


def _rotate(px: Fraction, py: Fraction, ox: Fraction, oy: Fraction, rot: int):
    """Rotate (px, py) clockwise about (ox, oy) in slide space (y down)."""
    rot %= FULL_TURN
    dx, dy = px - ox, py - oy
    quarter, rest = divmod(rot, 90 * ROT_UNITS_PER_DEGREE)
    if rest == 0:
        for _ in range(quarter):
            dx, dy = -dy, dx
        return ox + dx, oy + dy
    t = math.radians(rot / ROT_UNITS_PER_DEGREE)
    c, s = math.cos(t), math.sin(t)
    fx, fy = float(dx), float(dy)
    return ox + Fraction(repr(fx * c - fy * s)), oy + Fraction(repr(fx * s + fy * c))


def apply_group(p: Placement, g: Xfrm) -> Placement:
    """Map a placement from the group's child space into its parent's space."""
    sx = Fraction(g.cx, g.ch_cx) if g.ch_cx else Fraction(1)
    sy = Fraction(g.cy, g.ch_cy) if g.ch_cy else Fraction(1)
    cx = g.x + (p.cx - g.ch_x) * sx
    cy = g.y + (p.cy - g.ch_y) * sy
    w, h = p.w * sx, p.h * sy
    rot = p.rot
    gcx = Fraction(2 * g.x + g.cx, 2)
    gcy = Fraction(2 * g.y + g.cy, 2)
    if g.flip_h:
        cx = 2 * gcx - cx
        rot = -rot
    if g.flip_v:
        cy = 2 * gcy - cy
        rot = -rot
    if g.rot % FULL_TURN:
        cx, cy = _rotate(cx, cy, gcx, gcy, g.rot)
        rot += g.rot
    return Placement(cx, cy, w, h, rot % FULL_TURN)
