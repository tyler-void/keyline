from __future__ import annotations

from keyline.geom import overlap
from keyline.registry import rule
from keyline.rules._common import cm_emu, is_text_bearing
from keyline.units import cm, fmt_cm, round2


@rule(
    id="box-overlap",
    category="quality",
    severity="advisory",
    scope="slide",
    basis="geometry",
    since="0.1.0",
    summary="The boxes of two text-bearing shapes intersect (boxes, not ink)",
    rationale="L-005",
)
def check(deck, cfg):
    limit = cm_emu(cfg.box_overlap_min_cm)
    for slide in deck.slides:
        texts = [s for s in slide.shapes if s.box is not None and is_text_bearing(s)]
        for i, a in enumerate(texts):
            for b in texts[i + 1 :]:
                ox, oy = overlap(a.box, b.box)
                if ox > limit and oy > limit:
                    first, other = (a, b) if a.id <= b.id else (b, a)
                    yield check.finding(
                        slide.index,
                        first,
                        f"box overlaps {other.name or f'#{other.id}'} by "
                        f"{fmt_cm(ox)} × {fmt_cm(oy)} cm (boxes, not ink)",
                        measured=cm(min(ox, oy)),
                        threshold=round2(cfg.box_overlap_min_cm),
                    )
