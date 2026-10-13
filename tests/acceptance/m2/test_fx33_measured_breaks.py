"""Audit 07 FX-33 (amendment B-27 item 3): the no-break-before and no-break-after sets are
measured, not listed. tools/measure_lo.py probes every non-letter character of the
measured set at the space before it and the space after it, alone and attached to a word,
with and without room for the space; tools/gen_measured.py stores the union over the
versions measured (fit/tables/breaks.json), and this test re-derives it. LibreOffice
24.2.7.2 will not break before a backslash after a space: LaTeX-style text estimated at 4
lines was set in 5, +25.8 px below its region. Repro: evidence/audit07-repros/
f2_backslash.py and probe_b.py. Characters as code points."""

import importlib.util
import json
import re
import sys
import unicodedata

import pytest

from keyline.config import load as load_config
from keyline.fit.text import (
    FULLWIDTH_CLOSERS,
    MEASURED,
    NO_BREAK_AFTER,
    NO_BREAK_BEFORE,
    SPACES,
    break_units,
    opens,
)
from keyline.packs import resolve
from tests.acceptance.m2 import _lo
from tests.conftest import ROOT

pytest.importorskip("pptx")

from keyline.pen import Deck, DoesNotFit

FAMILIES = [f for f, _twin in load_config().portable_fonts]
BREAKS = ROOT / "src/keyline/fit/tables/breaks.json"
DATA = json.loads(BREAKS.read_text(encoding="utf-8"))
FULL = ROOT / "specs/002-skill-pack/evidence/lo-26.8.1.1-measurements.txt"
BACKSLASH, FRACTION_SLASH = chr(0x5C), chr(0x2044)


