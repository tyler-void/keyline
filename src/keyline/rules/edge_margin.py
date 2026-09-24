from __future__ import annotations

from keyline.registry import rule
from keyline.rules._common import cm_emu, is_background, is_visible
from keyline.rules.off_slide import worst_overrun
from keyline.units import cm, fmt_cm, fmt_num, round2


@rule(
    id="edge-margin",
    category="quality",
    severity="warning",
    scope="slide",
    basis="geometry",
    since="0.1.0",
    summary="A visible shape sits closer to a slide edge than the margin allows",
    rationale="L-006",
)
def check(deck, cfg):
    floor = cm_emu(cfg.edge_margin_cm - cfg.edge_margin_tolerance_cm)
    off_tol = cm_emu(cfg.off_slide_tolerance_cm)
    for slide in deck.slides:
        for s in slide.shapes:
            if s.box is None or s.kind == "cxnSp" or not is_visible(s):
                continue
            if is_background(s, deck, cfg):
                continue
            if worst_overrun(s.box, deck.width, deck.height)[0] > off_tol:
                continue  # already reported by off-slide (P-20)
            b = s.box
            margins = [
                (b.left, "left"),
                (b.top, "top"),
                (deck.width - b.right, "right"),
                (deck.height - b.bottom, "bottom"),
            ]
            margin, side = min(margins, key=lambda t: t[0])
            if margin < floor:
                yield check.finding(
                    slide.index,
                    s,
                    f"{fmt_cm(margin)} cm from the {side} edge "
                    f"(min {fmt_num(cfg.edge_margin_cm)} cm)",
                    measured=cm(margin),
                    threshold=round2(cfg.edge_margin_cm),
                )
