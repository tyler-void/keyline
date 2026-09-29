"""A colour that is not one of the voice's palette values (spec 002 §3.4, B-8.8)."""

from __future__ import annotations

from keyline.registry import rule
from keyline.rules._pack import PACK_DATA, palette


def _first_off(shape, allowed: set[str]) -> str | None:
    for run in shape.runs:
        if run.has_ink and run.color and run.color.upper() not in allowed:
            return run.color.upper()
    if shape.fill_rgb and shape.fill_rgb.upper() not in allowed:
        return shape.fill_rgb.upper()
    return None


@rule(
    id="off-palette-color",
    category="quality",
    severity="warning",
    scope="slide",
    basis="color",
    requires="pack",
    since="0.2.0",
    summary="A text colour, fill or slide background is not in the voice's palette",
    rationale=PACK_DATA,
)
def check(deck, cfg, ctx):
    allowed = palette(ctx)
    where = f"the {ctx.pack.name} palette (voice {ctx.voice.name})"
    for slide in deck.slides:
        bg = slide.background_rgb
        if bg and bg.upper() not in allowed:
            yield check.finding(
                slide.index, None, f"slide background #{bg.upper()} is not in {where}"
            )
        for shape in slide.shapes:
            off = _first_off(shape, allowed)
            if off is not None:
                yield check.finding(slide.index, shape, f"#{off} is not in {where}")
