"""The versioned rule registry (spec §4)."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from keyline.findings import SEVERITIES, Finding

if TYPE_CHECKING:
    from keyline.config import Config
    from keyline.model import Deck, Shape

CATEGORIES = ("slop", "quality")
SCOPES = ("slide", "deck")
BASES = ("geometry", "text", "color", "structure")

Check = Callable[["Deck", "Config"], Iterable[Finding]]


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
            "since": self.since,
            "summary": self.summary,
            "rationale": self.rationale,
            "severity_notes": self.severity_notes,
        }


_REGISTRY: dict[str, RuleSpec] = {}


def register(spec: RuleSpec) -> RuleSpec:
    if spec.id in _REGISTRY:
        raise ValueError(f"duplicate rule id {spec.id!r}")
    _REGISTRY[spec.id] = spec
    return spec


def rule(**fields: Any) -> Callable[[Check], RuleSpec]:
    """Decorator: `@rule(id=..., ...)` on a `check(deck, config)` function."""

    def wrap(fn: Check) -> RuleSpec:
        return register(RuleSpec(check=fn, **fields))

    return wrap


def get(rule_id: str) -> RuleSpec:
    return _REGISTRY[rule_id]


def all_rules() -> list[RuleSpec]:
    return [_REGISTRY[k] for k in sorted(_REGISTRY)]
