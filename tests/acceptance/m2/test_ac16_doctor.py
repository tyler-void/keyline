"""Spec 002 AC-16: `keyline doctor` prints one token per check (and one per portable font,
B-8.12), the install command for anything missing, and exits 0 exactly when lint can run.
The NO_PPTX and NO_LXML/NO_PILLOW paths run in real virtual environments that lack them."""

import json
import os
import subprocess
import sys
from pathlib import Path

import lxml
import PIL
import pytest

from keyline import doctor
from keyline.config import load
from tests.acceptance._cli import keyline
from tests.conftest import ROOT

TOKENS = {
    "python": {"PYTHON_OK", "PYTHON_OLD"},
    "lxml": {"LXML_OK", "NO_LXML"},
    "pillow": {"PILLOW_OK", "NO_PILLOW"},
    "python-pptx": {"PPTX_OK", "NO_PPTX"},
    "render": {"RENDER_LIBREOFFICE", "RENDER_OFFICECLI", "NO_RENDERER"},
    "rasterizer": {"RASTER_PDFIUM", "RASTER_PDFTOPPM", "NO_RASTER"},
    "validator": {"VALIDATE_OFFICECLI", "NO_VALIDATOR"},
}


def test_json_has_every_check_font_and_pack():
    proc = keyline("doctor", "--json")
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert list(data) == ["checks", "fonts", "packs", "lint_can_run"]
    assert [c["check"] for c in data["checks"]] == list(TOKENS)
    for c in data["checks"]:
        assert c["token"] in TOKENS[c["check"]]
        assert bool(c["hint"]) == c["token"].startswith(("NO_", "PYTHON_OLD"))
    families = [(f["family"], f["metric_twin"]) for f in data["fonts"]]
    assert families == list(load().portable_fonts)
    for f in data["fonts"]:
        assert f["token"] in ("FONT_OK", "FONT_SUBSTITUTED")
        assert bool(f["hint"]) == (f["token"] == "FONT_SUBSTITUTED")
    assert data["packs"] == ["swiss"] and data["lint_can_run"] is True


def test_human_lines_carry_the_tokens():
    out = keyline("doctor").stdout.decode().splitlines()
    assert out[0].startswith("PYTHON_OK ") and out[-1] == "PACKS: swiss"
    tokens = [line.split()[0] for line in out if line and not line.startswith(" ")]
    assert sum(t in ("FONT_OK", "FONT_SUBSTITUTED") for t in tokens) == 6


def test_missing_engines_print_install_commands(tmp_path):
    env = dict(os.environ, PATH=str(tmp_path))  # nothing on PATH, not even fc-match
    data = json.loads(keyline("doctor", "--json", env=env).stdout)
    by = {c["check"]: c for c in data["checks"]}
    if by["render"]["token"] == "NO_RENDERER":
        assert "npm install -g @officecli/officecli" in by["render"]["hint"]
    assert by["validator"]["token"] == "NO_VALIDATOR"
    assert "(no fc-match)" in data["fonts"][0]["detail"]


def test_fonts_by_file_name_without_fc_match(tmp_path, monkeypatch):
    (tmp_path / "Arial.ttf").write_bytes(b"")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "Carlito-Regular.ttf").write_bytes(b"")
    monkeypatch.setattr(doctor.shutil, "which", lambda name: None)
    monkeypatch.setattr(doctor, "font_dirs", lambda: [tmp_path])
    tokens = {f["family"]: f["token"] for f in doctor.fonts()}
    assert tokens["Arial"] == "FONT_OK"
    assert tokens["Calibri"] == "FONT_OK"  # through its twin
    assert tokens["Georgia"] == "FONT_SUBSTITUTED"


def _venv(tmp_path, *packages):
    """A real venv holding keyline (by path) and only the named site packages."""
    venv = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", venv], check=True)
    (site,) = (venv / "lib").glob("python3*/site-packages")
    (site / "keyline.pth").write_text(str(ROOT / "src") + "\n")
    for pkg in packages:
        (site / pkg.name).symlink_to(pkg)
    return venv / "bin" / "python"


def _doctor(python):
    proc = subprocess.run(
        [python, "-m", "keyline", "doctor", "--json"], capture_output=True, text=True
    )
    return proc.returncode, json.loads(proc.stdout)


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX venv layout")
def test_no_pptx_in_a_venv_without_python_pptx(tmp_path):
    site = Path(lxml.__file__).parents[1]
    packages = [Path(lxml.__file__).parent, Path(PIL.__file__).parent]
    packages += [p for p in (site / "pillow.libs",) if p.is_dir()]
    code, data = _doctor(_venv(tmp_path, *packages))
    by = {c["check"]: c for c in data["checks"]}
    assert code == 0 and by["python-pptx"]["token"] == "NO_PPTX"
    assert by["python-pptx"]["hint"] == 'pip install "keyline[pen]" (or pip install python-pptx)'


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX venv layout")
def test_without_lxml_and_pillow_lint_cannot_run(tmp_path):
    code, data = _doctor(_venv(tmp_path))
    by = {c["check"]: c["token"] for c in data["checks"]}
    assert code == 1 and data["lint_can_run"] is False
    assert (by["lxml"], by["pillow"]) == ("NO_LXML", "NO_PILLOW")
