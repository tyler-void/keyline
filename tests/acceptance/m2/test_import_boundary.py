"""Plan 002 §1: lint, the rules, the OOXML reader, briefs, numeric tokens, colour spaces
and packs never import python-pptx, pypdfium2, the pen or the render module. Checked in a
fresh interpreter that imports them all and lints a deck against a brief (the A1 half of
AC-15; A2 repeats it on the specimen)."""

import json
import subprocess
import sys

from tests.conftest import FIXTURES

SCRIPT = """
import json, sys
from pathlib import Path
import keyline.lint, keyline.rules, keyline.brief, keyline.briefcheck, keyline.numtokens
import keyline.colorspace, keyline.packs, keyline.packs.voices, keyline.validate
from keyline.brief import load
from keyline.context import LintContext
from keyline.lint import lint_path
from keyline.rules import load_all
load_all()
brief = load(Path(sys.argv[2]))
ctx = LintContext(brief.pack, brief.voice, brief, brief.evidence)
result = lint_path(sys.argv[1], brief.mode, ctx)
banned = ("pptx", "pypdfium2", "keyline.pen", "keyline.render")
print(json.dumps({
    "loaded": sorted(m for m in sys.modules if m.split(".")[0] in banned[:2] or m in banned),
    "exit": result.exit_code,
}))
"""

CLI = """
import json, sys
from keyline.cli import main
code = main(["lint", sys.argv[1], "--brief", sys.argv[2]])
print(json.dumps({"exit": code, "loaded": sorted(
    m for m in sys.modules if m.split(".")[0] in ("pptx", "pypdfium2"))}))
"""


def _run(script):
    deck = FIXTURES / "briefs/drift/base.pptx"
    brief = FIXTURES / "briefs/drift/base.brief.toml"
    proc = subprocess.run(
        [sys.executable, "-c", script, str(deck), str(brief)], capture_output=True, text=True
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_the_lint_core_imports_no_pen_render_or_rasterizer():
    assert _run(SCRIPT) == {"loaded": [], "exit": 0}


def test_keyline_lint_with_a_brief_loads_neither_pptx_nor_pypdfium2():
    assert _run(CLI) == {"exit": 0, "loaded": []}
