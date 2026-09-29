"""Audit 03 FX-9 (amendment B-19): LibreOffice converts a private copy with a fixed name,
so a symlinked deck or a name ending in "." renders, and the user's path never reaches
soffice."""

import subprocess

import pytest

from keyline import render as render_mod
from tests.acceptance._cli import keyline
from tests.conftest import GOLDEN

KPI = GOLDEN / "kpi-recipe.pptx"
needs_lo = pytest.mark.skipif(
    render_mod.find_soffice() is None or render_mod.find_rasterizer() is None,
    reason="LibreOffice and a rasterizer are not installed",
)


@pytest.mark.parametrize(
    ("name", "copy"),
    [("x.pptx", "deck.pptx"), ("x.PPTM", "deck.pptm"), ("clean v1.2", "deck.pptx")],
)
def test_soffice_gets_a_fixed_name_in_the_temp_directory(tmp_path, monkeypatch, name, copy):
    user = tmp_path / name
    user.write_bytes(KPI.read_bytes())
    seen = []

    def fake_run(cmd, timeout):
        seen.append(cmd[-1])
        return subprocess.CompletedProcess(cmd, 1, "", "no pdf")

    monkeypatch.setattr(render_mod, "_run", fake_run)
    work = tmp_path / "work"
    work.mkdir()
    with pytest.raises(render_mod.RenderError, match="wrote no PDF"):
        render_mod.convert_to_pdf(user, "soffice", work)
    assert seen == [str(work / copy)] and (work / copy).read_bytes() == KPI.read_bytes()


@needs_lo
@pytest.mark.parametrize("kind", ["symlink", "trailing-dot"])
def test_symlinks_and_trailing_dots_render(tmp_path, kind):
    if kind == "symlink":
        target = tmp_path / "real-target.pptx"
        target.write_bytes(KPI.read_bytes())
        deck = tmp_path / "link.pptx"
        deck.symlink_to(target)
    else:
        deck = tmp_path / "deck."
        deck.write_bytes(KPI.read_bytes())
    proc = keyline("render", deck, "-o", tmp_path / "out", "--engine", "libreoffice")
    assert proc.returncode == 0, proc.stderr.decode()
    assert len(list((tmp_path / "out").glob("slide-*.png"))) == 4
