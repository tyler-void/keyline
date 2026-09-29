"""Audit 02 FX-4 (amendment B-15): OfficeCLI's error envelope becomes one finding that
carries its message; an officecli that cannot start counts as absent, for check, render
and doctor."""

import json
import os
import stat
import subprocess

import pytest

from keyline import officecli
from keyline import validate as validate_mod
from tests.acceptance._cli import keyline
from tests.conftest import GOLDEN

ENVELOPE = json.dumps(
    {
        "success": False,
        "error": {
            "error": "Cannot open {name}: File contains corrupted data.",
            "code": "corrupt_file",
            "suggestion": "Verify the file is a valid .docx/.xlsx/.pptx (e.g. unzip -t).",
        },
    }
)
BROKEN_NODE = "env: 'node': No such file or directory"


def test_the_envelope_parses_as_one_error():
    text = ENVELOPE.replace("{name}", "x.pptx")
    assert validate_mod.parse(text) == [
        ("Cannot open x.pptx: File contains corrupted data.", "", "")
    ]


def test_the_envelope_finding_names_the_users_deck(monkeypatch):
    def fake_run(cmd, **kw):
        if cmd[1] == "validate":  # OfficeCLI names the file it was given: the private copy
            copy = os.path.basename(cmd[2])
            return subprocess.CompletedProcess(cmd, 1, ENVELOPE.replace("{name}", copy), "")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(validate_mod.shutil, "which", lambda name: "/usr/bin/officecli")
    monkeypatch.setattr(officecli.shutil, "which", lambda name: "/usr/bin/officecli")
    monkeypatch.setattr(validate_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(officecli.subprocess, "run", fake_run)
    (f,) = validate_mod.validate(GOLDEN / "kpi-recipe.pptx")
    assert (f.rule, f.slide) == ("ooxml-invalid", 0)
    assert f.message == "Cannot open kpi-recipe.pptx: File contains corrupted data."


@pytest.mark.officecli
def test_real_officecli_on_a_file_it_cannot_open(tmp_path):
    broken = tmp_path / "broken.pptx"
    broken.write_text("not a zip")
    (f,) = validate_mod.validate(broken)
    assert f.message.startswith("Cannot open broken.pptx: ")


def _broken_officecli(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    exe = bin_dir / "officecli"
    exe.write_text(f'#!/bin/sh\necho "{BROKEN_NODE}" >&2\nexit 127\n')
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    return dict(os.environ, PATH=str(bin_dir))


@pytest.mark.skipif(os.name != "posix", reason="a shell-script stand-in")
def test_an_officecli_that_cannot_start_counts_as_absent(tmp_path):
    env = _broken_officecli(tmp_path)
    clean = GOLDEN / "editorial-fixed.pptx"
    proc = keyline("check", clean, "--mode", "read", "-o", tmp_path / "out", env=env)
    err = proc.stderr.decode()
    assert proc.returncode == 0  # the exit code does not change
    assert f"validate: skipped (officecli could not run: {BROKEN_NODE})" in err
    assert f"render: skipped (officecli could not run: {BROKEN_NODE}; or install LibreOffice" in err
    data = json.loads(keyline("doctor", "--json", env=env).stdout)
    by = {c["check"]: c for c in data["checks"]}
    assert by["validator"]["token"] == "NO_VALIDATOR"
    assert BROKEN_NODE in by["validator"]["detail"]
    assert by["render"]["token"] == "NO_RENDERER"


def test_status_reports_why(monkeypatch):
    monkeypatch.setattr(officecli.shutil, "which", lambda name: None)
    assert officecli.status() == (False, "officecli is not installed")
    monkeypatch.setattr(officecli.shutil, "which", lambda name: "/nonexistent/officecli")
    ok, reason = officecli.status()
    assert not ok and reason.startswith("officecli could not run: ")
