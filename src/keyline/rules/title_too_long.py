from __future__ import annotations

from keyline.registry import rule
from keyline.rules._common import RESEARCH_CANON, pick_title, words


@rule(
    id="title-too-long",
    category="quality",
    severity="warning",
    scope="slide",
    basis="text",
    since="0.2.0",
    summary="The title has more words than the mode allows",
    rationale=RESEARCH_CANON,
)
def check(deck, cfg, ctx):
    limit = cfg.as_int("title_words_max")
    for slide in deck.slides:
        if slide.role == "quote":
            continue  # the title of a quote slide is the quote itself
        title = pick_title(slide, cfg)
        if title is None:
            continue
        n = words(title.text)
        if n > limit:
            yield check.finding(
                slide.index,
                title,
                f"title has {n} words (max {limit} in {cfg.mode} mode)",
                measured=n,
                threshold=limit,
            )
