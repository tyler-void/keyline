"""The findings contract (spec §3): fixed keys, fixed order, byte-stable output."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

SEVERITIES = ("error", "warning", "advisory")
FAILING = frozenset({"error", "warning"})

EXIT_CLEAN = 0
EXIT_SCAN_FAILED = 1
EXIT_FINDINGS = 2


@dataclass(frozen=True, slots=True)
class Finding:
    rule: str
    category: str
    severity: str
    slide: int
    shape_id: int | None
    shape_name: str | None
    message: str
    measured: float | int | None
    threshold: float | int | None

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"bad severity {self.severity!r}")

    def to_dict(self) -> dict[str, Any]:
        # Key order is part of the contract.
        return {
            "rule": self.rule,
            "category": self.category,
            "severity": self.severity,
            "slide": self.slide,
            "shape_id": self.shape_id,
            "shape_name": self.shape_name,
            "message": self.message,
            "measured": self.measured,
            "threshold": self.threshold,
        }


def sort_key(f: Finding) -> tuple:
    """(slide, rule, shape_id with null first, message). The message breaks ties (P-13)."""
    sid = (0, 0) if f.shape_id is None else (1, f.shape_id)
    return (f.slide, f.rule, sid, f.message)


def sort_findings(findings: Iterable[Finding]) -> list[Finding]:
    return sorted(findings, key=sort_key)


def to_json(findings: Iterable[Finding]) -> str:
    data = [f.to_dict() for f in sort_findings(findings)]
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def human_line(f: Finding) -> str:
    where = "deck" if f.slide == 0 else f"slide {f.slide}"
    parts = [where, f.rule, f.severity]
    if f.shape_name:
        parts.append(f.shape_name)
    elif f.shape_id is not None:
        parts.append(f"#{f.shape_id}")
    parts.append(f.message)
    return " · ".join(parts)


def summary_line(findings: Iterable[Finding]) -> str:
    items = list(findings)
    counts = {s: 0 for s in SEVERITIES}
    for f in items:
        counts[f.severity] += 1
    noun = "finding" if len(items) == 1 else "findings"
    detail = ", ".join(f"{counts[s]} {s}" for s in SEVERITIES)
    return f"{len(items)} {noun}: {detail}"


def to_human(findings: Iterable[Finding]) -> str:
    items = sort_findings(findings)
    lines = [human_line(f) for f in items]
    lines.append(summary_line(items))
    return "\n".join(lines) + "\n"


def exit_code(findings: Iterable[Finding]) -> int:
    """0 when nothing is at warning or error; advisory findings never fail (spec §3)."""
    return EXIT_FINDINGS if any(f.severity in FAILING for f in findings) else EXIT_CLEAN
