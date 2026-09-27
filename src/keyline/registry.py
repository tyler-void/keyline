"""The versioned rule registry (spec 001 §4; spec 002 §3.4 adds `requires`)."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from keyline.findings import SEVERITIES, Finding

if TYPE_CHECKING:
    from keyline.config import Config
    from keyline.context import LintContext
    from keyline.model import Deck, Shape

CATEGORIES = ("slop", "quality")
SCOPES = ("slide", "deck")
BASES = ("geometry", "text", "color", "structure")
REQUIRES = ("none", "pack", "brief", "officecli")

# check(deck, cfg, ctx); spec 001 rules take (deck, cfg) and are adapted in RuleSpec.run
Check = Callable[..., Iterable[Finding]]


@dataclass(frozen=True)
class RuleSpec:
    id: str
    category: str
    severity: str
    scope: str
    basis: str
    since: str
    summary: str
    rationale: str
    severity_notes: str = ""
    requires: str = "none"
    check: Check | None = field(default=None, compare=False, repr=False)

    def __post_init__(self) -> None:
        if self.category not in CATEGORIES:
            raise ValueError(f"{self.id}: bad category {self.category!r}")
        if self.severity not in SEVERITIES:
            raise ValueError(f"{self.id}: bad severity {self.severity!r}")
        if self.scope not in SCOPES:
            raise ValueError(f"{self.id}: bad scope {self.scope!r}")
        if self.basis not in BASES:
            raise ValueError(f"{self.id}: bad basis {self.basis!r}")
        if self.requires not in REQUIRES:
            raise ValueError(f"{self.id}: bad requires {self.requires!r}")

    def run(self, deck: Deck, cfg: Config, ctx: LintContext) -> Iterable[Finding]:
        """Call the check with the context when it takes one. Spec 001 checks take
        (deck, cfg); keeping them callable leaves every spec 001 test unchanged."""
        if self.check is None:
            return ()
        if _positional_arity(self.check) >= 3:
            return self.check(deck, cfg, ctx)
        return self.check(deck, cfg)

    def finding(
        self,
        slide: int,
        shape: Shape | None,
        message: str,
        measured: float | int | None = None,
        threshold: float | int | None = None,
        severity: str | None = None,
    ) -> Finding:
        return Finding(
            rule=self.id,
            category=self.category,
            severity=severity or self.severity,
            slide=slide,
            shape_id=None if shape is None else shape.id,
            shape_name=None if shape is None else shape.name,
            message=message,
            measured=measured,
            threshold=threshold,
        )

    def describe(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "severity": self.severity,
            "scope": self.scope,
            "basis": self.basis,
            "requires": self.requires,
            "since": self.since,
            "summary": self.summary,
            "rationale": self.rationale,
            "severity_notes": self.severity_notes,
        }


def _positional_arity(fn: Callable) -> int:
    params = inspect.signature(fn).parameters.values()
    if any(p.kind is p.VAR_POSITIONAL for p in params):
        return 3
    return sum(p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) for p in params)


_REGISTRY: dict[str, RuleSpec] = {}


def register(spec: RuleSpec) -> RuleSpec:
    if spec.id in _REGISTRY:
        raise ValueError(f"duplicate rule id {spec.id!r}")
    _REGISTRY[spec.id] = spec
    return spec


def rule(**fields: Any) -> Callable[[Check], RuleSpec]:
    """Decorator: `@rule(id=..., ...)` on a `check(deck, cfg, ctx)` function (or a spec 001
    `check(deck, cfg)`)."""

    def wrap(fn: Check) -> RuleSpec:
        return register(RuleSpec(check=fn, **fields))

    return wrap


def get(rule_id: str) -> RuleSpec:
    return _REGISTRY[rule_id]


def all_rules() -> list[RuleSpec]:
    return [_REGISTRY[k] for k in sorted(_REGISTRY)]
