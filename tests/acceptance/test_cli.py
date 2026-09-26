import json

from tests.acceptance._cli import keyline
from tests.conftest import GOLDEN

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


def test_lint_json_contract():
    proc = keyline("lint", GOLDEN / "kpi-recipe.pptx", "--json")
    assert proc.returncode == 2
    data = json.loads(proc.stdout)
    assert data and all(list(f) == KEYS for f in data)
    keys = [(f["slide"], f["rule"], (f["shape_id"] is not None, f["shape_id"] or 0)) for f in data]
    assert keys == sorted(keys)
    err = proc.stderr.decode().splitlines()
    assert err[-1].startswith(f"{len(data)} findings:")


def test_lint_without_json_writes_nothing_to_stdout():
    proc = keyline("lint", GOLDEN / "editorial.pptx", "--mode", "read")
    assert proc.returncode == 2 and proc.stdout == b""


def test_rules_listing():
    proc = keyline("rules", "--json")
    assert proc.returncode == 0
    ids = [r["id"] for r in json.loads(proc.stdout)]
    assert ids == sorted(ids)
    assert set(ids) == {
        "adapter-unresolved",
        "body-too-small",
        "box-overlap",
        "dead-band",
        "edge-margin",
        "equal-card-row",
        "font-count",
        "notes-missing",
        "off-slide",
        "text-contrast",
        "title-not-dominant",
        "title-underline",
        "unsupported-content",
    }
    for r in json.loads(proc.stdout):
        assert r["since"] == "0.1.0"
    human = keyline("rules")
    assert human.returncode == 0 and b"equal-card-row" in human.stdout


def test_no_command_prints_help_and_fails():
    proc = keyline()
    assert proc.returncode == 1 and b"usage" in proc.stderr
