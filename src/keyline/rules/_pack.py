"""Shared helpers for the pack rules (spec 002 §3.4, amendment B-8.8): every value they
check against comes from the resolved system (ctx.pack) and voice (ctx.voice)."""

from __future__ import annotations

from keyline.rules._common import is_text_bearing

PACK_DATA = (
    'research §A measurable canon, style packs with switches, and "editorial" has become '
    "Claude's signature"
)


def voice_label(ctx) -> str:
    """ "swiss (voice neutral)", for messages."""
    return f"{ctx.pack.name} (voice {ctx.voice.name})"


def palette(ctx) -> set[str]:
    return set(ctx.voice.palette.values())


def is_accent_element(shape, accents: set[str]) -> bool:
    """A text-bearing shape with an inked run in an accent colour, or a shape whose solid
    fill is an accent colour; counted once per shape (§3.4)."""
    if shape.fill_rgb and shape.fill_rgb.upper() in accents:
        return True
    return is_text_bearing(shape) and any(
        r.has_ink and r.color and r.color.upper() in accents for r in shape.runs
    )
