"""Shared driver for the brief fixtures (fixtures/briefs/expect.toml)."""

import json
import tomllib

from tests.acceptance._cli import keyline
from tests.conftest import FIXTURES

BRIEFS = FIXTURES / "briefs"
CASES = tomllib.loads((BRIEFS / "expect.toml").read_text("utf-8"))["case"]


def run_case(case):
    path = BRIEFS / case["file"]
    proc = keyline("brief", path, "--json")
    err = proc.stderr.decode()
    assert proc.returncode == case["exit"], err
    assert "Traceback" not in err
    if case["exit"] == 1:
        assert proc.stdout == b""
        assert err == f"keyline: {path.name}: {case['error']}\n"
        return
    data = json.loads(proc.stdout)
    got = [(f["rule"], f["slide"], f["severity"]) for f in data["findings"]]
    for spec in case.get("must", []):
        rule, _, rest = spec.partition("@")
        slide, _, severity = rest.partition(":")
        assert (rule, int(slide), severity) in got, (spec, got)
    for rule in case.get("absent", []):
        assert all(g[0] != rule for g in got), (rule, got)
