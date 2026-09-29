"""More accent elements on a slide than the pack's budget (spec 002 §3.4, B-8.8)."""

from __future__ import annotations

from keyline.registry import rule
from keyline.rules._common import RESEARCH_TELLS
from keyline.rules._pack import is_accent_element


@rule(
    id="accent-overuse",
    category="slop",
    severity="warning",
    scope="slide",
    basis="color",
    requires="pack",
    since="0.2.0",
    summary="A slide has more accent elements than the pack's accent budget",
    rationale=RESEARCH_TELLS,
)
def check(deck, cfg, ctx):
    accents = ctx.voice.accent_hexes(ctx.pack)
    budget = ctx.pack.accent_budget
    for slide in deck.slides:
        count = sum(1 for shape in slide.shapes if is_accent_element(shape, accents))
        if count > budget:
            yield check.finding(
                slide.index,
                None,
                f"{count} accent elements; {ctx.pack.name} allows {budget} per slide",
                measured=count,
                threshold=budget,
            )
