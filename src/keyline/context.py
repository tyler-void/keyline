"""What a lint run knows besides the deck: the resolved pack, brief and evidence
(spec 002 §3.4). Each may be None. Rules receive it as their third argument."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LintContext:
    pack: Any = None  # keyline.packs.Pack
    brief: Any = None  # keyline.brief.Brief
    evidence: Any = None  # keyline.brief.EvidenceSet

    def satisfies(self, requires: str) -> bool:
        """Whether a rule with this `requires` runs in lint. `officecli` rules only run in
        `check`'s validate step, never here (plan Q-12)."""
        if requires == "none":
            return True
        if requires == "pack":
            return self.pack is not None
        if requires == "brief":
            return self.brief is not None
        return False


EMPTY = LintContext()
