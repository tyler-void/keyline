"""What a lint run knows besides the deck: the resolved pack (system) and voice, the brief
and the evidence (spec 002 §3.4, amendment B-8.8). Each may be None. Rules receive it as
their third argument."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LintContext:
    pack: Any = None  # keyline.packs.Pack (the system)
    voice: Any = None  # keyline.packs.voices.Voice
    brief: Any = None  # keyline.brief.Brief
    evidence: Any = None  # keyline.brief.EvidenceSet

    def satisfies(self, requires: str) -> bool:
        """Whether a rule with this `requires` runs in lint. `officecli` rules only run in
        `check`'s validate step, never here (plan Q-12)."""
        if requires == "none":
            return True
        if requires == "pack":  # B-8.8: pack rules resolve the voice's values
            return self.pack is not None and self.voice is not None
        if requires == "brief":
            return self.brief is not None
        return False

    def accepted(self) -> dict[str, str]:
        """Rule id -> reason, from the pack's and the voice's `accepted` (plan Q-24, Q-31)."""
        out: dict[str, str] = {}
        for source in (self.pack, self.voice):
            for rule_id, reason in getattr(source, "accepted", ()) or ():
                out.setdefault(rule_id, reason)
        return out


EMPTY = LintContext()
