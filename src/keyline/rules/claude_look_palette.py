"""Cream paper plus a terracotta accent: the documented "Claude look" (L-007, §3.4)."""

from __future__ import annotations

from fractions import Fraction

from keyline.colorspace import hsl, lab
from keyline.registry import rule
from keyline.rules._common import is_visible
from keyline.units import fmt_pct, round3


def is_cream(rgb: str, cfg) -> bool:
    lightness, chroma, hue = lab(rgb)
    return (
        lightness >= cfg.cream_lightness_min
        and cfg.neutral_chroma_max < chroma <= cfg.cream_chroma_max
        and cfg.cream_hue_min <= hue <= cfg.cream_hue_max
    )


def is_terracotta(rgb: str, cfg) -> bool:
    hue, sat, light = hsl(rgb)
    return (
        cfg.terracotta_hue_min <= hue <= cfg.terracotta_hue_max
        and cfg.terracotta_sat_min <= sat <= cfg.terracotta_sat_max
        and cfg.terracotta_light_min <= light <= cfg.terracotta_light_max
    )


def _colours(deck):
    """Inked run colours, visible solid fills and resolved slide backgrounds, in deck
    order (hidden shapes are already out of the model, A-12)."""
    for slide in deck.slides:
        if slide.background_rgb:
            yield slide.background_rgb
        for shape in slide.shapes:
            if is_visible(shape) and shape.fill_rgb:
                yield shape.fill_rgb
            for run in shape.runs:
                if run.has_ink and run.color:
                    yield run.color


@rule(
    id="claude-look-palette",
    category="slop",
    severity="warning",
    scope="deck",
    basis="color",
    since="0.2.0",
    summary="Cream paper on most slides, with a terracotta accent (the Claude look)",
    rationale="L-007",
    severity_notes="advisory when only the cream paper is present",
)
def check(deck, cfg, ctx):
    if not deck.slides:
        return
    cream = sum(1 for s in deck.slides if s.background_rgb and is_cream(s.background_rgb, cfg))
    ratio = Fraction(cream, len(deck.slides))  # unknown backgrounds count as not cream (Q-25)
    if ratio < cfg.cream_slide_ratio:
        return
    terracotta = next((c for c in _colours(deck) if is_terracotta(c, cfg)), None)
    share = f"{cream} of {len(deck.slides)} slides ({fmt_pct(ratio)}) have a cream background"
    if terracotta is None:
        yield check.finding(
            0,
            None,
            f"{share}; no terracotta accent",
            measured=round3(ratio),
            threshold=round3(cfg.cream_slide_ratio),
            severity="advisory",
        )
    else:
        yield check.finding(
            0,
            None,
            f"{share} and #{terracotta.upper()} is a terracotta accent",
            measured=round3(ratio),
            threshold=round3(cfg.cream_slide_ratio),
        )
