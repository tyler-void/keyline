"""Every rule's positive and negative decks (constitution VI), driven by expect.toml.

A case may name a `pack` and, since amendment B-8.8, must then name its `voice` (plan
Q-36), or a `brief` (a path relative to fixtures/rules), which supplies mode, pack and
voice; the harness passes them to lint (spec 002 AC-2)."""

import tomllib

import pytest

from keyline.context import EMPTY, LintContext
from keyline.lint import lint_path
from tests.conftest import RULES

CASES = tomllib.loads((RULES / "expect.toml").read_text("utf-8")).get("case", [])
FAILING = ("error", "warning")


def _parse(spec: str) -> tuple[str, str | None, str | None]:
    rule, _, rest = spec.partition("@")
    shape, _, sev = rest.partition(":")
    return rule, (shape or None), (sev or None)


def _context(case) -> LintContext:
    if "brief" in case:
        from keyline.brief import load

        brief = load(RULES / case["brief"])
        assert case.get("mode", brief.mode) == brief.mode, "the brief decides the mode"
        return LintContext(brief.pack, brief.voice, brief, brief.evidence)
    if "pack" not in case:
        assert "voice" not in case, "a voice needs a pack"
        return EMPTY
    from keyline.packs import resolve

    assert "voice" in case, f"{case['deck']}: a case with a pack needs a voice (Q-36)"
    pack = resolve(case["pack"])
    return LintContext(pack=pack, voice=pack.voice(case["voice"]))


def _matches(f, rule, shape, sev):
    if f.rule != rule:
        return False
    if shape == "-" and f.shape_name is not None:
        return False
    if shape not in (None, "-") and f.shape_name != shape:
        return False
    return sev is None or f.severity == sev


def _id(c):
    voice = f",{c['voice']}" if "voice" in c else ""
    return f"{c['deck']}[{c.get('mode', 'presented')}{voice}]"


@pytest.mark.parametrize("case", CASES, ids=[_id(c) for c in CASES])
def test_rule_fixture(case):
    ctx = _context(case)
    mode = ctx.brief.mode if ctx.brief else case.get("mode", "presented")
    result = lint_path(RULES / case["deck"], mode, ctx)
    for spec in case.get("must", []):
        rule, shape, sev = _parse(spec)
        assert any(_matches(f, rule, shape, sev) for f in result.findings), (
            f"missing {spec}; got {[(f.rule, f.shape_name, f.severity) for f in result.findings]}"
        )
    for spec in case.get("must_not", []):
        rule, shape, _ = _parse(spec)
        bad = [
            f for f in result.findings if f.severity in FAILING and _matches(f, rule, shape, None)
        ]
        assert not bad, f"unexpected {spec}: {[(f.shape_name, f.message) for f in bad]}"
    for spec in case.get("absent", []):
        rule, shape, _ = _parse(spec)
        bad = [f for f in result.findings if _matches(f, rule, shape, None)]
        assert not bad, f"unexpected {spec} (any severity): {[f.message for f in bad]}"


def test_every_rule_has_positive_and_negative_fixture():
    from keyline.registry import all_rules
    from keyline.rules import load_all

    load_all()
    for spec in all_rules():
        if spec.check is None:
            continue
        pos = [c for c in CASES if any(_parse(m)[0] == spec.id for m in c.get("must", []))]
        neg = [
            c
            for c in CASES
            if any(_parse(m)[0] == spec.id for m in c.get("must_not", []) + c.get("absent", []))
        ]
        assert pos and neg, f"{spec.id} needs a positive and a negative fixture"
