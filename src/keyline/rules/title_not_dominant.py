from __future__ import annotations

from fractions import Fraction

from keyline.registry import rule
from keyline.rules._common import (
    RESEARCH_CANON,
    body_paragraphs,
    max_size,
    paragraph_max_size,
    pick_title,
)
from keyline.units import fmt_num, round3


@rule(
    id="title-not-dominant",
    category="quality",
    severity="warning",
    scope="slide",
    basis="text",
    since="0.1.0",
    summary="The title is not clearly larger than the largest body text",
    rationale=RESEARCH_CANON,
)
def check(deck, cfg):
    for slide in deck.slides:
        title = pick_title(slide, cfg)
        if title is None or max_size(title) is None:
            continue
        body = [paragraph_max_size(p) for _, p in body_paragraphs(slide, title, cfg)]
        body = [b for b in body if b is not None]
        if not body:
            continue
        t, b = Fraction(max_size(title), 100), Fraction(max(body), 100)
        if t < cfg.title_ratio_min * b:
            yield check.finding(
                slide.index,
                title,
                f"title {fmt_num(t)} pt is {fmt_num(t / b)}× the largest body text "
                f"({fmt_num(b)} pt); needs {fmt_num(cfg.title_ratio_min)}×",
                measured=round3(t / b),
                threshold=round3(cfg.title_ratio_min),
            )
