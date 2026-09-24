"""In-process lint entry point used by the CLI, `check`, and tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from keyline import config as config_mod
from keyline.findings import Finding, exit_code, sort_findings
from keyline.model import Deck
from keyline.ooxml.adapter import load_deck
from keyline.registry import all_rules
from keyline.rules import load_all


@dataclass(frozen=True)
class LintResult:
    findings: list[Finding]
    exit_code: int


def lint_deck(deck: Deck, diagnostics: list[Finding], cfg: config_mod.Config) -> list[Finding]:
    load_all()
    out = list(diagnostics)
    for spec in all_rules():
        if spec.check is not None:
            out.extend(spec.check(deck, cfg))
    return sort_findings(out)


def lint_path(path: str | Path, mode: str = "presented") -> LintResult:
    """Raises ScanError (exit 1) when the file cannot be scanned."""
    cfg = config_mod.load(mode)
    deck, diags = load_deck(path)
    findings = lint_deck(deck, diags, cfg)
    return LintResult(findings, exit_code(findings))
