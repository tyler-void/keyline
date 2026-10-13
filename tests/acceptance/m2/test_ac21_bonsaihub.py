"""Spec 002 AC-21 (§10; tasks T-45 and T-46; B-8.14, B-28; audit 07 §4.6): the BonsaiHub
demo. `product.toml` matches its hash. The deck tests skip only while no demo file
exists; once one exists they run, and fail when they cannot. For each of `pitch` and
`preread`:
- the brief passes `kl.py brief` with exit 0 and carries an inline voice with a `why`
  line per palette role;
- the deck passes `kl.py check DECK --brief BRIEF` with exit 0, and gives no
  `ooxml-invalid` where OfficeCLI is installed;
- two builds are byte-identical to each other and to the committed deck;
- the disclosure is on the first or the last slide;
- the slide count is within §10's range."""

import hashlib
import json
import shutil
import subprocess
import sys
import tomllib
import zipfile

import pytest
from lxml import etree

from tests.conftest import ROOT

DEMO = ROOT / "examples" / "bonsaihub"
KL = ROOT / "skill" / "keyline" / "scripts" / "kl.py"
PRODUCT_SHA256 = "9b0fea6ee7eac65dbb380b6d91128406772abed2caa5f23bdcf379eae1586f8b"
DECKS = {  # deck: (mode, fewest slides, most slides)
    "pitch": ("presented", 8, 12),
    "preread": ("read", 4, 8),
}
ROLES = ("paper", "ink", "muted", "hairline", "accent", "accent_on_ink")
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def demo_files(deck: str) -> list:
    return [DEMO / f"{deck}.brief.toml", DEMO / f"build_{deck}.py", DEMO / f"{deck}.pptx"]


EXISTS = any(p.exists() for deck in DECKS for p in demo_files(deck))
needs_demo = pytest.mark.skipif(not EXISTS, reason="the demo has not been built yet (T-46)")


def kl(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(KL), *map(str, args)], capture_output=True, text=True, cwd=cwd
    )


def slide_texts(deck_path) -> list[str]:
    """The text of each slide, in order."""
    with zipfile.ZipFile(deck_path) as z:
        names = sorted(
            (n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")),
            key=lambda n: int(n[len("ppt/slides/slide") : -len(".xml")]),
        )
        return [
            " ".join(t.text or "" for t in etree.fromstring(z.read(n)).iter(f"{A}t")) for n in names
        ]


def test_product_toml_is_the_auditors_file():
    data = (DEMO / "product.toml").read_bytes()
    assert hashlib.sha256(data).hexdigest() == PRODUCT_SHA256


@needs_demo
@pytest.mark.parametrize("deck", list(DECKS))
def test_every_demo_file_is_committed(deck):
    for path in demo_files(deck):
        assert path.is_file(), f"{path.relative_to(ROOT)} is missing"
    render = DEMO / "render" / deck
    assert (render / "contact.png").is_file() and list(render.glob("slide-*.png"))
    script = (DEMO / f"build_{deck}.py").read_text(encoding="utf-8")
    assert 'author="Tyler"' in script or "author='Tyler'" in script


@needs_demo
@pytest.mark.parametrize("deck", list(DECKS))
def test_the_brief_passes_and_carries_an_inline_voice(deck):
    path = DEMO / f"{deck}.brief.toml"
    proc = kl("brief", path)
    assert proc.returncode == 0, proc.stderr
    brief = tomllib.loads(path.read_text(encoding="utf-8"))
    mode, fewest, most = DECKS[deck]
    assert brief["mode"] == mode and brief["pack"] == "swiss"  # B-28: the Swiss pack
    assert fewest <= len(brief["slides"]) <= most
    assert "product.toml" in brief["evidence"][0]  # the primary evidence file
    voice = brief["voice"]
    assert isinstance(voice, dict), "the voice is inline, derived from [product.world] (B-8.14)"
    assert set(voice["palette"]) == set(ROLES)
    assert set(voice["why"]) == set(ROLES) and all(voice["why"][r].strip() for r in ROLES)
    direction = brief["direction"]
    assert 3 <= len(direction["own_world"]) <= 7 and direction["thesis"] and direction["motif"]


@needs_demo
@pytest.mark.parametrize("deck", list(DECKS))
def test_the_deck_passes_check(deck, tmp_path):
    proc = kl("check", DEMO / f"{deck}.pptx", "--brief", DEMO / f"{deck}.brief.toml",
              "-o", tmp_path / "render", "--json")  # fmt: skip
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    findings = report["findings"] if isinstance(report, dict) else report
    assert not [f for f in findings if f["rule"] == "ooxml-invalid"]
    assert not [f for f in findings if f["severity"] in ("warning", "error")]


@needs_demo
@pytest.mark.parametrize("deck", list(DECKS))
def test_two_builds_equal_each_other_and_the_committed_deck(deck, tmp_path):
    built = []
    for run in ("one", "two"):
        work = tmp_path / run
        shutil.copytree(DEMO, work, ignore=shutil.ignore_patterns("render", "surfaces", "*.pptx"))
        proc = kl("run", work / f"build_{deck}.py", cwd=work)
        assert proc.returncode == 0, proc.stderr
        built.append((work / f"{deck}.pptx").read_bytes())
    assert built[0] == built[1]
    assert built[0] == (DEMO / f"{deck}.pptx").read_bytes(), "the committed deck is not this build"


@needs_demo
@pytest.mark.parametrize("deck", list(DECKS))
def test_the_disclosure_and_the_slide_count(deck):
    product = tomllib.loads((DEMO / "product.toml").read_text(encoding="utf-8"))["product"]
    assert product["fictional"] is True
    slides = slide_texts(DEMO / f"{deck}.pptx")
    _mode, fewest, most = DECKS[deck]
    assert fewest <= len(slides) <= most
    disclosure = " ".join(product["disclosure"].split())
    edges = " ".join(slides[0].split()), " ".join(slides[-1].split())
    assert any(disclosure in text for text in edges), "the disclosure is on neither edge slide"


@needs_demo
def test_g2a_is_recorded():
    report = (ROOT / "specs" / "002-skill-pack" / "report.md").read_text(encoding="utf-8")
    assert "G-2a" in report and "sha256" in report.lower()
