"""The README's pen example runs from the repository root as written, and the deck it
saves passes `check --brief` (T-31)."""

import json
import re
import subprocess
import sys

import pytest

from tests.acceptance._cli import keyline
from tests.conftest import ROOT

pytest.importorskip("pptx")


def test_the_readme_pen_example_runs_and_passes_its_brief(tmp_path):
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    section = readme.split("## The pen", 1)[1]
    (code,) = re.findall(r"```python\n(.*?)```", section.split("\n## ", 1)[0], re.S)
    for name in ("fixtures", "examples"):  # "from the repository root"
        (tmp_path / name).symlink_to(ROOT / name, target_is_directory=True)
    proc = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, capture_output=True)
    assert proc.returncode == 0, proc.stderr.decode()
    brief = tmp_path / "fixtures/briefs/drift/base.brief.toml"
    check = keyline(
        "check", tmp_path / "bonsaihub.pptx", "--brief", brief, "--json", "-o", tmp_path / "r"
    )
    assert check.returncode == 0, check.stderr.decode()
    assert json.loads(check.stdout) == []
