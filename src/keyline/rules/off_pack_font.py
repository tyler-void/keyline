"""A font family that is not one of the voice's two (spec 002 §3.4, B-8.8)."""

from __future__ import annotations

from keyline.registry import rule
from keyline.rules._pack import PACK_DATA
from keyline.rules.font_count import family

MAX_SLIDES_LISTED = 5


@rule(
    id="off-pack-font",
    category="quality",
    severity="warning",
    scope="deck",
    basis="text",
    requires="pack",
    since="0.2.0",
    summary="A resolved font family is not one of the voice's fonts",
    rationale=PACK_DATA,
)
def check(deck, cfg, ctx):
    allowed = {family(f) for f in ctx.voice.fonts}
    seen: dict[str, tuple[str, list[int]]] = {}  # normalised family -> (spelling, slides)
    for slide in deck.slides:
        for shape in slide.shapes:
            for run in shape.runs:
                if not run.has_ink or not run.font:
                    continue
                key = family(run.font)
                if key in allowed:
                    continue
                spelling, slides = seen.setdefault(key, (run.font, []))
                if not slides or slides[-1] != slide.index:
                    slides.append(slide.index)
    fonts = " and ".join(ctx.voice.fonts)
    for spelling, slides in seen.values():
        listed = ", ".join(str(n) for n in slides[:MAX_SLIDES_LISTED])
        more = " …" if len(slides) > MAX_SLIDES_LISTED else ""
        noun = "slide" if len(slides) == 1 else "slides"
        yield check.finding(
            0,
            None,
            f"{spelling} is not a font of {ctx.pack.name} (voice {ctx.voice.name}: {fonts}); "
            f"{noun} {listed}{more}",
            measured=len(slides),
        )
