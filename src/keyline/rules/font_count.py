from __future__ import annotations

from keyline.registry import rule
from keyline.rules._common import RESEARCH_CANON

# A-8: one trailing weight or width token is stripped, so "Calibri Light" is Calibri.
STYLE_TOKENS = frozenset(
    [
        "thin",
        "extralight",
        "ultralight",
        "light",
        "regular",
        "book",
        "medium",
        "semibold",
        "demibold",
        "bold",
        "extrabold",
        "ultrabold",
        "black",
        "heavy",
        "condensed",
        "narrow",
    ]
)


def family(name: str) -> str:
    folded = name.casefold().strip()
    head, _, last = folded.rpartition(" ")
    return head if head and last in STYLE_TOKENS else folded


@rule(
    id="font-count",
    category="quality",
    severity="warning",
    scope="deck",
    basis="text",
    since="0.1.0",
    summary="The deck uses more font families than the limit",
    rationale=RESEARCH_CANON,
)
def check(deck, cfg):
    names: dict[str, str] = {}  # family -> a representative typeface name
    for slide in deck.slides:
        for shape in slide.shapes:
            for run in shape.runs:
                if not run.has_ink or run.font is None:
                    continue
                key = family(run.font)
                if key not in names or run.font < names[key]:
                    names[key] = run.font
    limit = cfg.as_int("font_family_max")
    if len(names) > limit:
        listed = ", ".join(names[k] for k in sorted(names))
        yield check.finding(
            0,
            None,
            f"{len(names)} font families: {listed} (max {limit})",
            measured=len(names),
            threshold=limit,
        )
