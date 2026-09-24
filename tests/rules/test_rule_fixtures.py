"""Every rule's positive and negative decks (constitution VI), driven by expect.toml."""

import tomllib

import pytest

from keyline.lint import lint_path
from tests.conftest import RULES

CASES = tomllib.loads((RULES / "expect.toml").read_text("utf-8")).get("case", [])
FAILING = ("error", "warning")


def _parse(spec: str) -> tuple[str, str | None, str | None]:
    rule, _, rest = spec.partition("@")
    shape, _, sev = rest.partition(":")
    return rule, (shape or None), (sev or None)


def _matches(f, rule, shape, sev):
    if f.rule != rule:
        return False
    if shape == "-" and f.shape_name is not None:
        return False
    if shape not in (None, "-") and f.shape_name != shape:
        return False
    return sev is None or f.severity == sev


@pytest.mark.parametrize(
    "case", CASES, ids=[f"{c['deck']}[{c.get('mode', 'presented')}]" for c in CASES]
)
def test_rule_fixture(case):
    result = lint_path(RULES / case["deck"], case.get("mode", "presented"))
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


def test_every_rule_has_positive_and_negative_fixture():
    from keyline.registry import all_rules
    from keyline.rules import load_all

    load_all()
    for spec in all_rules():
        if spec.check is None:
            continue
        pos = [c for c in CASES if any(_parse(m)[0] == spec.id for m in c.get("must", []))]
        neg = [c for c in CASES if any(_parse(m)[0] == spec.id for m in c.get("must_not", []))]
        assert pos and neg, f"{spec.id} needs a positive and a negative fixture"
