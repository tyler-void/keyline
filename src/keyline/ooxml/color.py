"""DrawingML color resolution.

Supported color elements: srgbClr, sysClr (lastClr), schemeClr (through the clrMap and
the theme; phClr takes the referencing style's color). prstClr, hslClr and scrgbClr
resolve to None with a reason.

Supported transforms, applied in document order (val is in 1/1000 of a percent):
  lumMod, lumOff  HSL lightness: L = L * lumMod, then L = L + lumOff, clamped to [0, 1]
  tint            per sRGB channel: c + (1 - c) * (1 - tint)
  shade           per sRGB channel: c * shade
  alpha           100% is ignored; anything lower resolves to None (no blending)
Any other transform resolves to None with reason "transform:<name>".
"""

from __future__ import annotations

import colorsys
import math
from dataclasses import dataclass

from lxml import etree

from keyline.ooxml.ns import q
from keyline.ooxml.numbers import number

CLR_MAP_KEYS = (
    "bg1",
    "tx1",
    "bg2",
    "tx2",
    "accent1",
    "accent2",
    "accent3",
    "accent4",
    "accent5",
    "accent6",
    "hlink",
    "folHlink",
)
DEFAULT_CLR_MAP = {
    "bg1": "lt1",
    "tx1": "dk1",
    "bg2": "lt2",
    "tx2": "dk2",
    **{k: k for k in CLR_MAP_KEYS[4:]},
}

COLOR_TAGS = frozenset(
    q(f"a:{n}") for n in ("srgbClr", "sysClr", "schemeClr", "prstClr", "hslClr", "scrgbClr")
)


@dataclass(frozen=True)
class ColorContext:
    theme_colors: dict[str, str]
    clr_map: dict[str, str]
    ph_color: str | None = None  # the color a fillRef/fontRef/bgRef passes as phClr

    def with_ph(self, ph_color: str | None) -> ColorContext:
        return ColorContext(self.theme_colors, self.clr_map, ph_color)


@dataclass(frozen=True, slots=True)
class Resolved:
    rgb: str | None  # "RRGGBB"
    problem: str | None = None


def parse_clr_map(el: etree._Element | None) -> dict[str, str]:
    if el is None:
        return dict(DEFAULT_CLR_MAP)
    return {k: el.get(k, DEFAULT_CLR_MAP[k]) for k in CLR_MAP_KEYS}


def apply_override(base: dict[str, str], clr_map_ovr: etree._Element | None) -> dict[str, str]:
    """p:clrMapOvr: masterClrMapping keeps `base`; overrideClrMapping replaces it (P-8)."""
    if clr_map_ovr is None:
        return base
    override = clr_map_ovr.find(q("a:overrideClrMapping"))
    if override is None:
        return base
    return parse_clr_map(override)


def _hex_to_rgb(h: str) -> tuple[float, float, float] | None:
    if len(h) != 6:
        return None
    try:
        return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]
    except ValueError:
        return None


def _rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    # half away from zero on non-negative values; c * 255 is clamped to [0, 255]
    return "".join(f"{min(255, max(0, math.floor(c * 255 + 0.5))):02X}" for c in rgb)


def _pct(el: etree._Element) -> float | None:
    """A transform's val as a fraction (1.0 == 100%); None when it cannot be parsed."""
    v = number(el.get("val", "0"), f"{etree.QName(el).localname}@val", percent=True)
    return None if v is None else float(v / 100000)


def find_color(parent: etree._Element | None) -> etree._Element | None:
    """The first color element directly under `parent` (e.g. a:solidFill)."""
    if parent is None:
        return None
    for child in parent:
        if child.tag in COLOR_TAGS:
            return child
    return None


def resolve(el: etree._Element | None, ctx: ColorContext) -> Resolved:
    if el is None:
        return Resolved(None, "color:missing")
    tag = el.tag.rpartition("}")[2]
    if tag == "srgbClr":
        base = (el.get("val") or "").upper()
    elif tag == "sysClr":
        base = (el.get("lastClr") or "").upper()
    elif tag == "schemeClr":
        val = el.get("val", "")
        if val == "phClr":
            if ctx.ph_color is None:
                return Resolved(None, "color:phClr-unbound")
            base = ctx.ph_color
        else:
            slot = ctx.clr_map.get(val, val)
            if slot not in ctx.theme_colors:
                return Resolved(None, f"color:scheme-{val}")
            base = ctx.theme_colors[slot]
    else:
        return Resolved(None, f"color:{tag}")
    rgb = _hex_to_rgb(base)
    if rgb is None:
        return Resolved(None, f"color:bad-value-{base or 'empty'}")
    if len(el) == 0:  # no transforms: the value is already the answer
        return Resolved(base)
    for t in el:
        name = etree.QName(t).localname
        if name in ("lumMod", "lumOff", "tint", "shade", "alpha") and _pct(t) is None:
            continue  # A-17: an unparseable transform is dropped (and reported)
        if name in ("lumMod", "lumOff"):
            h, lum, s = colorsys.rgb_to_hls(*rgb)
            lum = lum * _pct(t) if name == "lumMod" else lum + _pct(t)
            rgb = colorsys.hls_to_rgb(h, min(1.0, max(0.0, lum)), s)
        elif name == "tint":
            v = _pct(t)
            rgb = tuple(c + (1 - c) * (1 - v) for c in rgb)  # type: ignore[assignment]
        elif name == "shade":
            v = _pct(t)
            rgb = tuple(c * v for c in rgb)  # type: ignore[assignment]
        elif name == "alpha":
            if _pct(t) < 1:
                return Resolved(None, "transform:alpha")
        else:
            return Resolved(None, f"transform:{name}")
    return Resolved(_rgb_to_hex(rgb))
