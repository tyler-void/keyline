"""The pen's errors (§6.1). DoesNotFit comes from the estimator (keyline.fit)."""

from __future__ import annotations

from keyline.fit import DoesNotFit


class PenError(ValueError):
    """A token, role, region, style or component the pack does not allow, or a voice the
    pen refuses. The message is one line."""


class EvidenceError(PenError):
    """An evidence id that is not in the deck's evidence."""


__all__ = ["DoesNotFit", "EvidenceError", "PenError"]
