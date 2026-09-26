from __future__ import annotations

from keyline.registry import rule
from keyline.rules._common import RESEARCH_CANON, is_content_slide


@rule(
    id="notes-missing",
    category="quality",
    severity="warning",
    scope="slide",
    basis="structure",
    since="0.1.0",
    summary="A content slide has no speaker notes",
    rationale=RESEARCH_CANON,
    severity_notes="advisory in read mode",
)
def check(deck, cfg):
    severity = "advisory" if cfg.mode == "read" else "warning"
    for slide in deck.slides:
        if is_content_slide(slide) and not slide.has_notes:
            yield check.finding(
                slide.index, None, "content slide has no speaker notes", severity=severity
            )
