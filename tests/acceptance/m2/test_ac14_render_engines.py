"""Spec 002 AC-14 (render engines) and B-7 (the LibreOffice version is recorded). The
LibreOffice tests skip where soffice is absent (CI); the no-engine paths run everywhere."""

import os
import shutil
import subprocess

import pytest
from PIL import Image

from keyline import render as render_mod
from tests.acceptance._cli import keyline
from tests.conftest import GOLDEN

KPI = GOLDEN / "kpi-recipe.pptx"
SLIDES = ["contact.png", "slide-01.png", "slide-02.png", "slide-03.png", "slide-04.png"]
needs_lo = pytest.mark.skipif(
    render_mod.find_soffice() is None or render_mod.find_rasterizer() is None,
    reason="LibreOffice and a rasterizer are not installed",
)


def _env_path(path):
    env = dict(os.environ)
    env["PATH"] = str(path)
    return env


@needs_lo
def test_libreoffice_renders_one_png_per_slide_and_a_contact_sheet(tmp_path):
    proc = keyline("render", KPI, "-o", tmp_path, "--engine", "libreoffice")
    err = proc.stderr.decode()
    assert proc.returncode == 0, err
    assert sorted(p.name for p in tmp_path.iterdir()) == SLIDES
    for name in SLIDES[1:]:
        with Image.open(tmp_path / name) as im:
            assert im.width == render_mod.PNG_WIDTH
    assert "L-010" in err and "L-002" not in err  # the engine's own known limits
    assert "render engine: LibreOffice " in err  # B-7: the version it ran on


@needs_lo
def test_auto_picks_libreoffice_when_present(tmp_path):
    proc = keyline("render", KPI, "-o", tmp_path)
    assert proc.returncode == 0 and "render engine: LibreOffice " in proc.stderr.decode()


@needs_lo
def test_pdftoppm_rasterizer(tmp_path, monkeypatch):
    if shutil.which("pdftoppm") is None:
        pytest.skip("pdftoppm is not installed")
    monkeypatch.setattr(render_mod, "_pdfium_available", lambda: False)
    assert render_mod.find_rasterizer() == "pdftoppm"
    result = render_mod.render(KPI, tmp_path, "libreoffice")
    assert result.engine == "libreoffice" and result.version.startswith("LibreOffice ")
    assert len(result.slides) == 4
    for png in result.slides:
        with Image.open(png) as im:
            assert im.width == render_mod.PNG_WIDTH


def _needs_node(exe):
    with open(exe, "rb") as f:
        first = f.readline(200)
    return first.startswith(b"#!") and b"node" in first


@pytest.mark.officecli
def test_auto_falls_back_to_officecli_without_soffice(tmp_path):
    """Audit 02 FX-4: the npm launcher is a node script, so node goes on the PATH too."""
    only = tmp_path / "bin"
    only.mkdir()
    exe = shutil.which("officecli")
    (only / "officecli").symlink_to(exe)
    if _needs_node(exe):
        node = shutil.which("node")
        if node is None:
            pytest.skip("officecli is a node script and node is not on PATH")
        (only / "node").symlink_to(node)
    proc = keyline("render", KPI, "-o", tmp_path / "out", env=_env_path(only))
    assert proc.returncode == 0, proc.stderr.decode()
    assert "L-002" in proc.stderr.decode()


def test_forcing_an_absent_engine_exits_1_with_its_install_hint(tmp_path):
    env = _env_path(tmp_path)  # an empty directory: nothing can be found
    if render_mod.find_soffice() not in (None, shutil.which("soffice")):
        pytest.skip("LibreOffice is installed at a standard path outside PATH")
    lo = keyline("render", KPI, "-o", tmp_path / "a", "--engine", "libreoffice", env=env)
    assert lo.returncode == 1
    assert "libreoffice is not installed; install LibreOffice" in lo.stderr.decode()
    oc = keyline("render", KPI, "-o", tmp_path / "b", "--engine", "officecli", env=env)
    assert oc.returncode == 1
    assert "officecli is not installed; install it with: npm install" in oc.stderr.decode()


def test_no_engine_names_both_hints_and_check_keeps_lints_exit_code(tmp_path):
    env = _env_path(tmp_path)
    if render_mod.find_soffice() not in (None, shutil.which("soffice")):
        pytest.skip("LibreOffice is installed at a standard path outside PATH")
    proc = keyline("render", KPI, "-o", tmp_path / "a", env=env)
    err = proc.stderr.decode()
    assert proc.returncode == 1
    assert (
        "officecli is not installed; install it with: npm install -g @officecli/officecli; "
        "or install LibreOffice" in err
    )
    assert "L-002" in err
    check = keyline("check", KPI, "-o", tmp_path / "b", env=env)
    assert check.returncode == 2 and "render: skipped (officecli is not installed" in (
        check.stderr.decode()
    )


def test_standard_install_paths_are_searched(tmp_path, monkeypatch):
    fake = tmp_path / "soffice"
    fake.write_text("#!/bin/sh\necho 'LibreOffice 9.9.9.9 test'\n")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    monkeypatch.setattr(render_mod, "SOFFICE_PATHS", ("/nonexistent/soffice", str(fake)))
    assert render_mod.find_soffice() == str(fake)
    assert render_mod.libreoffice_version(str(fake)) == "LibreOffice 9.9.9.9 test"


def test_the_libreoffice_command_keeps_the_profile_and_outdir(tmp_path, monkeypatch):
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 1, "", "boom")

    monkeypatch.setattr(render_mod, "_run", lambda cmd, timeout: fake_run(cmd))
    with pytest.raises(render_mod.RenderError, match="libreoffice wrote no PDF: boom"):
        render_mod._render_libreoffice(KPI, tmp_path, "soffice", "pypdfium2", 4)
    (cmd,) = calls
    assert cmd[:3] == ["soffice", "--headless", "--norestore"]
    assert cmd[3].startswith("-env:UserInstallation=file://")
    assert cmd[4:7] == ["--convert-to", render_mod.LO_PDF_FILTER, "--outdir"]
    assert cmd[-1].endswith("/deck.pptx") and cmd[-1] != str(KPI.resolve())  # B-19
