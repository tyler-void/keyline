import json

from tests.acceptance._cli import keyline
from tests.conftest import GOLDEN


def run(deck: str, mode: str):
    proc = keyline("lint", GOLDEN / deck, "--mode", mode, "--json")
    return proc.returncode, json.loads(proc.stdout)


def has(findings, rule, *, slide=None, shape=None, severity=None):
    return [
        f
        for f in findings
        if f["rule"] == rule
        and (slide is None or f["slide"] == slide)
        and (shape is None or f["shape_name"] == shape)
        and (severity is None or f["severity"] == severity)
    ]


FAILING = ("warning", "error")
