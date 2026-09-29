"""Spec 002 AC-14b: `check` runs `officecli validate` after lint when OfficeCLI is present;
each schema error is one `ooxml-invalid` finding; --no-validate skips it; without
OfficeCLI it says so and the exit code does not change; lint never validates."""

import json
import os
import subprocess
import sys

import pytest

from keyline import validate as validate_mod
from tests.acceptance._cli import keyline
from tests.conftest import FIXTURES, GOLDEN, ROOT

BOGUS = FIXTURES / "validate/editorial-bogus.pptx"
MESSAGE = (
    "/ppt/slides/slide1.xml /p:sld[1]/p:cSld[1]: [Schema] The element has invalid child "
    "element 'http://schemas.openxmlformats.org/presentationml/2006/main:bogus'."
)


def _invalid(proc):
    return [f for f in json.loads(proc.stdout) if f["rule"] == "ooxml-invalid"]


@pytest.mark.officecli
def test_each_schema_error_is_one_finding(tmp_path):
    proc = keyline("check", BOGUS, "-o", tmp_path, "--json", "--engine", "officecli")
    (f,) = _invalid(proc)
    assert (f["slide"], f["severity"], f["message"]) == (1, "warning", MESSAGE)
    assert "validate: 1 schema error(s)" in proc.stderr.decode()


@pytest.mark.officecli
def test_a_valid_deck_passes(tmp_path):
    proc = keyline("check", GOLDEN / "editorial.pptx", "-o", tmp_path, "--json")
    assert _invalid(proc) == [] and "validate: passed" in proc.stderr.decode()


@pytest.mark.officecli
def test_no_validate_turns_the_step_off(tmp_path):
    proc = keyline("check", BOGUS, "-o", tmp_path, "--json", "--no-validate")
    assert _invalid(proc) == []
    assert "validate: skipped (--no-validate)" in proc.stderr.decode()


def test_without_officecli_it_is_skipped_and_the_exit_code_stays(tmp_path):
    env = dict(os.environ, PATH=str(tmp_path))
    proc = keyline("check", BOGUS, "-o", tmp_path / "out", "--json", env=env)
    lint = keyline("lint", BOGUS, "--json")
    assert "validate: skipped (officecli is not installed)" in proc.stderr.decode()
    assert proc.returncode == lint.returncode
    assert json.loads(proc.stdout) == json.loads(lint.stdout)


def test_lint_never_validates():
    assert _invalid(keyline("lint", BOGUS, "--json")) == []


VALID = '{"success": true, "data": "Validation passed: no errors found."}'
TWO = json.dumps(
    {
        "success": False,
        "warnings": [
            {"message": "Found 2 validation error(s):", "code": "warning"},
            {"message": "[Schema] first", "code": "warning"},
            {"message": "Path: /p:sld[1]", "code": "warning"},
            {"message": "Part: /ppt/slides/slide2.xml", "code": "warning"},
            {"message": "[Schema] second", "code": "warning"},
            {"message": "Path: /a:theme[1]", "code": "warning"},
            {"message": "Part: /ppt/theme/theme1.xml", "code": "warning"},
        ],
    }
)


def test_parse_the_observed_shapes():
    assert validate_mod.parse(VALID) == []
    assert validate_mod.parse(TWO) == [
        ("[Schema] first", "/p:sld[1]", "/ppt/slides/slide2.xml"),
        ("[Schema] second", "/a:theme[1]", "/ppt/theme/theme1.xml"),
    ]
    for unreadable in ("Found 1 validation error(s):", "[]", '{"success": false}', ""):
        assert validate_mod.parse(unreadable) is None


def test_unreadable_output_gives_one_finding_with_its_first_line(monkeypatch):
    out = "Segmentation fault\nmore"

    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 139, out, "")

    monkeypatch.setattr(validate_mod.shutil, "which", lambda name: "/usr/bin/officecli")
    monkeypatch.setattr(validate_mod.subprocess, "run", fake_run)
    (f,) = validate_mod.validate(BOGUS)
    assert (f.rule, f.slide) == ("ooxml-invalid", 0)
    assert f.message == "officecli validate output not understood: Segmentation fault"


def test_parts_map_to_the_slide_position_in_the_deck(monkeypatch):
    monkeypatch.setattr(validate_mod.shutil, "which", lambda name: "/usr/bin/officecli")
    monkeypatch.setattr(
        validate_mod.subprocess,
        "run",
        lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, TWO, ""),
    )
    slides = [f.slide for f in validate_mod.validate(GOLDEN / "kpi-recipe.pptx")]
    assert slides == [2, 0]  # the theme is not a slide


def test_the_bogus_deck_rebuilds_byte_identically(tmp_path):
    script = ROOT / "fixtures/validate/src/build_bogus.py"
    subprocess.run([sys.executable, script, tmp_path], check=True, capture_output=True)
    assert (tmp_path / "editorial-bogus.pptx").read_bytes() == BOGUS.read_bytes()
