"""Audit 03 FX-13 (B-12 item 7): a pack or voice path that cannot be examined gives one
line and exit 1, like a brief in the same place, never an internal error."""

import os
import shutil
import subprocess
import sys

import pytest

from keyline.packs import resolve
from tests.conftest import FIXTURES

DECK = FIXTURES / "briefs/drift/base.pptx"
PACK_DIR = resolve("swiss").directory


@pytest.mark.skipif(os.name != "posix" or os.geteuid() == 0, reason="needs a non-root POSIX user")
def test_locked_pack_and_voice_paths(tmp_path):
    locked = tmp_path / "locked"
    shutil.copytree(PACK_DIR, locked / "pk", ignore=shutil.ignore_patterns("*.pptx", "src"))
    locked.chmod(0o000)
    try:
        runs = {
            "pack": ["--pack", "./locked/pk", "--voice", "neutral"],
            "voice": ["--pack", "swiss", "--voice", "./locked/pk/voices/neutral.toml"],
        }
        for what, flags in runs.items():
            proc = subprocess.run(
                [sys.executable, "-m", "keyline", "lint", str(DECK), *flags],
                cwd=tmp_path,
                capture_output=True,
            )
            err = proc.stderr.decode()
            assert proc.returncode == 1 and proc.stdout == b"", (what, err)
            assert len(err.splitlines()) == 1 and "internal error" not in err, (what, err)
            assert "cannot be read: Permission denied" in err, (what, err)
    finally:
        locked.chmod(0o755)
