"""Colour spaces for the pack and Claude-look rules (spec 002 §3.3, normative).

CIELAB: sRGB (IEC 61966-2-1) -> linear -> XYZ (D65) -> CIELAB with reference white
(0.95047, 1.0, 1.08883); C* = sqrt(a*^2 + b*^2); h = atan2(b*, a*) in degrees, [0, 360).
HSL: the CSS Color 4 definition, saturation and lightness in [0, 1].
Paper is judged by C*, saturated accents by HSL hue (lesson L-011).
"""

from __future__ import annotations

import colorsys
import math

_WHITE = (0.95047, 1.0, 1.08883)
_EPS = (6 / 29) ** 3
_KAPPA = 3 * (6 / 29) ** 2


def _channels(hex_rgb: str) -> tuple[float, float, float]:
    h = hex_rgb.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"not an RRGGBB colour: {hex_rgb!r}")
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def _linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _f(t: float) -> float:
    return t ** (1 / 3) if t > _EPS else t / _KAPPA + 4 / 29


def lab(hex_rgb: str) -> tuple[float, float, float]:
    """(L*, C*, h) of an sRGB hex colour."""
    r, g, b = (_linear(c) for c in _channels(hex_rgb))
    x = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b
    fx, fy, fz = _f(x / _WHITE[0]), _f(y / _WHITE[1]), _f(z / _WHITE[2])
    lightness = 116 * fy - 16
    a, bb = 500 * (fx - fy), 200 * (fy - fz)
    return lightness, math.hypot(a, bb), math.degrees(math.atan2(bb, a)) % 360


def hsl(hex_rgb: str) -> tuple[float, float, float]:
    """(hue in degrees, saturation, lightness) of an sRGB hex colour."""
    hue, lightness, saturation = colorsys.rgb_to_hls(*_channels(hex_rgb))
    return hue * 360, saturation, lightness
