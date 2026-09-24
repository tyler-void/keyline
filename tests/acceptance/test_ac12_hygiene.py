"""AC-12: only allowed identities appear in commit metadata and fixture metadata.

Allowlist (D-013, D-014):
  author/committer  Tyler or tyler-void <code@tyler-void.dev>; committer GitHub <noreply@github.com>
  trailers          Co-Authored-By: Claude ... <noreply@anthropic.com>
The "no file copied from anthropics/skills" half of AC-12 is a manual audit step (the
lint core makes no network calls); see specs/001-lint-core/report.md.
"""

import io
import re
import shutil
import subprocess
import zipfile

import pytest
from lxml import etree

from tests.conftest import FIXTURES, ROOT

PEOPLE = {("Tyler", "code@tyler-void.dev"), ("tyler-void", "code@tyler-void.dev")}
WEB_COMMITTER = ("GitHub", "noreply@github.com")
CLAUDE_TRAILER = re.compile(r"^Co-Authored-By: Claude [^<>]* <noreply@anthropic\.com>$", re.I)
IDENTITY_TRAILER = re.compile(
    r"^(Co-Authored-By|Signed-off-by|Reviewed-by|Acked-by|Tested-by|Reported-by):", re.I
)
FIXTURE_PEOPLE = {"", "Tyler", "tyler-void", "@tyler-void", "OfficeCLI"}  # OfficeCLI: a tool (R-5)
SEP = "\x1e"


def _git_log():
    if shutil.which("git") is None or not (ROOT / ".git").exists():
        pytest.skip("not a git checkout")
    fmt = f"%H%x1f%an%x1f%ae%x1f%cn%x1f%ce%x1f%B{SEP}"
    out = subprocess.run(
        ["git", "-C", str(ROOT), "log", "--all", f"--format={fmt}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    commits = []
    for chunk in out.split(SEP):
        chunk = chunk.strip("\n")
        if chunk:
            sha, an, ae, cn, ce, body = chunk.split("\x1f", 5)
            commits.append((sha[:7], (an, ae), (cn, ce), body))
    return commits


def test_commit_authors_and_committers():
    commits = _git_log()
    assert commits
    for sha, author, committer, _ in commits:
        assert author in PEOPLE, f"{sha}: author {author}"
        assert committer in PEOPLE or committer == WEB_COMMITTER, f"{sha}: committer {committer}"


def test_commit_trailers():
    for sha, _, _, body in _git_log():
        for line in body.splitlines():
            line = line.strip()
            if not IDENTITY_TRAILER.match(line):
                continue
            if CLAUDE_TRAILER.match(line):
                continue
            m = re.match(r"^[^:]+:\s*(.+?)\s*<([^>]+)>$", line)
            assert m and (m.group(1), m.group(2)) in PEOPLE, f"{sha}: trailer {line!r}"


def _core_props(data: bytes, where: str):
    """(where, creator, lastModifiedBy) for a package and any package embedded in it."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            inner = z.read(name)
            if inner[:2] == b"PK":
                yield from _core_props(inner, f"{where}!{name}")
            elif name == "docProps/core.xml":
                root = etree.fromstring(inner)
                values = {}
                for tag in ("creator", "lastModifiedBy"):
                    el = root.find(f".//{{*}}{tag}")
                    values[tag] = (el.text or "").strip() if el is not None else ""
                yield where, values["creator"], values["lastModifiedBy"]


def test_fixture_metadata_identities():
    decks = sorted(FIXTURES.rglob("*.pptx"))
    assert len(decks) >= 20
    for deck in decks:
        for where, creator, modified in _core_props(deck.read_bytes(), deck.name):
            assert creator in FIXTURE_PEOPLE, f"{where}: creator {creator!r}"
            assert modified in FIXTURE_PEOPLE, f"{where}: lastModifiedBy {modified!r}"


def test_notice():
    assert "Copyright 2026 Tyler (@tyler-void)" in (ROOT / "NOTICE").read_text()
