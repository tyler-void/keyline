"""In-process lint entry point used by the CLI, `check`, and tests."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from keyline import config as config_mod
from keyline import progress
from keyline.context import EMPTY, LintContext
from keyline.findings import Finding, exit_code, sort_findings
from keyline.model import Deck
from keyline.ooxml.adapter import load_deck
from keyline.registry import all_rules
from keyline.rules import load_all


@dataclass(frozen=True)
class LintResult:
    findings: list[Finding]
    exit_code: int


def lint_deck(
    deck: Deck,
    diagnostics: list[Finding],
    cfg: config_mod.Config,
    ctx: LintContext = EMPTY,
) -> list[Finding]:
    """Run every registered rule whose `requires` the context satisfies. Findings of a rule
    the pack or voice lists in `accepted` are downgraded to advisory (plan Q-24, Q-31)."""
    load_all()
    out = list(diagnostics)
    for spec in all_rules():
        if spec.check is None or not ctx.satisfies(spec.requires):
            continue
        progress.reading.set(f"rule {spec.id}")
        out.extend(spec.run(deck, cfg, ctx))
    accepted = ctx.accepted()
    if accepted:
        out = [_accept(f, accepted[f.rule]) if f.rule in accepted else f for f in out]
    return sort_findings(out)


def _accept(finding: Finding, reason: str) -> Finding:
    if finding.severity == "advisory":
        return finding
    return replace(finding, severity="advisory", message=f"{finding.message} (accepted: {reason})")


def lint_path(path: str | Path, mode: str = "presented", ctx: LintContext = EMPTY) -> LintResult:
    """Raises ScanError (exit 1) when the file cannot be scanned."""
    cfg = config_mod.load(mode)
    deck, diags = load_deck(path)
    findings = lint_deck(deck, diags, cfg, ctx)
    return LintResult(findings, exit_code(findings))
