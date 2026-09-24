"""The committed rule and foreign fixtures are exactly what their build scripts produce.

python-pptx writes zip timestamps, so the zips differ byte-wise; each XML part is
compared after canonicalization instead (docProps excluded)."""

import importlib.util
import io
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
