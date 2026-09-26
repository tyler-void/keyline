from __future__ import annotations

from fractions import Fraction

from keyline.registry import rule
from keyline.rules._common import RESEARCH_TELLS, cm_emu, is_text_bearing, pick_title
from keyline.units import fmt_cm, fmt_pct, round3


@rule(
    id="title-underline",
    category="slop",
    severity="warning",
    scope="slide",
    basis="geometry",
    since="0.1.0",
    summary="A short accent bar sits just under the title",
    rationale=RESEARCH_TELLS,
)
def check(deck, cfg):
    content_width = deck.width - 2 * cm_emu(cfg.edge_margin_cm)
    max_h = cm_emu(cfg.underline_max_height_cm)
    max_gap = cm_emu(cfg.underline_max_gap_cm)
    max_dx = cm_emu(cfg.underline_max_left_offset_cm)
    for slide in deck.slides:
        title = pick_title(slide, cfg)
        if title is None or title.box is None:
            continue
        t = title.box
        lo = t.top + Fraction(t.h, 2)  # A-9: from the middle of the title box ...
        hi = t.bottom + max_gap  # ... to 1.0 cm below its bottom
        for s in slide.shapes:
            if s is title or s.kind != "sp" or s.box is None or s.fill == "none":
                continue
            if is_text_bearing(s):
                continue
            b = s.box
            if b.h > max_h or not (lo <= b.top <= hi) or abs(b.left - t.left) > max_dx:
                continue
            ratio = Fraction(b.w) / content_width
            if ratio >= cfg.underline_max_width_ratio:
                continue  # a full-width hairline is structure, not an accent
            yield check.finding(
                slide.index,
                s,
                f"{fmt_cm(b.w)} × {fmt_cm(b.h)} cm bar {fmt_cm(b.top - t.bottom)} cm below "
                f"the title ({fmt_pct(ratio)} of the content width) "
                "reads as an underline accent",
                measured=round3(ratio),
                threshold=round3(cfg.underline_max_width_ratio),
            )
