"""Spec 002 AC-19 (§9; task T-43): `tools/build_skill.py` writes `dist/keyline.zip`. Two
builds are byte-identical; the zip root holds exactly one folder, `keyline/`, with
`SKILL.md`, `references/`, `scripts/`, `lib/keyline/` (the package with its packs and fit
tables, without caches or tests), `LICENSE` and `NOTICE`; and it is under 3 MB."""

import importlib.util
import sys
import zipfile

import pytest

from tests.conftest import ROOT

REFERENCES = ("anti-tells.md", "brief.md", "check.md", "craft-floor.md", "pen.md")


@pytest.fixture(scope="module")
def build_skill():
    spec = importlib.util.spec_from_file_location("build_skill", ROOT / "tools/build_skill.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_skill"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def package(build_skill, tmp_path_factory):
    return build_skill.build(tmp_path_factory.mktemp("dist") / "keyline.zip")


def test_two_builds_are_byte_identical(build_skill, package, tmp_path):
    again = build_skill.build(tmp_path / "again.zip")
    assert again.read_bytes() == package.read_bytes()
    assert package.stat().st_size < 3 * 1024 * 1024


def test_the_structure(package):
    with zipfile.ZipFile(package) as z:
        names = z.namelist()
        assert z.testzip() is None
    assert len(names) == len(set(names)) and {n.split("/")[0] for n in names} == {"keyline"}
    top = {n.split("/")[1] for n in names}
    assert top == {"SKILL.md", "references", "scripts", "lib", "LICENSE", "NOTICE"}
    assert sorted(n for n in names if n.startswith("keyline/references/")) == [
        f"keyline/references/{r}" for r in REFERENCES
    ]
    assert [n for n in names if n.startswith("keyline/scripts/")] == ["keyline/scripts/kl.py"]
    assert {n.split("/")[2] for n in names if n.startswith("keyline/lib/")} == {"keyline"}
    for needed in (
        "__init__.py", "cli.py", "thresholds.toml", "pen/_api.py", "packs/swiss/pack.toml",
        "packs/swiss/voices/neutral.toml", "fit/tables/liberation-sans-regular.json",
        "fit/tables/numerals.json", "fit/tables/breaks.json", "fit/tables/environments.json",
    ):  # fmt: skip
        assert f"keyline/lib/keyline/{needed}" in names, needed
    for name in names:
        assert "__pycache__" not in name and "/tests/" not in name, name
        assert not name.endswith((".pyc", ".pyo", "/")), name


def test_the_library_is_the_source_package(package):
    source = ROOT / "src" / "keyline"
    expected = {
        p.relative_to(source).as_posix(): p.read_bytes()
        for p in source.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    }
    with zipfile.ZipFile(package) as z:
        found = {
            n.removeprefix("keyline/lib/keyline/"): z.read(n)
            for n in z.namelist()
            if n.startswith("keyline/lib/keyline/")
        }
        assert z.read("keyline/SKILL.md") == (ROOT / "skill/keyline/SKILL.md").read_bytes()
        assert z.read("keyline/LICENSE") == (ROOT / "LICENSE").read_bytes()
        assert z.read("keyline/NOTICE") == (ROOT / "NOTICE").read_bytes()
    assert found == expected


def test_dist_is_not_committed():
    assert "dist/" in (ROOT / ".gitignore").read_text(encoding="utf-8").split()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for word in ("tools/build_skill.py", "dist/keyline.zip", "claude.ai", "Claude Code"):
        assert word in readme, word
