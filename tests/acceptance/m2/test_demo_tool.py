"""Task T-46 (plan Q-58 as ruled; audit 07 §4.7): `tools/demo.py` prepares the directory
for the fresh session that builds the BonsaiHub demo, outside the checkout, records what
the audit asks for, and copies the outputs into examples/bonsaihub/. The session itself
is Tyler's; this tests the tool around it."""

import hashlib
import importlib.util
import json
import sys

import pytest

from tests.conftest import ROOT


@pytest.fixture(scope="module")
def demo():
    spec = importlib.util.spec_from_file_location("demo", ROOT / "tools" / "demo.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["demo"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def ready(demo, tmp_path, monkeypatch):
    """A demo folder set up from a freshly built zip, without the venv."""
    build = importlib.util.spec_from_file_location("build_skill", ROOT / "tools/build_skill.py")
    build_skill = importlib.util.module_from_spec(build)
    sys.modules["build_skill"] = build_skill
    build.loader.exec_module(build_skill)
    monkeypatch.setattr(demo, "ZIP", build_skill.build(tmp_path / "dist" / "keyline.zip"))
    folder = tmp_path / "demo"
    demo.setup(folder, with_venv=False)
    return folder


def test_setup_makes_the_folder_ready(demo, ready):
    assert (ready / ".claude/skills/keyline/SKILL.md").is_file()
    assert (ready / ".claude/skills/keyline/lib/keyline/__init__.py").is_file()
    product = ready / "examples/bonsaihub/product.toml"
    assert product.read_bytes() == (ROOT / "examples/bonsaihub/product.toml").read_bytes()
    assert not (ready / "CLAUDE.md").exists()  # the checkout's instructions are not there
    data = json.loads((ready / "SETUP.json").read_text(encoding="utf-8"))
    assert data["zip_sha256"] == hashlib.sha256(demo.ZIP.read_bytes()).hexdigest()
    assert "examples/bonsaihub/product.toml" in data["placed"]
    assert ".claude/skills/keyline/scripts/kl.py" in data["placed"]


def test_setup_refuses_the_checkout_and_a_folder_in_use(demo, ready):
    with pytest.raises(SystemExit, match="outside the keyline checkout"):
        demo.setup(ROOT / "examples" / "bonsaihub" / "run", with_venv=False)
    with pytest.raises(SystemExit, match="is not empty"):
        demo.setup(ready, with_venv=False)


def session_writes(folder):
    """What a fresh session leaves behind, for one deck."""
    work = folder / "examples" / "bonsaihub"
    (work / "pitch.brief.toml").write_text("schema = 1\n", encoding="utf-8")
    (work / "build_pitch.py").write_text("print('build')\n", encoding="utf-8")
    (work / "pitch.pptx").write_bytes(b"PK deck")
    (work / "pitch.evidence.toml").write_text("schema = 1\n", encoding="utf-8")
    (work / "render" / "pitch").mkdir(parents=True)
    (work / "render" / "pitch" / "contact.png").write_bytes(b"png")
    (work / "scratch.txt").write_text("a note the session left\n", encoding="utf-8")


def test_record_lists_what_the_session_wrote(demo, ready):
    session_writes(ready)
    text = demo.record(ready)
    assert f"- working directory: `{ready}`" in text
    assert f"- skill: `{ready / '.claude' / 'skills' / 'keyline'}`" in text
    assert "`dist/keyline.zip` SHA-256: `" in text and "imports from" in text
    deck = hashlib.sha256(b"PK deck").hexdigest()
    assert f"  - `examples/bonsaihub/pitch.pptx` `{deck}`" in text
    assert "scratch.txt" in text  # everything the session wrote is recorded
    assert "product.toml" not in text and "SKILL.md" not in text and "SETUP.json" not in text


def test_collect_copies_the_outputs_and_nothing_else(demo, ready, tmp_path):
    session_writes(ready)
    target = tmp_path / "target"
    copied = sorted(p.relative_to(target).as_posix() for p in demo.collect(ready, target))
    assert copied == [
        "build_pitch.py",
        "pitch.brief.toml",
        "pitch.evidence.toml",
        "pitch.pptx",
        "render/pitch/contact.png",
    ]
    assert not (target / "product.toml").exists() and not (target / "scratch.txt").exists()