def tool(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_the_data_is_rederived():
    """From the committed measure_lo outputs alone: no LibreOffice, no fonts."""
    assert tool("gen_measured").breaks() == BREAKS.read_text(encoding="utf-8")


def test_the_sets_are_the_union_over_the_versions():
    versions = {v["version"]: v for v in DATA["versions"]}
    assert len(versions) == 3 and any("24.2.7.2" in v for v in versions)
    for key in ("no_break_before", "no_break_after"):
        assert DATA[key] == sorted({cp for v in versions.values() for cp in v[key]})
    assert set(NO_BREAK_BEFORE) == {*map(chr, DATA["no_break_before"]), *FULLWIDTH_CLOSERS}
    assert set(NO_BREAK_AFTER) == set(map(chr, DATA["no_break_after"]))
    assert set(NO_BREAK_BEFORE) - set(FULLWIDTH_CLOSERS) <= set(MEASURED)
    assert set(NO_BREAK_AFTER) <= set(MEASURED)


def test_the_full_probe_gives_its_version_as_measured():
    """26.8.1.1: eleven characters are kept with the word before, U+2044 among them, and
    seven with the word after. It breaks before a backslash; 24.2.7.2 does not."""
    text = FULL.read_text(encoding="utf-8")
    (full,) = [v for v in DATA["versions"] if v["probe"] == "full"]
    assert full["version"] in text
    for side in ("before", "after"):
        (line,) = re.findall(rf"^  no break {side} \(\d+\):(.*)$", text, re.MULTILINE)
        assert full[f"no_break_{side}"] == sorted(int(cp[2:], 16) for cp in line.split())
    assert {chr(c) for c in full["no_break_before"]} == {*")]},.:;!?/", FRACTION_SLASH}
    assert {chr(c) for c in full["no_break_after"]} == {
        *"([{",
        *map(chr, (0xA1, 0xBF, 0x201A, 0x201E)),
    }
    old = next(v for v in DATA["versions"] if "24.2.7.2" in v["version"])
    assert old["probe"].startswith("listed") and ord(BACKSLASH) in old["no_break_before"]
    assert ord(BACKSLASH) not in full["no_break_before"]


def test_the_probe_covers_every_non_letter_of_the_measured_set():
    measure_lo = tool("measure_lo")
    chars = measure_lo.break_chars()
    assert chars == [c for c in MEASURED if unicodedata.category(c)[0] != "L" and c not in SPACES]
    assert len(chars) == 202
    text = FULL.read_text(encoding="utf-8")
    start = text.index("line breaks at a space (B-27 item 3)")
    section = text[start : text.index("\n\n", start)]
    rows = {
        int(cp, 16) for cp in re.findall(r"^  U\+([0-9A-F]{4,5}) .*[Kb-]/[Kb-]$", section, re.M)
    }
    (unprobed,) = re.findall(r"in no twin, not probed \(\d+\):(.*)$", section, re.MULTILINE)
    missing = {int(cp[2:], 16) for cp in unprobed.split()}
    assert rows | missing == set(map(ord, chars)) and not rows & missing
    assert len(rows) == 150


def test_the_outcome_of_a_probe():
    """From glyph origins (character, x, y): the break at the probed space, a refused
    break, and a probe that tested nothing."""
    outcome = tool("measure_lo").break_outcome

    def glyphs(text, *line_ends):
        """The text's glyphs in reading order, a new line after each index given."""
        out, y = [], 500.0
        for i, ch in enumerate(text.replace(" ", "")):
            out.append((ch, float(i), y))
            if i in line_ends:
                y -= 57.6
        return out

    text = "nnn nnn nnn ) mmm"  # glyph 8 ends the first words, 9 is the character
    assert outcome("before", glyphs(text, 8)) == "breaks"
    assert outcome("before", glyphs(text, 5)) == "kept"  # the last word went down with it
    assert outcome("before", glyphs(text, 9)) == "fits"
    assert outcome("after", glyphs(text, 9)) == "breaks"
    assert outcome("after", glyphs(text, 8)) == "kept"  # it went down with the next word
    assert outcome("after", glyphs(text)) == "fits"
    assert outcome("before", glyphs("nnn nnn nnn mmm")) == "no glyph"


def test_break_units_use_the_measured_sets():
    assert break_units(f"the angle, {BACKSLASH}alpha sets") == [
        "the",
        f"angle, {BACKSLASH}alpha",
        "sets",
    ]
    assert break_units(f"1 {FRACTION_SLASH} 2") == [f"1 {FRACTION_SLASH}", "2"]
    assert opens("(") and opens(chr(0xFF08)) and not opens("") and not opens("$")
    assert break_units("") == [""]


# f2_backslash.py's corpus: LaTeX-style commands, each after a space ("@" stands for the
# backslash here)
CORPUS = (
    "In the template, @alpha sets the angle, @beta the slope and @gamma the offset; "
    "@frac divides two terms, @sqrt takes the root, @sum adds the series, @int "
    "integrates it, @label names the equation, @ref cites it and @cite points to "
    "the source, while @emph marks a word and @textbf sets it in bold."
)
CORPUS = CORPUS.replace("@", BACKSLASH).split()
PLACES = [  # role, variant, region, style
    ("evidence", None, "main", "body"),
    ("statement", None, "main", "lede"),
    ("evidence", "figure", "side", "body"),
]


def longest(accepts):
    best = None
    for n in range(1, 2000):
        text = " ".join(CORPUS[i % len(CORPUS)] for i in range(n))
        if not accepts(text):
            return best
        best = text
    raise AssertionError("no text was refused")


def place(deck, role, variant, region, style, text):
    deck.add(role, "x", variant=variant).text(text, style=style, region=region)


def accepts(mode, voice, where, text):
    try:
        place(Deck(pack="swiss", mode=mode, voice=voice), *where, text)
    except DoesNotFit:
        return False
    return True


@_lo.needs_lo("Arial", "Courier New", "Calibri")
@pytest.mark.parametrize("mode", ["presented", "read"])
def test_backslash_commands_at_the_limit_stay_in_their_region(mode, tmp_path):
    """f2_backslash.py: the longest text the pen accepts, word by word, in the body, the
    lede and the side body. Every glyph ends within 1.5 pt (2 px at 1280 px) of its
    region's bottom. 24.2.7.2 is the version that needs the fix."""
    pack = resolve("swiss")
    for family in ("Arial", "Courier New", "Calibri"):
        voice = _lo.voice_file(tmp_path, family)
        texts = [longest(lambda t, w=where, v=voice: accepts(mode, v, w, t)) for where in PLACES]
        d = Deck(pack="swiss", mode=mode, voice=voice)
        for where, text in zip(PLACES, texts, strict=True):
            place(d, *where, text)
        path = tmp_path / f"latex-{family.replace(' ', '')}.pptx"
        d.save(str(path))
        pages = _lo.chars(path, tmp_path / f"lo-{path.stem}")
        for (role, variant, region, style), page in zip(PLACES, pages, strict=True):
            layout = f"keyline:{role}" + (f":{variant}" if variant else "")
            box = _lo.region_pt(pack, layout, region)
            mine = [c for c in page if c[2] >= box[1] - 1.5 and c[1] >= box[0] - 1.5]
            assert mine and max(c[4] for c in mine) <= box[3] + 1.5, (mode, family, layout, style)
