from __future__ import annotations

from fractions import Fraction

from keyline.registry import rule
from keyline.rules._common import (
    RESEARCH_CANON,
    body_paragraphs,
    max_size,
    pick_title,
)
from keyline.units import autofit_note, fmt_num, round3


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
        body = [
            r
            for _, p in body_paragraphs(slide, title, cfg)
            for r in p.runs
            if r.has_ink and r.size is not None
        ]
        if not body:
            continue
        big = max(body, key=lambda r: r.size)
        head = max(
            (r for r in title.runs if r.has_ink and r.size is not None), key=lambda r: r.size
        )
        t, b = Fraction(head.size, 100), Fraction(big.size, 100)
        if t < cfg.title_ratio_min * b:
            yield check.finding(
                slide.index,
                title,
                f"title {fmt_num(t)} pt{autofit_note(head.autofit)} is {fmt_num(t / b)}× the "
                f"largest body text ({fmt_num(b)} pt{autofit_note(big.autofit)}); "
                f"needs {fmt_num(cfg.title_ratio_min)}×",
                measured=round3(t / b),
                threshold=round3(cfg.title_ratio_min),
            )
