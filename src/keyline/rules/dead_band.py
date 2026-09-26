from __future__ import annotations

from fractions import Fraction

from keyline.registry import rule
from keyline.rules._common import is_background, is_content_slide, is_visible
from keyline.units import fmt_cm, fmt_pct, round3


def occupied(slide, deck, cfg) -> list[tuple[int, int]]:
    """Merged [top, bottom] spans of every visible, non-background shape (and connectors),
    clipped to the slide."""
    spans = []
    for s in slide.shapes:
        if s.box is None or is_background(s, deck, cfg):
            continue
        if not (is_visible(s) or s.kind == "cxnSp"):
            continue
        top, bottom = max(0, s.box.top), min(deck.height, s.box.bottom)
        if top > deck.height or bottom < 0 or bottom < top:
            continue
        spans.append((top, bottom))
    spans.sort()
    merged: list[list[int]] = []
    for top, bottom in spans:
        if merged and top <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], bottom)
        else:
            merged.append([top, bottom])
    return [(a, b) for a, b in merged]


def gaps(spans: list[tuple[int, int]], height: int) -> list[tuple[int, int]]:
    edges = [0]
    for top, bottom in spans:
        edges += [top, bottom]
    edges.append(height)
    return [(edges[i], edges[i + 1]) for i in range(0, len(edges), 2)]


@rule(
    id="dead-band",
    category="quality",
    severity="warning",
    scope="slide",
    basis="geometry",
    since="0.1.0",
    summary="A content slide has a horizontal band with no shapes taller than the limit",
    rationale="L-003",
)
def check(deck, cfg):
    limit = cfg.dead_band_ratio * deck.height
    for slide in deck.slides:
        if not is_content_slide(slide):
            continue
        for a, b in gaps(occupied(slide, deck, cfg), deck.height):
            band = b - a
            if band <= limit:
                continue
            where = "top" if a == 0 else "bottom" if b == deck.height else "middle"
            ratio = Fraction(band, deck.height)
            yield check.finding(
                slide.index,
                None,
                f"{fmt_cm(band)} cm empty {where} band from {fmt_cm(a)} to {fmt_cm(b)} cm "
                f"({fmt_pct(ratio)} of slide height)",
                measured=round3(ratio),
                threshold=round3(cfg.dead_band_ratio),
            )
