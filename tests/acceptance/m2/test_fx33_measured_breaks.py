"""Audit 07 FX-33 (amendment B-27 item 3): the no-break-before and no-break-after sets are
measured, not listed. tools/measure_lo.py probes every non-letter character of the
measured set at the space before it and the space after it, alone and attached to a word,
with and without room for the space; tools/gen_measured.py stores the union over the
versions measured (fit/tables/breaks.json), and this test re-derives it. LibreOffice
24.2.7.2 will not break before a backslash after a space: LaTeX-style text estimated at 4
lines was set in 5, +25.8 px below its region. Repro: evidence/audit07-repros/
f2_backslash.py and probe_b.py. Since the auditor's Phase B checkpoint (plan Q-60) both
entries come from the full probe: 26.8.1.1 and 24.2.7.2. Characters as code points."""

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
BACKSLASH, FRACTION_SLASH = chr(0x5C), chr(0x2044)
KEPT_BEFORE = ")]},.:;!?/" + FRACTION_SLASH  # kept with the word before, on both versions
KEPT_AFTER = "([{" + "".join(map(chr, (0xA1, 0xBF, 0x201A, 0x201E)))  # with the word after
QUILL_LEFT, QUILL_RIGHT = chr(0x2045), chr(0x2046)  # no twin has them; probed since FX-36
NOT_PROBED = re.compile(r"in no (?:twin|installed font), not probed \(\d+\):(.*)$", re.MULTILINE)


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
    """Two versions have run the full probe: Tyler's 26.8.1.1 and the auditor's 24.2.7.2.
    26.8.0.3 has no entry: its output predates the probe (plan Q-60)."""
    versions = {v["version"].split()[1]: v for v in DATA["versions"]}
    assert sorted(versions) == ["24.2.7.2", "26.8.1.1"]
    for key in ("no_break_before", "no_break_after"):
        assert DATA[key] == sorted({cp for v in versions.values() for cp in v[key]})
    assert set(NO_BREAK_BEFORE) == {*map(chr, DATA["no_break_before"]), *FULLWIDTH_CLOSERS}
    assert set(NO_BREAK_AFTER) == set(map(chr, DATA["no_break_after"]))
    assert set(NO_BREAK_BEFORE) - set(FULLWIDTH_CLOSERS) <= set(MEASURED)
    assert set(NO_BREAK_AFTER) <= set(MEASURED)
    assert set(NO_BREAK_BEFORE) - set(FULLWIDTH_CLOSERS) == {*KEPT_BEFORE, BACKSLASH, QUILL_RIGHT}
    assert set(NO_BREAK_AFTER) == {*KEPT_AFTER, QUILL_LEFT}


def test_each_entry_is_what_its_output_measured():
    """Both versions keep eleven characters with the word before, U+2044 among them, and
    seven with the word after. 24.2.7.2 also keeps the backslash; 26.8.1.1 breaks before
    it. 26.8.1.1's output, since FX-36, also probes the characters no twin has: it keeps
    U+2046 with the word before and U+2045 with the word after. 24.2.7.2's output
    predates FX-36; the auditor re-runs it at the Phase B audit."""
    for version in DATA["versions"]:
        text = (ROOT / version["source"]).read_text(encoding="utf-8")
        assert f"version: {version['version']}\n" in text
        for side in ("before", "after"):
            (line,) = re.findall(rf"^  no break {side} \(\d+\):(.*)$", text, re.MULTILINE)
            assert version[f"no_break_{side}"] == sorted(int(cp[2:], 16) for cp in line.split())
        old = "24.2.7.2" in version["version"]
        after = {chr(c) for c in version["no_break_after"]}
        assert after == set(KEPT_AFTER) | (set() if old else {QUILL_LEFT}), version["version"]
        before = {chr(c) for c in version["no_break_before"]}
        extra = {BACKSLASH} if old else {QUILL_RIGHT}
        assert before == set(KEPT_BEFORE) | extra, version["version"]


def test_neither_version_keeps_the_characters_that_were_only_listed():
    """B-22 item 4 listed % and U+2030, U+00BB, U+201D, U+2019. No probe on either
    version kept any of them, so the estimator breaks there too. (U+2045, which B-25
    item 5 also covered, is kept: FX-36 probed it.)"""
    for ch in "%" + "".join(map(chr, (0x2030, 0xBB, 0x201D, 0x2019))):
        assert ch not in NO_BREAK_BEFORE
        assert break_units(f"a {ch} b") == ["a", ch, "b"]


def test_the_probe_covers_every_non_letter_of_the_measured_set():
    measure_lo = tool("measure_lo")
    chars = measure_lo.break_chars()
    assert chars == [c for c in MEASURED if unicodedata.category(c)[0] != "L" and c not in SPACES]
    assert len(chars) == 202
    for version in DATA["versions"]:
        text = (ROOT / version["source"]).read_text(encoding="utf-8")
        start = text.index("line breaks at a space (B-27 item 3)")
        section = text[start : text.index("\n\n", start)]
        rows = {
            int(cp, 16) for cp in re.findall(r"^  U\+([0-9A-F]{4,5}) .*[Kb-]/[Kb-]$", section, re.M)
        }
        (unprobed,) = NOT_PROBED.findall(section)
        missing = {int(cp[2:], 16) for cp in unprobed.split()}
        assert rows | missing == set(map(ord, chars)) and not rows & missing
        assert len(rows) == (150 if "24.2.7.2" in version["version"] else 202)


def test_every_character_is_probed_on_some_version():
    """FX-36: every non-letter character of the measured set is probed on at least one
    version, except characters no installed font has. 26.8.1.1 probes all 202: the 52 no
    twin has are set in an installed font that has them, and the output names it."""
    chars = set(map(ord, tool("measure_lo").break_chars()))
    probed, no_font = set(), None
    for version in DATA["versions"]:
        text = (ROOT / version["source"]).read_text(encoding="utf-8")
        start = text.index("line breaks at a space (B-27 item 3)")
        section = text[start : text.index("\n\n", start)]
        probed |= {
            int(cp, 16) for cp in re.findall(r"^  U\+([0-9A-F]{4,5}) .*[Kb-]/[Kb-]$", section, re.M)
        }
        if "in no installed font" in section:  # an output with FX-36's probe
            (line,) = NOT_PROBED.findall(section)
            found = {int(cp[2:], 16) for cp in line.split()}
            no_font = found if no_font is None else no_font & found
            assert re.search(r"no twin has these; probed in [A-Z][\w ]+ \(\d+\):", section)
    assert no_font is not None, "no output has FX-36's probe"
    assert chars - probed == no_font == set()


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
