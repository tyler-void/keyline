from __future__ import annotations

from keyline.geom import Box
from keyline.registry import rule
from keyline.rules._common import RESEARCH_NICHE, cm_emu, is_text_bearing
from keyline.units import cm, fmt_cm, round2

SIDES = ("left", "top", "right", "bottom")


def overruns(box: Box, width: int, height: int) -> list[tuple[int, str]]:
    """How far the box extends past each edge (negative = inside)."""
    return [
        (-box.left, "left"),
        (-box.top, "top"),
        (box.right - width, "right"),
        (box.bottom - height, "bottom"),
    ]


def worst_overrun(box: Box, width: int, height: int) -> tuple[int, str]:
    # max() keeps the first of equal values, so ties resolve left, top, right, bottom
    return max(overruns(box, width, height), key=lambda t: t[0])


@rule(
    id="off-slide",
    category="quality",
    severity="error",
    scope="slide",
    basis="geometry",
    since="0.1.0",
    summary="A text-bearing shape extends more than 0.05 cm beyond the slide",
    rationale=RESEARCH_NICHE,
    severity_notes="advisory for a non-text shape (possible bleed)",
)
def check(deck, cfg):
    tol = cm_emu(cfg.off_slide_tolerance_cm)
    for slide in deck.slides:
        for s in slide.shapes:
            if s.box is None:
                continue
            amount, side = worst_overrun(s.box, deck.width, deck.height)
            if amount <= tol:
                continue
            text = is_text_bearing(s)
            msg = f"runs {fmt_cm(amount)} cm past the {side} edge"
            if not text:
                msg += " (non-text shape: possible bleed)"
            yield check.finding(
                slide.index,
                s,
                msg,
                measured=cm(amount),
                threshold=round2(cfg.off_slide_tolerance_cm),
                severity="error" if text else "advisory",
            )
