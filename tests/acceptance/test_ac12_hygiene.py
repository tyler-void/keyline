"""AC-12: only allowed identities appear in commit metadata and fixture metadata.

Allowlist (D-013, D-014):
  author/committer  Tyler or tyler-void <code@tyler-void.dev>; committer GitHub <noreply@github.com>
  trailers          Co-Authored-By: Claude ... <noreply@anthropic.com>
The "no file copied from anthropics/skills" half of AC-12 is a manual audit step (the
lint core makes no network calls); see specs/001-lint-core/report.md.

Spec 002 AC-23 (task T-48; audit 07 §4.8) extends the metadata check from fixtures/ to
every deck under examples/, skill/ and the bundled packs, with an allow-list for the
core properties, and checks the text of skill/ and examples/ for other identities.
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
# OfficeCLI and PptxGenJS are tool names, not people (R-5; d20's embedded chart workbook)
FIXTURE_PEOPLE = {"", "Tyler", "tyler-void", "@tyler-void", "OfficeCLI", "PptxGenJS"}
# AC-23: what a deck keyline ships or shows may carry as creator or lastModifiedBy
SHIPPED_PEOPLE = {"", "Tyler", "tyler-void", "@tyler-void"}
SHIPPED = (ROOT / "examples", ROOT / "skill", ROOT / "src" / "keyline" / "packs")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
HANDLE = re.compile(r"(?<![\w.`/])@([A-Za-z][\w-]*)")
AUTHOR = re.compile(r"""author\s*=\s*["']([^"']*)["']""")
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


def test_shipped_deck_metadata_identities():
    """AC-23: every deck under examples/, skill/ and the bundled packs, by allow-list."""
    decks = sorted(p for folder in SHIPPED if folder.is_dir() for p in folder.rglob("*.pptx"))
    assert len(decks) >= 2  # the two neutral templates, then the demo and surface decks
    for deck in decks:
        for where, creator, modified in _core_props(deck.read_bytes(), deck.name):
            assert creator in SHIPPED_PEOPLE, f"{where}: creator {creator!r}"
            assert modified in SHIPPED_PEOPLE, f"{where}: lastModifiedBy {modified!r}"


def test_skill_and_examples_name_no_one_else():
    """AC-23: in the text of skill/ and examples/, an e-mail address or an @handle is an
    approved one, and a build script's author is Tyler."""
    checked = 0
    for folder in (ROOT / "skill", ROOT / "examples"):
        for path in sorted(folder.rglob("*")):
            if not path.is_file() or path.suffix not in (".md", ".toml", ".py", ".txt", ".json"):
                continue
            text = path.read_text(encoding="utf-8")
            where = path.relative_to(ROOT).as_posix()
            checked += 1
            for address in EMAIL.findall(text):
                assert address in {e for _n, e in PEOPLE}, f"{where}: {address}"
            if path.suffix != ".py":  # a decorator is not a handle
                for handle in HANDLE.findall(text):
                    assert handle == "tyler-void", f"{where}: @{handle}"
            for author in AUTHOR.findall(text) if path.suffix == ".py" else ():
                assert author in ("", "Tyler"), f"{where}: author={author!r}"
    assert checked >= 8  # SKILL.md, five references, kl.py and product.toml
