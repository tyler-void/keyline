"""Spec 002 §3.4 registry changes: `requires`, the context argument, and the adapter
that keeps spec 001's two-argument checks working (plan §2.1, T-03)."""

import dataclasses

import pytest

from keyline.config import load
from keyline.context import EMPTY, LintContext
from keyline.lint import lint_deck
from keyline.model import Deck
from keyline.registry import RuleSpec, all_rules
from keyline.rules import load_all

BASE = dict(
    id="x",
    category="quality",
    severity="warning",
    scope="deck",
    basis="text",
    since="0.2.0",
    summary="s",
    rationale="L-001",
)


def test_requires_is_validated_and_defaults_to_none():
    assert RuleSpec(**BASE).requires == "none"
    for value in ("none", "pack", "brief", "officecli"):
        RuleSpec(**BASE, requires=value)
    with pytest.raises(ValueError, match="bad requires"):
        RuleSpec(**BASE, requires="render")


def test_spec_001_entries_require_nothing():
    load_all()
    m1 = [s for s in all_rules() if s.since == "0.1.0"]
    assert len(m1) == 13
    assert {s.requires for s in m1} == {"none"}


def test_describe_lists_requires_after_basis():
    keys = list(RuleSpec(**BASE, requires="pack").describe())
    assert keys[keys.index("basis") + 1] == "requires"


def test_run_passes_context_only_to_three_argument_checks():
    seen = []

    def two(deck, cfg):
        seen.append(("two", cfg.mode))
        return []

    def three(deck, cfg, ctx):
        seen.append(("three", ctx))
        return []

    cfg = load("read")
    ctx = LintContext(pack="p")
    list(RuleSpec(**BASE, check=two).run(Deck(1, 1), cfg, ctx))
    list(RuleSpec(**BASE, check=three).run(Deck(1, 1), cfg, ctx))
    assert seen == [("two", "read"), ("three", ctx)]


def test_context_decides_which_rules_run():
    assert EMPTY.satisfies("none")
    assert not EMPTY.satisfies("pack") and not EMPTY.satisfies("brief")
    assert LintContext(pack="p", voice="v").satisfies("pack")
    assert not LintContext(pack="p").satisfies("pack")  # B-8.8: pack rules need a voice
    assert LintContext(brief="b").satisfies("brief")
    assert not LintContext(pack="p", brief="b").satisfies("officecli")  # check-only (Q-12)


def test_lint_skips_rules_whose_requirement_is_missing(monkeypatch):
    from keyline import registry

    load_all()
    calls = []

    def needs_pack(deck, cfg, ctx):
        calls.append(ctx.pack.name)
        return []

    spec = dataclasses.replace(registry.get("font-count"), requires="pack", check=needs_pack)
    monkeypatch.setitem(registry._REGISTRY, "font-count", spec)
    cfg = load()
    lint_deck(Deck(1, 1), [], cfg)
    assert calls == []
    from keyline.packs import resolve

    pack = resolve("swiss")
    lint_deck(Deck(1, 1), [], cfg, LintContext(pack=pack))
    assert calls == []  # B-8.8: no voice, no pack rules
    lint_deck(Deck(1, 1), [], cfg, LintContext(pack=pack, voice=pack.voice("neutral")))
    assert calls == ["swiss"]
