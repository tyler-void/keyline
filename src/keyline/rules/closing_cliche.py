from __future__ import annotations

import re
import unicodedata

from keyline.registry import rule
from keyline.rules._common import RESEARCH_TELLS, pick_title

_STRIP = ".!?…:;-–— "


def normalise(text: str) -> str:
    """NFC, casefold, whitespace collapsed, `.!?…:;-–—` and spaces stripped at both ends."""
    folded = unicodedata.normalize("NFC", text).casefold()
    return re.sub(r"\s+", " ", folded).strip(_STRIP)


@rule(
    id="closing-cliche",
    category="slop",
    severity="warning",
    scope="slide",
    basis="text",
    since="0.2.0",
    summary='The last slide is a "Thank you" or "Questions?" slide',
    rationale=RESEARCH_TELLS,
)
def check(deck, cfg, ctx):
    if not deck.slides:
        return
    last = deck.slides[-1]
    title = pick_title(last, cfg)
    if title is None:
        return
    text = normalise(title.text)
    if text in cfg.closing_cliches:
        yield check.finding(last.index, title, f'the last slide says "{text}"')
