from __future__ import annotations

from fractions import Fraction

from keyline.registry import rule
from keyline.rules._common import RESEARCH_CANON, body_paragraphs, pick_title, words
from keyline.units import autofit_note, fmt_num, round2


@rule(
    id="body-too-small",
    category="quality",
    severity="warning",
    scope="slide",
    basis="text",
    since="0.1.0",
    summary="Body text is smaller than the mode's minimum size",
    rationale=RESEARCH_CANON,
)
def check(deck, cfg):
    floor = cfg.body_min_pt * 100  # in 1/100 pt, like Run.size
    for slide in deck.slides:
        title = pick_title(slide, cfg)
        worst: dict[int, tuple] = {}  # shape z -> (size, autofit, words, shape)
        for shape, para in body_paragraphs(slide, title, cfg):
            small = [r for r in para.runs if r.has_ink and r.size is not None and r.size < floor]
            if not small:
                continue
            run = min(small, key=lambda r: r.size)
            cur = worst.get(shape.z)
            if cur is None or run.size < cur[0]:
                worst[shape.z] = (run.size, run.autofit, words(para.text), shape)
        for _, (size, autofit, n, shape) in sorted(worst.items()):
            pt = Fraction(size, 100)
            yield check.finding(
                slide.index,
                shape,
                f"{fmt_num(pt)} pt{autofit_note(autofit)} text in a {n}-word paragraph "
                f"(min {fmt_num(cfg.body_min_pt)} pt in {cfg.mode} mode)",
                measured=round2(pt),
                threshold=round2(cfg.body_min_pt),
            )
