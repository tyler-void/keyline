import json

import pytest

from keyline.findings import Finding, exit_code, sort_findings, summary_line, to_human, to_json
from keyline.registry import RuleSpec

KEYS = [
    "rule",
    "category",
    "severity",
    "slide",
    "shape_id",
    "shape_name",
    "message",
    "measured",
    "threshold",
]


def f(rule="edge-margin", slide=2, sid=5, sev="warning", msg="m"):
    return Finding(rule, "quality", sev, slide, sid, None, msg, 1.2, 1.27)


def test_keys_in_contract_order():
    data = json.loads(to_json([f()]))
    assert list(data[0]) == KEYS


def test_sort_slide_rule_id_null_first_then_message():
    items = [
        f(slide=2, rule="edge-margin", sid=9),
        f(slide=0, rule="font-count", sid=None),
        f(slide=2, rule="dead-band", sid=None, msg="b"),
        f(slide=2, rule="dead-band", sid=None, msg="a"),
        f(slide=2, rule="edge-margin", sid=3),
        f(slide=1, rule="off-slide", sid=1),
    ]
    got = [(x.slide, x.rule, x.shape_id, x.message) for x in sort_findings(items)]
    assert got == [
        (0, "font-count", None, "m"),
        (1, "off-slide", 1, "m"),
        (2, "dead-band", None, "a"),
        (2, "dead-band", None, "b"),
        (2, "edge-margin", 3, "m"),
        (2, "edge-margin", 9, "m"),
    ]


def test_json_is_byte_stable_and_order_independent():
    a = [f(sid=1), f(sid=2, msg="é"), f(slide=0, sid=None)]
    assert to_json(a) == to_json(list(reversed(a)))
    assert "é" in to_json(a)  # ensure_ascii=False
    assert to_json([]) == "[]\n"


def test_exit_codes():
    assert exit_code([]) == 0
    assert exit_code([f(sev="advisory")]) == 0
    assert exit_code([f(sev="advisory"), f(sev="warning")]) == 2
    assert exit_code([f(sev="error")]) == 2


def test_human_output_ends_with_summary():
    text = to_human([f(sev="advisory"), f(sev="error", slide=0, sid=None)])
    lines = text.splitlines()
    assert lines[0].startswith("deck · edge-margin · error")
    assert lines[-1] == "2 findings: 1 error, 0 warning, 1 advisory"
    assert summary_line([]) == "0 findings: 0 error, 0 warning, 0 advisory"


def test_rulespec_validates_fields():
    ok = dict(
        id="x",
        category="slop",
        severity="warning",
        scope="slide",
        basis="geometry",
        since="0.1.0",
        summary="s",
        rationale="L-001",
    )
    RuleSpec(**ok)
    for key, bad in [("category", "style"), ("severity", "info"), ("basis", "render")]:
        with pytest.raises(ValueError):
            RuleSpec(**{**ok, key: bad})


def test_bad_severity_rejected():
    with pytest.raises(ValueError):
        f(sev="info")
