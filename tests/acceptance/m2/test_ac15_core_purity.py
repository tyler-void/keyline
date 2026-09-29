"""Spec 002 AC-15 (task T-29): `keyline lint --brief` on a pen-built specimen, in a fresh
interpreter, loads neither python-pptx nor pypdfium2. The A1 half, on the drift base, is
in test_import_boundary.py."""

import json
import subprocess
import sys

import pytest

from tests.conftest import FIXTURES

PACKS = FIXTURES / "packs"
CLI = """
import json, sys
from keyline.cli import main
code = main(["lint", sys.argv[1], "--brief", sys.argv[2]])
print(json.dumps({"exit": code, "loaded": sorted(
    m for m in sys.modules if m.split(".")[0] in ("pptx", "pypdfium2"))}))
"""


@pytest.mark.parametrize(
    "stem",
    [
        "swiss-specimen-presented-neutral",
        "swiss-specimen-presented-night",
        "swiss-specimen-read-field",
    ],
)
def test_lint_with_a_brief_on_a_specimen_loads_neither_pptx_nor_pypdfium2(stem):
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            CLI,
            str(PACKS / f"{stem}.pptx"),
            str(PACKS / f"{stem}.brief.toml"),
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout.strip().splitlines()[-1]) == {"exit": 0, "loaded": []}
