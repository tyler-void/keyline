"""A type size that is not on the pack's scale for the mode (spec 002 §3.4)."""

from __future__ import annotations

from fractions import Fraction

from keyline.registry import rule
from keyline.rules._pack import PACK_DATA
from keyline.units import autofit_note, fmt_num


@rule(
    id="off-scale-size",
    category="quality",
    severity="warning",
    scope="slide",
    basis="text",
    requires="pack",
    since="0.2.0",
    summary="A run's effective size is not on the pack's type scale for the mode",
    rationale=PACK_DATA,
)
def check(deck, cfg, ctx):
    scale = ctx.pack.scale(cfg.mode)
    listed = ", ".join(fmt_num(Fraction(s, 100)) for s in sorted(scale))
    for slide in deck.slides:
        for shape in slide.shapes:
            run = next(
                (r for r in shape.runs if r.has_ink and r.size is not None and r.size not in scale),
                None,
            )
            if run is None:
                continue
            size = Fraction(run.size, 100)
            yield check.finding(
                slide.index,
                shape,
                f"{fmt_num(size)} pt{autofit_note(run.autofit)} is not on the {ctx.pack.name} "
                f"{cfg.mode} scale ({listed} pt)",
                measured=float(size),
            )
