"""AC-10: kpi-recipe.pptx renders 4 slide PNGs and contact.png (needs OfficeCLI).
The paths without OfficeCLI run everywhere (A-10)."""

import os
import sys
from pathlib import Path

import pytest
from PIL import Image

from keyline.render import COLUMNS, GUTTER, TILE_WIDTH, contact_sheet
from tests.acceptance._cli import keyline
from tests.conftest import GOLDEN

KPI = GOLDEN / "kpi-recipe.pptx"


@pytest.mark.officecli
def test_render_kpi(tmp_path):
    proc = keyline("render", KPI, "-o", tmp_path)
    assert proc.returncode == 0, proc.stderr.decode()
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == ["contact.png", "slide-01.png", "slide-02.png", "slide-03.png", "slide-04.png"]
    assert b"L-002" in proc.stderr
    with Image.open(tmp_path / "contact.png") as im:
        assert im.width == GUTTER + COLUMNS * (TILE_WIDTH + GUTTER)


@pytest.mark.officecli
def test_check_with_render_keeps_lint_exit_code(tmp_path):
    proc = keyline("check", KPI, "-o", tmp_path, "--json")
    assert proc.returncode == 2
    assert b"slide-04.png" in proc.stderr and proc.stdout.startswith(b"[")


def _no_officecli_env(tmp_path):
    env = dict(os.environ)
    env["PATH"] = str(tmp_path)  # an empty directory: officecli cannot be found
    return env


def test_render_without_officecli_exits_1(tmp_path):
    proc = keyline("render", KPI, "-o", tmp_path / "out", env=_no_officecli_env(tmp_path))
    assert proc.returncode == 1
    err = proc.stderr.decode()
    assert "npm install -g @officecli/officecli" in err and "L-002" in err


def test_check_without_officecli_keeps_lint_exit_code(tmp_path):
    env = _no_officecli_env(tmp_path)
    proc = keyline("check", KPI, "-o", tmp_path / "out", env=env)
    assert proc.returncode == 2  # lint's code (A-10)
    assert "render: skipped (officecli is not installed" in proc.stderr.decode()
    fixed = GOLDEN / "editorial-fixed.pptx"
    clean = keyline("check", fixed, "--mode", "read", "-o", tmp_path / "o2", env=env)
    assert clean.returncode == 0


def test_require_render_turns_failure_into_exit_1(tmp_path):
    proc = keyline(
        "check", KPI, "-o", tmp_path / "out", "--require-render", env=_no_officecli_env(tmp_path)
    )
    assert proc.returncode == 1


def test_contact_sheet_grid(tmp_path):
    pngs = []
    for i in range(4):
        p = tmp_path / f"slide-{i + 1:02d}.png"
        Image.new("RGB", (1280, 720), (i * 40, 0, 0)).save(p)
        pngs.append(p)
    out = contact_sheet(pngs, tmp_path / "contact.png")
    with Image.open(out) as im:
        assert im.width == GUTTER + 3 * (TILE_WIDTH + GUTTER)
        tile_h = 270 + 20
        assert im.height == GUTTER + 2 * (tile_h + GUTTER)


def test_python_is_absolute_so_empty_path_still_runs():
    assert Path(sys.executable).is_absolute()
