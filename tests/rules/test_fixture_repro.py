"""The committed rule and foreign fixtures are exactly what their build scripts produce.

python-pptx writes zip timestamps, so the zips differ byte-wise; each XML part is
compared after canonicalization instead (docProps excluded)."""

import importlib.util
import io
import subprocess
import sys
import zipfile

import pytest
from lxml import etree

from tests.conftest import FOREIGN, RULES

pytest.importorskip("pptx")


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _parts(source, prefix=""):
    """Canonical parts of a zip; nested zips (embedded workbooks) are expanded too."""
    out = {}
    with zipfile.ZipFile(source) as z:
        for n in sorted(z.namelist()):
            if n.startswith("docProps/"):
                continue
            data = z.read(n)
            if data[:2] == b"PK":
                out.update(_parts(io.BytesIO(data), f"{prefix}{n}!"))
                continue
            if n.endswith((".xml", ".rels")):
                data = etree.tostring(etree.fromstring(data), method="c14n")
            out[prefix + n] = data
    return out


BUILDERS = [
    (RULES / "src" / "build_rules.py", RULES),
    (FOREIGN / "src" / "build_foreign.py", FOREIGN),
]


@pytest.mark.parametrize(("script", "committed"), BUILDERS, ids=["rules", "foreign"])
def test_fixtures_reproduce(script, committed, tmp_path):
    if not script.exists():
        pytest.skip(f"{script.name} not written yet")
    mod = _load(script, f"_builder_{committed.name}")
    written = mod.build(tmp_path)
    if not written:
        pytest.skip("builder defines no decks yet")
    for fresh in written:
        kept = committed / fresh.name
        assert kept.exists(), f"{kept.name} is not committed"
        assert _parts(fresh) == _parts(kept), f"{kept.name} differs from its build script"


STRESS = FOREIGN / "stress"
STRESS_PY = [
    ("ppx_style_text.py", "d15_ppx_style_fontref.pptx"),
    ("raw_color.py", "d16_raw_color.pptx"),
    ("raw_geometry.py", "d17_raw_geometry.pptx"),
    ("ppx_localized_names.py", "d25_ppx_localized_names.pptx"),
]


def _run(*args, cwd):
    subprocess.run([sys.executable, *map(str, args)], cwd=cwd, check=True, capture_output=True)


@pytest.mark.parametrize(("script", "deck"), STRESS_PY, ids=[d for _, d in STRESS_PY])
def test_stress_decks_reproduce(script, deck, tmp_path):
    src = STRESS / "src"
    _run(src / script, tmp_path / deck, cwd=src)
    assert _parts(tmp_path / deck) == _parts(STRESS / deck)


def test_stress_strict_and_oddities_reproduce(tmp_path):
    src = STRESS / "src"
    _run(src / "ppx_layouts.py", tmp_path / "d02.pptx", cwd=src)
    _run(src / "strict_convert.py", tmp_path / "d02.pptx", tmp_path / "d27.pptx", cwd=src)
    assert _parts(tmp_path / "d27.pptx") == _parts(STRESS / "d27_strict_from_ppx.pptx")
    _run(src / "raw_oddities.py", tmp_path, cwd=src)
    odd = sorted(STRESS.glob("o5*.pptx"))
    assert len(odd) == 6
    for kept in odd:
        assert _parts(tmp_path / kept.name) == _parts(kept), kept.name
