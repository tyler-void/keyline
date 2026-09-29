"""Spec 002 AC-11 and AC-12 on the three specimens (§11.13, task T-28).

AC-11: building each specimen twice gives byte-identical files. AC-12: `keyline brief`
and `keyline check --brief` exit 0 on each, with no `adapter-unresolved`, and no
`ooxml-invalid` when OfficeCLI is present. The committed decks are also compared with a
fresh build: every XML part byte for byte, the picture by its pixels (its PNG bytes come
from Pillow's zlib, and the chart workbook's from XlsxWriter, neither of them pinned)."""

import io
import json
import subprocess
import sys
import zipfile

import pytest

pytest.importorskip("pptx")

from tests.acceptance._cli import keyline
from tests.conftest import FIXTURES, HAS_OFFICECLI

PACKS = FIXTURES / "packs"
SCRIPT = PACKS / "src/build_specimens.py"
STEMS = [
    "swiss-specimen-presented-neutral",
    "swiss-specimen-presented-night",
    "swiss-specimen-read-field",
]


@pytest.fixture(scope="module")
def builds(tmp_path_factory):
    """Two independent builds of all three specimens."""
    dirs = [tmp_path_factory.mktemp("first"), tmp_path_factory.mktemp("second")]
    for d in dirs:
        proc = subprocess.run([sys.executable, str(SCRIPT), str(d)], capture_output=True)
        assert proc.returncode == 0, proc.stderr.decode()
    return dirs


@pytest.mark.parametrize("stem", STEMS)
def test_ac11_each_specimen_builds_byte_identically(builds, stem):
    first, second = (d / f"{stem}.pptx" for d in builds)
    assert first.read_bytes() == second.read_bytes()


@pytest.mark.parametrize("stem", STEMS)
def test_the_committed_specimen_is_what_the_script_builds(builds, stem):
    from PIL import Image

    committed = zipfile.ZipFile(PACKS / f"{stem}.pptx")
    fresh = zipfile.ZipFile(builds[0] / f"{stem}.pptx")
    assert committed.namelist() == fresh.namelist()
    for name in committed.namelist():
        if name.startswith("ppt/embeddings/"):
            continue  # XlsxWriter's bytes; the chart part carries the same values
        old, new = committed.read(name), fresh.read(name)
        if name.startswith("ppt/media/"):
            old_img, new_img = (Image.open(io.BytesIO(b)) for b in (old, new))
            assert old_img.size == new_img.size, name
            assert old_img.convert("RGB").tobytes() == new_img.convert("RGB").tobytes(), name
        else:
            assert old == new, name


@pytest.mark.parametrize("stem", STEMS)
def test_ac12_the_brief_passes(stem):
    proc = keyline("brief", PACKS / f"{stem}.brief.toml", "--json")
    assert proc.returncode == 0, proc.stdout.decode() + proc.stderr.decode()


@pytest.mark.parametrize("stem", STEMS)
def test_ac12_check_with_the_brief_passes(tmp_path, stem):
    proc = keyline(
        "check",
        PACKS / f"{stem}.pptx",
        "--brief",
        PACKS / f"{stem}.brief.toml",
        "--json",
        "-o",
        tmp_path / "render",
    )
    err = proc.stderr.decode()
    assert proc.returncode == 0, err
    rules = {f["rule"] for f in json.loads(proc.stdout)}
    assert "adapter-unresolved" not in rules
    assert "ooxml-invalid" not in rules
    if HAS_OFFICECLI:
        assert "validate: passed" in err
