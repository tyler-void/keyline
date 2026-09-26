"""WCAG 2.x contrast of each run against its effective background.

The effective background is the first shape found walking down the z-order from the
text's own shape (P-26) whose box covers at least `backing_coverage_min` of the text
shape's box, edges included (A-15, replacing P-27's full containment), and whose fill is
not none; otherwise the slide background.
"""

from __future__ import annotations

from fractions import Fraction

from keyline.geom import coverage, overlap
from keyline.registry import rule
from keyline.rules._common import is_text_bearing
from keyline.units import autofit_note, fmt_num, round3


def _channel(c: int) -> float:
    v = c / 255
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def luminance(rgb: str) -> float:
    r, g, b = (int(rgb[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _covers(outer, inner, need) -> bool:
    """coverage(outer, inner) >= need, in exact integer arithmetic where possible."""
    if inner.area == 0:
        return coverage(outer, inner) >= need
    ox, oy = overlap(outer, inner)
    if ox <= 0 or oy <= 0:
        return False
    return ox * oy * need.denominator >= need.numerator * inner.area


def effective_background(shape, slide, cfg, position=None) -> tuple[str | None, str]:
    """(rgb or None, description). slide.shapes is in z order, so walking down from the
    shape's own position visits the shapes beneath it, topmost first."""
    if position is None:
        position = slide.shapes.index(shape)
    need = cfg.backing_coverage_min
    for s in reversed(slide.shapes[: position + 1]):
        if s.box is None:
            continue
        if s is not shape and not _covers(s.box, shape.box, need):
            continue
        if s.kind == "pic":
            return None, f"picture {s.name or s.id}"
        if s.fill == "none":
            continue
        if s.fill_rgb:
            return s.fill_rgb, s.name or f"#{s.id}"
        return None, f"{s.fill} fill of {s.name or s.id}"
    if slide.background_rgb:
        return slide.background_rgb, "slide background"
    return None, "slide background (not a solid fill)"


@rule(
    id="text-contrast",
    category="quality",
    severity="warning",
    scope="slide",
    basis="color",
    since="0.1.0",
    summary="Text contrast against its effective background is below WCAG 2.x",
    rationale="L-006",
    severity_notes="advisory when the text color or its background is unknown",
)
def check(deck, cfg):
    large_pt, large_bold_pt = cfg.large_text_pt * 100, cfg.large_text_bold_pt * 100
    for slide in deck.slides:
        for position, shape in enumerate(slide.shapes):
            if shape.box is None or not is_text_bearing(shape):
                continue
            bg, where = effective_background(shape, slide, cfg, position)
            runs = [r for r in shape.runs if r.has_ink and r.size is not None]
            if not runs:
                continue
            if bg is None:
                yield check.finding(
                    slide.index,
                    shape,
                    f"contrast not checked: background is the {where}",
                    severity="advisory",
                )
                continue
            if any(r.color is None for r in runs):
                yield check.finding(
                    slide.index,
                    shape,
                    "contrast not checked for runs whose color could not be resolved",
                    severity="advisory",
                )
            worst = None
            for r in runs:
                if r.color is None:
                    continue
                large = r.size >= large_pt or (r.bold and r.size >= large_bold_pt)
                need = cfg.contrast_large if large else cfg.contrast_normal
                ratio = contrast(r.color, bg)
                if ratio < float(need) and (worst is None or ratio < worst[0]):
                    worst = (ratio, need, r)
            if worst is not None:
                ratio, need, r = worst
                yield check.finding(
                    slide.index,
                    shape,
                    f"{r.color} on {bg} ({where}) is {fmt_num(Fraction(repr(ratio)))}:1 at "
                    f"{fmt_num(Fraction(r.size, 100))} pt{autofit_note(r.autofit)}"
                    f"{' bold' if r.bold else ''} "
                    f"(needs {fmt_num(need)}:1)",
                    measured=round3(ratio),
                    threshold=round3(need),
                )
