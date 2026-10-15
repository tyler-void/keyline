"""FX-36 (the auditor's checkpoint at f523a1a; B-27 item 3): tools/measure_lo.py skipped
the 52 non-letter characters of the measured set that no twin has. It now probes each in
an installed font that has it (fc-list), and its output names the font. LibreOffice
24.2.7.2 and 26.8.1.1 keep U+2045 with the word after and U+2046 with the word before,
as they do ( and ); the other 50 break. Before, the estimator broke at both, so it could
count one line fewer than LibreOffice set (FX-33's mechanism). Repro:
evidence/fx36-repros/probe_unprobed.py. Characters as code points."""

import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

from keyline.config import load as load_config
from keyline.fit.text import NO_BREAK_AFTER, NO_BREAK_BEFORE, break_units, opens
from tests.acceptance.m2 import _lo
from tests.conftest import ROOT

QUILL_LEFT, QUILL_RIGHT = chr(0x2045), chr(0x2046)  # ⁅ ⁆
REFERENCE_MARK, ASTERISKS = chr(0x203B), chr(0x2042)  # two of the 50 that break
FAMILIES = [family for family, _twin in load_config().portable_fonts]
needs_fonts = pytest.mark.skipif(shutil.which("fc-list") is None, reason="fc-list is not installed")
TWINS = _lo.untwinned(FAMILIES)  # the 52 are the characters the twins lack
needs_twins = pytest.mark.skipif(TWINS is not None, reason=f"the twins: {TWINS}")


@pytest.fixture(scope="module")
def measure_lo():
    pytest.importorskip("fontTools")
    spec = importlib.util.spec_from_file_location("measure_lo", ROOT / "tools/measure_lo.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["measure_lo"] = module
    spec.loader.exec_module(module)
    return module


def outside(measure_lo) -> list[str]:
    maps = [measure_lo._font(family, "regular")[0] for family in FAMILIES]
    return [c for c in measure_lo.break_chars() if not any(ord(c) in cmap for cmap in maps)]


def test_the_estimator_keeps_the_quills_with_their_words():
    assert QUILL_RIGHT in NO_BREAK_BEFORE and QUILL_LEFT in NO_BREAK_AFTER and opens(QUILL_LEFT)
    assert break_units(f"see {QUILL_LEFT} the note {QUILL_RIGHT} here") == [
        "see",
        f"{QUILL_LEFT} the",
        f"note {QUILL_RIGHT}",
        "here",
    ]
    assert break_units(f"a {REFERENCE_MARK} b") == ["a", REFERENCE_MARK, "b"]


@needs_fonts
@needs_twins
def test_each_character_no_twin_has_gets_an_installed_font(measure_lo):
    """The choice is fixed: the family that has the most of the characters left first,
    ties by name; each picked face maps its characters, and none is a portable family."""
    chars = outside(measure_lo)
    assert len(chars) == 52 and {QUILL_LEFT, QUILL_RIGHT} <= set(chars)
    picked, none = measure_lo.fallback_fonts(chars)
    assert (picked, none) == measure_lo.fallback_fonts(chars)
    assigned = [c for found in picked.values() for c in found]
    assert sorted(assigned + none) == sorted(chars) and len(set(assigned)) == len(assigned)
    for font, found in picked.items():
        assert font not in FAMILIES
        cmap = measure_lo._font(font, "regular")[0]
        assert all(ord(c) in cmap for c in found), font


def test_the_committed_output_probes_them_and_names_the_font():
    text = (ROOT / "specs/002-skill-pack/evidence/lo-26.8.1.1-measurements.txt").read_text(
        encoding="utf-8"
    )
    start = text.index("line breaks at a space (B-27 item 3)")
    section = text[start : text.index("\n\n", start)]
    (line,) = [row for row in section.splitlines() if "no twin has these; probed in" in row]
    assert "(52):" in line and "U+2045" in line and "U+2046" in line
    assert "in no installed font, not probed (0):" in section
    for cp, row in (("2045", "b/b       b/b             K/b       K/b"),
                    ("2046", "K/b       -/b             b/b       b/b")):  # fmt: skip
        assert any(r.startswith(f"  U+{cp} ") and r.endswith(row) for r in section.splitlines())


@needs_fonts
@_lo.needs_lo("Arial")
def test_libreoffice_keeps_the_quills_and_breaks_at_the_others(measure_lo, monkeypatch):
    """probe_unprobed.py: measure_lo's own probe on four characters no twin has, in the
    font picked for them, with ( and ) in Arial as controls."""
    from keyline.render import find_soffice, libreoffice_version

    chars = [QUILL_LEFT, QUILL_RIGHT, REFERENCE_MARK, ASTERISKS]
    picked, none = measure_lo.fallback_fonts(chars)
    if none:
        pytest.skip(f"no installed font has {', '.join(f'U+{ord(c):04X}' for c in none)}")
    monkeypatch.setattr(measure_lo, "break_chars", lambda: [*chars, "(", ")"])
    decks = {font: measure_lo.build_breaks(font, found) for font, found in picked.items()}
    decks["Arial"] = measure_lo.build_breaks("Arial", ["(", ")"])
    soffice = find_soffice()
    pages = {}
    with tempfile.TemporaryDirectory(prefix="kl-fx36-") as tmp:
        for i, (family, (deck_bytes, probes)) in enumerate(decks.items()):
            got = measure_lo.convert(Path(tmp), f"b{i}", deck_bytes, soffice, origins=True)
            assert len(got) == len(probes), family
            pages[family] = got
    lines, sets = measure_lo.break_report(decks, pages, libreoffice_version(soffice), picked)
    assert set(sets["before"]) == {")", QUILL_RIGHT}
    assert set(sets["after"]) == {"(", QUILL_LEFT}
    assert any(line.startswith("  no twin has these; probed in ") for line in lines)
