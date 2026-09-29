"""The deck against its brief (spec 002 §4.5): six rules with `requires = "brief"` that run
in `lint` and `check` when a brief is given. Slide-level findings pair deck and brief
slides by index, over the common prefix only.
"""

from __future__ import annotations

import unicodedata

from keyline.numtokens import slide_texts, tokens
from keyline.registry import rule
from keyline.rules._common import RESEARCH_TELLS, is_text_bearing, line_kind, pick_title


def _collapse(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).split())


def _inked(shape) -> str:
    return "\n".join("".join(r.text for r in p.runs if not r.hidden) for p in shape.paragraphs)


def _pairs(deck, brief):
    return zip(deck.slides, brief.slides, strict=False)  # the common prefix (§4.5)


def _fields(**kw):
    return dict(category="quality", requires="brief", since="0.2.0", rationale=RESEARCH_TELLS, **kw)


@rule(
    id="brief-slide-count",
    severity="error",
    scope="deck",
    basis="structure",
    summary="The deck's slide count differs from the brief's",
    **_fields(),
)
def slide_count(deck, cfg, ctx):
    have, want = len(deck.slides), len(ctx.brief.slides)
    if have != want:
        yield slide_count.finding(
            0, None, f"deck has {have} slides, brief has {want}", measured=have, threshold=want
        )


@rule(
    id="brief-role",
    severity="warning",
    scope="slide",
    basis="structure",
    summary="A slide's role differs from its brief slide's role, or the slide has no role",
    **_fields(),
)
def role(deck, cfg, ctx):
    for slide, want in _pairs(deck, ctx.brief):
        if slide.role is None:
            yield role.finding(slide.index, None, f"slide has no role; brief says {want.role}")
        elif slide.role != want.role:
            yield role.finding(slide.index, None, f"role {slide.role}; brief says {want.role}")


@rule(
    id="brief-headline",
    severity="warning",
    scope="slide",
    basis="text",
    summary="A slide's title text differs from its brief headline",
    **_fields(),
)
def headline(deck, cfg, ctx):
    for slide, want in _pairs(deck, ctx.brief):
        title = pick_title(slide, cfg)
        have = _collapse(_inked(title)) if title is not None else ""
        if have != _collapse(want.headline):
            shown = f"{have!r}" if have else "no title"
            yield headline.finding(
                slide.index, title, f"title is {shown}; brief says {_collapse(want.headline)!r}"
            )


@rule(
    id="unsourced-number",
    severity="warning",
    scope="slide",
    basis="text",
    summary="A significant number on a slide is not in that slide's brief evidence",
    **_fields(),
)
def unsourced(deck, cfg, ctx):
    entries = ctx.brief.evidence.entries
    for slide, want in _pairs(deck, ctx.brief):
        allowed = set().union(*(entries[i].tokens() for i in want.evidence))
        seen = set()
        for shape, text in slide_texts(slide, cfg):
            for token, significant in tokens(text):
                if significant and token not in allowed and token not in seen:
                    seen.add(token)
                    ids = ", ".join(want.evidence) or "none"
                    yield unsourced.finding(
                        slide.index, shape, f"{token} is not in this slide's evidence ({ids})"
                    )


@rule(
    id="source-missing",
    severity="warning",
    scope="slide",
    basis="structure",
    summary="A slide that shows its brief evidence has no source line",
    **_fields(),
)
def source_missing(deck, cfg, ctx):
    for slide, want in _pairs(deck, ctx.brief):
        if not want.evidence:
            continue
        if any(
            line_kind(p, cfg) == "source"
            for s in slide.shapes
            if is_text_bearing(s)
            for p in s.paragraphs
        ):
            continue
        shows_number = any(
            sig for _shape, text in slide_texts(slide, cfg) for _t, sig in tokens(text)
        )
        has_frame = any(
            s.kind in ("graphicFrame:chart", "graphicFrame:table") for s in slide.shapes
        )
        if shows_number or has_frame:
            what = "a chart or table" if has_frame and not shows_number else "numbers"
            yield source_missing.finding(
                slide.index, None, f"slide shows {what} from its evidence but has no source line"
            )


@rule(
    id="fiction-undisclosed",
    severity="warning",
    scope="deck",
    basis="structure",
    summary="A fictional product's disclosure is on neither the first nor the last slide",
    **_fields(),
)
def fiction_undisclosed(deck, cfg, ctx):
    product = ctx.brief.evidence.product
    if not product.fictional:
        return
    needle = _collapse(product.disclosure)
    ends = [deck.slides[0], deck.slides[-1]] if deck.slides else []
    for slide in ends:
        text = _collapse("\n".join(_inked(s) for s in slide.shapes))
        if needle in text:
            return
    yield fiction_undisclosed.finding(
        0, None, "the fictional-product disclosure is on neither the first nor the last slide"
    )
