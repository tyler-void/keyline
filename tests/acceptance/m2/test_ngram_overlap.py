"""Spec 002 AC-23 (task T-48; Q-56 as ruled): `tools/ngram_overlap.py A B` counts the
8-word sequences two folders share. It is generic and holds no third-party text; the
auditor runs it against a clone of another skill repository at the Phase B audit."""

import importlib.util
import sys

import pytest

from tests.conftest import ROOT

SENTENCE = "the lending shelf holds forty chisels and nine planes in two rows"


@pytest.fixture(scope="module")
def tool():
    spec = importlib.util.spec_from_file_location("ngram_overlap", ROOT / "tools/ngram_overlap.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["ngram_overlap"] = module
    spec.loader.exec_module(module)
    return module


def folders(tmp_path, left: str, right: str):
    a, b = tmp_path / "a", tmp_path / "b"
    (a / "docs").mkdir(parents=True)
    b.mkdir()
    (a / "docs" / "one.md").write_text(left, encoding="utf-8")
    (b / "two.txt").write_text(right, encoding="utf-8")
    return a, b


def test_a_shared_sentence_is_found_whatever_its_case_and_punctuation(tool, tmp_path, capsys):
    a, b = folders(tmp_path, f"# Notes\n\n{SENTENCE}.\n", f"Before. {SENTENCE.upper()}, after!\n")
    found = tool.shared(a, b)
    assert len(found) == len(SENTENCE.split()) - 8 + 1 == 5
    assert found[0] == (" ".join(SENTENCE.split()[:8]), "docs/one.md", "two.txt")
    assert tool.main([str(a), str(b), "--show", "2"]) == 1
    out = capsys.readouterr().out
    assert out.startswith("5 shared sequences of 8 words") and "… and 3 more" in out


def test_nothing_shared(tool, tmp_path, capsys):
    a, b = folders(tmp_path, SENTENCE, "a completely different line about bonsai trees and pots")
    assert tool.shared(a, b) == [] and tool.main([str(a), str(b)]) == 0
    assert capsys.readouterr().out.startswith("0 shared sequences")
    seven = " ".join(SENTENCE.split()[:7])  # shorter than a sequence
    a, b = folders(tmp_path / "short", seven, seven)
    assert tool.shared(a, b) == [] and len(tool.shared(a, b, n=7)) == 1


def test_binary_files_and_tool_folders_are_skipped(tool, tmp_path):
    a, b = folders(tmp_path, SENTENCE, SENTENCE)
    (b / "two.txt").unlink()
    (b / "blob.bin").write_bytes(b"\0\1" + SENTENCE.encode())
    (b / ".git").mkdir()
    (b / ".git" / "packed").write_text(SENTENCE, encoding="utf-8")
    (b / "latin1.txt").write_bytes("caf\xe9 ".encode("latin-1") + SENTENCE.encode())
    assert tool.shared(a, b) == []


def test_usage_errors(tool, tmp_path, capsys):
    a, b = folders(tmp_path, SENTENCE, SENTENCE)
    assert tool.main([str(a), str(tmp_path / "missing")]) == 2
    assert tool.main([str(a), str(b), "--n", "0"]) == 2
    assert "ngram_overlap:" in capsys.readouterr().err


def test_the_tool_holds_no_third_party_text():
    """It reads only the two folders it is given, and imports only the standard library."""
    source = (ROOT / "tools" / "ngram_overlap.py").read_text(encoding="utf-8")
    imports = set(__import__("re").findall(r"^(?:import|from) (\w+)", source, flags=8))
    assert imports <= {"__future__", "argparse", "re", "sys", "pathlib"}
    assert "http" not in source and "urllib" not in source and "socket" not in source
