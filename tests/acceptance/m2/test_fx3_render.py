"""Audit 02 FX-3 (amendment B-13): slide-NN.png is deck slide NN in every engine; a deck
with no slides, an unusable -o and a timeout fail cleanly; a reused output directory
loses the earlier render's PNGs."""

import os
import stat
import time

import pytest
from PIL import Image, ImageChops

from keyline import render as render_mod
from keyline import zipnorm
from tests.acceptance._cli import keyline
from tests.conftest import GOLDEN, ROOT

KPI = GOLDEN / "kpi-recipe.pptx"
EMPTY = ROOT / "src/keyline/packs/swiss/swiss-neutral-presented.pptx"  # a template: 0 slides
needs_lo = pytest.mark.skipif(
    render_mod.find_soffice() is None or render_mod.find_rasterizer() is None,
    reason="LibreOffice and a rasterizer are not installed",
)


def _hide_slide_2(out):
    entries = []
    for name, data in zipnorm.read_entries(KPI.read_bytes()):
        if name == "ppt/slides/slide2.xml":
            data = data.replace(b"<p:sld ", b'<p:sld show="0" ', 1)
        entries.append((name, data))
    return zipnorm.write(out, entries)


def _same(a, b):
    with Image.open(a) as x, Image.open(b) as y:
        return (
            x.size == y.size
            and ImageChops.difference(x.convert("RGB"), y.convert("RGB")).getbbox() is None
        )


@needs_lo
def test_libreoffice_exports_hidden_slides_so_numbers_match(tmp_path):
    hidden = _hide_slide_2(tmp_path / "hidden.pptx")
    a = render_mod.render(KPI, tmp_path / "a", "libreoffice")
    b = render_mod.render(hidden, tmp_path / "b", "libreoffice")
    assert [p.name for p in b.slides] == [
        "slide-01.png",
        "slide-02.png",
        "slide-03.png",
        "slide-04.png",
    ]
    for pa, pb in zip(a.slides, b.slides, strict=True):
        assert _same(pa, pb), pb.name  # slide-02.png is deck slide 2, hidden or not


def test_png_names_pad_to_the_slide_count():
    assert render_mod.png_name(3, 9) == "slide-03.png"
    assert render_mod.png_name(3, 99) == "slide-03.png"
    assert render_mod.png_name(3, 100) == "slide-003.png"
    assert render_mod.png_name(1000, 1000) == "slide-1000.png"


def test_rasterize_names_pages_for_the_deck_size(tmp_path):
    pdfium = pytest.importorskip("pypdfium2")
    doc = pdfium.PdfDocument.new()
    for _ in range(3):
        doc.new_page(960, 540)
    doc.save(tmp_path / "three.pdf")
    doc.close()
    pngs = render_mod.rasterize(tmp_path / "three.pdf", tmp_path, "pypdfium2", tmp_path, 120)
    assert [p.name for p in pngs] == ["slide-001.png", "slide-002.png", "slide-003.png"]


def test_a_deck_with_no_slides(tmp_path):
    proc = keyline("render", EMPTY, "-o", tmp_path / "r")
    assert proc.returncode == 1
    assert proc.stderr.decode().splitlines()[-1] == "keyline: render failed: deck has no slides"
    check = keyline("check", EMPTY, "-o", tmp_path / "c", "--no-validate")
    lint = keyline("lint", EMPTY)
    assert "render: skipped (deck has no slides)" in check.stderr.decode()
    assert check.returncode == lint.returncode


def test_an_unusable_output_directory(tmp_path):
    blocker = tmp_path / "a-file"
    blocker.write_text("not a directory")
    proc = keyline("render", KPI, "-o", blocker)
    assert proc.returncode == 1
    last = proc.stderr.decode().splitlines()[-1]
    assert last.startswith(f"keyline: render failed: cannot use {blocker} as the output directory")
    check = keyline("check", KPI, "-o", blocker, "--no-validate")
    assert check.returncode == 2  # lint's exit code (A-10)
    assert f"render: skipped (cannot use {blocker} as the output directory" in check.stderr.decode()
    assert "internal error" not in check.stderr.decode()


@needs_lo
def test_a_reused_output_directory_loses_the_old_pngs(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    for name in ("slide-09.png", "slide-100.png", "contact.png"):
        Image.new("RGB", (8, 8)).save(out / name)
    (out / "notes.txt").write_text("kept")
    render_mod.render(KPI, out, "libreoffice")
    assert sorted(p.name for p in out.iterdir()) == [
        "contact.png",
        "notes.txt",
        "slide-01.png",
        "slide-02.png",
        "slide-03.png",
        "slide-04.png",
    ]


@pytest.mark.skipif(os.name != "posix", reason="process groups")
def test_a_timeout_kills_the_group_and_removes_the_temp_directory(tmp_path, monkeypatch):
    pidfile = tmp_path / "child.pid"
    fake = tmp_path / "soffice"
    fake.write_text(f"#!/bin/sh\nsleep 300 &\necho $! > {pidfile}\nwait\n")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    made = []
    real_mkdtemp = render_mod.tempfile.mkdtemp

    def mkdtemp(**kw):
        made.append(real_mkdtemp(**kw))
        return made[-1]

    monkeypatch.setattr(render_mod.tempfile, "mkdtemp", mkdtemp)
    monkeypatch.setattr(render_mod, "LO_TIMEOUT_S", 1)
    with pytest.raises(render_mod.RenderError, match="libreoffice timed out after 1 s"):
        render_mod._render_libreoffice(KPI, tmp_path / "out", str(fake), "pypdfium2", 4)
    child = int(pidfile.read_text())
    for _ in range(50):  # the orphaned child is reaped by init shortly after the kill
        try:
            os.kill(child, 0)
        except ProcessLookupError:
            break
        time.sleep(0.1)
    else:
        pytest.fail(f"the soffice child {child} survived the timeout")
    assert made and not os.path.exists(made[0])
