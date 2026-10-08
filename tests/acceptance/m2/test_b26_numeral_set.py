"""Amendment B-26 (the ruling on Q-52): a figure's value uses only the numeral set, B-25's
measured set minus every character whose top or left reach, in any of the six twins at
either mode's numeral size, is not smaller than the smallest free space above, or beside,
a region that allows a figure. tools/gen_fit_tables.py derives the excluded characters and
commits them with the twins' versions (fit/tables/numerals.json); the tests re-derive
them. The pen and `keyline brief` refuse any other character in a figure's value, naming
it and suggesting the label. Characters as code points."""

import dataclasses
import hashlib
import json
import re
import shutil
import subprocess
import sys
import unicodedata

import pytest

from keyline.brief import BriefError, load_evidence
from keyline.config import load as load_config
from keyline.fit import VIETNAMESE, WEIGHTS, load_table
from keyline.fit.numerals import NUMERALS, derive, excluded, limits, numeral_problem, reach
from keyline.fit.text import MEASURED, inked, measured
from keyline.packs import bundled, resolve
from tests.acceptance._cli import keyline
from tests.acceptance.m2 import _lo
from tests.conftest import FIXTURES, ROOT

pytest.importorskip("pptx")

from keyline.pen import Deck, PenError

DATA = json.loads(NUMERALS.read_text(encoding="utf-8"))
FAMILIES = [f for f, _twin in load_config().portable_fonts]
A_HOOK = chr(0x1EA8)  # Ẩ: excluded, top
A_GRAVE = chr(0x1EA6)  # Ầ: the tallest character kept (Gelasio, 1.057 em)
F_HOOK = chr(0x192)  # ƒ: the character kept that reaches furthest left (0.093 em)
FRACTION_SLASH = chr(0x2044)  # excluded, left
MINUS = chr(0x2212)  # outside the measured set
TY = "t" + chr(0x1EF7)  # tỷ
DONG = chr(0x111) + chr(0x1ED3) + "ng"  # đồng
NAM = "n" + chr(0x103) + "m"  # năm


def test_the_committed_list_is_derived():
    """For every bundled pack, the committed list is what the reach and the pack give."""
    for name in bundled():
        pack, committed = resolve(name), DATA["packs"][name]
        listed = {chr(cp): edge for cp, ch, edge in committed["excluded"]}
        assert all(chr(cp) == ch for cp, ch, _edge in committed["excluded"])
        assert listed == derive(pack, reach()) == excluded(pack)
        lim = limits(pack)
        assert committed["free_above_emu"] == lim["free_above_emu"]
        assert committed["free_left_emu"] == lim["free_left_emu"]
        assert committed["numeral"] == {
            mode: {"size_pt": str(size), "line_spacing": str(ls), "caps": caps}
            for mode, (size, ls, caps) in lim["numeral"].items()
        }


def test_the_swiss_numeral_set():
    """37 excluded: capitals with stacked marks at the top; Ɲ, Ȉ, ȉ and the fraction slash
    at the side region's left. Lowercase Vietnamese is kept."""
    out = excluded(resolve("swiss"))
    assert len(out) == 37
    tops = [c for c, edge in out.items() if edge == "top"]
    assert len(tops) == 33 and all(unicodedata.category(c) == "Lu" for c in tops)
    assert {c for c, edge in out.items() if edge == "left"} == {
        chr(0x19D),
        chr(0x208),
        chr(0x209),
        FRACTION_SLASH,
    }
    assert out[A_HOOK] == "top" and A_GRAVE not in out and F_HOOK not in out
    assert not {c for c in VIETNAMESE if c.islower()} & set(out)
    assert all(measured(c) for c in out)


def test_the_reach_agrees_with_the_tables():
    """The reach is per character what the tables hold as maxima, over the same twins."""
    r = reach()
    tables = [load_table(f, w) for f in FAMILIES for w in WEIGHTS]
    assert max(top for top, _left in r.values()) == max(t.top_em for t in tables)
    assert max(left for _top, left in r.values()) == max(t.left_em for t in tables)
    assert set(r) <= set(MEASURED) and all(inked(c) for c in r)
    twins = {(t["family"], t["weight"]): t["sha256"] for t in DATA["twins"]}
    assert twins == {(t.family, t.weight): t.source["sha256"] for t in tables}


def _installed(family, weight):
    style = "Bold" if weight == "bold" else "Regular"
    out = subprocess.run(
        ["fc-match", "-f", "%{file}", f"{family}:style={style}"], capture_output=True, text=True
    )
    try:
        with open(out.stdout.strip(), "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


@pytest.mark.skipif(shutil.which("fc-match") is None, reason="fc-match is not installed")
def test_the_rebuild_derives_the_same_list():
    """From the installed twins: byte-identical, when they are the files the data used."""
    pytest.importorskip("fontTools")
    other = [
        f"{t['twin']} {t['weight']}"
        for t in DATA["twins"]
        if _installed(t["family"], t["weight"]) != t["sha256"]
    ]
    if other:
        pytest.skip(f"installed font files differ from the data's: {', '.join(other)}")
    sys.path.insert(0, str(ROOT / "tools"))
    import gen_fit_tables

    assert gen_fit_tables.numerals() == NUMERALS.read_text(encoding="utf-8")


def test_a_pack_directory_gets_its_own():
    pack = resolve(FIXTURES / "briefs/packs/presented-only")
    assert list(limits(pack)["numeral"]) == ["presented"]
    assert excluded(pack) == derive(pack, reach()) and A_HOOK in excluded(pack)


# -- the pen and `keyline brief` -----------------------------------------------------------

HEAD = 'schema = 1\n\n[product]\nname = "Numerals"\nfictional = false\n'


def evidence(tmp_path, value, name="numerals"):
    """An evidence file whose entry "n" has this value; or, for a list of values, entries
    "n0", "n1", …"""
    values = {"n": value} if isinstance(value, str) else {f"n{i}": v for i, v in enumerate(value)}
    path = tmp_path / f"{name}.toml"
    path.write_text(
        HEAD
        + "".join(
            f'\n[[evidence]]\nid = "{eid}"\nlabel = "a numeral"\nsource = "test"\n'
            f"value = {json.dumps(v, ensure_ascii=False)}\n"
            for eid, v in values.items()
        ),
        encoding="utf-8",
    )
    return path


REFUSED = {
    "stacked capital": (f"{A_HOOK}n 12", "U+1EA8", "reaches above"),
    "decomposed": (unicodedata.normalize("NFD", f"{A_HOOK}n 12"), "U+1EA8", "reaches above"),
    "fraction slash": (f"1{FRACTION_SLASH}2", "U+2044", "reaches left of"),
    "minus sign": (f"{MINUS}0.4%", "U+2212", "outside the measured set"),
}


@pytest.mark.parametrize("name", list(REFUSED))
def test_a_value_outside_the_numeral_set_is_refused(name, tmp_path):
    value, code, why = REFUSED[name]
    path = evidence(tmp_path, value)
    swiss = resolve("swiss")
    code = re.escape(code)
    with pytest.raises(BriefError, match=f"value: contains {code} .*{why}.*put it in the label"):
        load_evidence([str(path)], "presented", swiss)
    with pytest.raises(PenError, match=f"contains {code}.*put it in the label"):
        Deck(pack="swiss", mode="read", voice="field", evidence=str(path))
    load_evidence([str(path)])  # without a pack there is no figure region to measure


@pytest.mark.parametrize("value", [f"12 {TY} " + chr(0x20AB), f"3 {DONG}", f"{NAM} 2026"])
def test_vietnamese_numerals_stay(value, tmp_path):
    assert numeral_problem(value, resolve("swiss")) is None
    d = Deck(pack="swiss", mode="presented", voice="field", evidence=str(evidence(tmp_path, value)))
    d.add("evidence", "A figure").figure("n")


def test_the_label_takes_what_the_numeral_cannot(tmp_path):
    d = Deck(pack="swiss", mode="presented", voice="field", evidence=str(evidence(tmp_path, "12")))
    d.add("evidence", "A figure").figure("n", label=f"{A_HOOK}n {FRACTION_SLASH} {MINUS}")


def test_figure_checks_again(tmp_path):
    """An entry that bypassed the loader is refused at the verb, naming the character."""
    d = Deck(pack="swiss", mode="presented", voice="field", evidence=str(evidence(tmp_path, "12")))
    entries = d._evidence.entries
    entries["n"] = dataclasses.replace(entries["n"], value=f"{A_HOOK} 12")
    with pytest.raises(PenError, match=r"numeral .* contains U\+1EA8 .*put it in the label"):
        d.add("evidence", "A figure").figure("n")


def test_keyline_brief_refuses(tmp_path):
    path = evidence(tmp_path, f"{A_HOOK}n 12")
    brief = tmp_path / "b.brief.toml"
    valid = (FIXTURES / "briefs/valid.brief.toml").read_text(encoding="utf-8")
    start = valid.index("evidence = [")
    end = valid.index("\n", start)
    brief.write_text(valid[:start] + f'evidence = ["{path.name}"]' + valid[end:], encoding="utf-8")
    proc = keyline("brief", brief)
    assert proc.returncode != 0
    err = proc.stderr.decode()
    assert "U+1EA8" in err and "put it in the label" in err


# -- LibreOffice: the characters kept at the edge stay clear -------------------------------


@_lo.needs_lo(*FAMILIES)
@pytest.mark.parametrize("mode", ["presented", "read"])
def test_the_edge_characters_stay_clear(mode, tmp_path):
    """Ầ, the tallest character kept, under the statement's title and the evidence rule;
    ƒ, the one reaching furthest left, in the side region. Each numeral's ink (the slide
    less a control without the figure, at 8 px per pt) stays below the box or rule above
    its region, and right of the region on its left. pdfium's character boxes are not
    used: for Gelasio Bold's Ầ, a composite glyph, they give the stored bounds (2170 of
    2048 units), 0.46 pt above the outline (2162.8) that LibreOffice draws."""
    pack = resolve("swiss")
    cases = [  # role, variant, region, value
        ("statement", None, "main", f"{A_GRAVE}12"),
        ("evidence", None, "main", f"{A_GRAVE}12"),
        ("evidence", "figure", "side", f"{F_HOOK}12"),
    ]
    edge = A_GRAVE + F_HOOK
    for family in FAMILIES:
        if not all(ord(c) in load_table(family, "bold").advances for c in edge):
            continue  # Caladea lacks Ầ
        voice = _lo.voice_file(tmp_path, family)
        stem = family.replace(" ", "")
        values = evidence(tmp_path, [value for *_, value in cases], stem)
        path = tmp_path / f"{stem}.pptx"
        d = Deck(pack="swiss", mode=mode, voice=voice, evidence=str(values))
        for i, (role, variant, region, _value) in enumerate(cases):
            d.add(role, "x", variant=variant).figure(f"n{i}", region=region)
            d.add(role, "x", variant=variant)  # the control
        d.save(str(path))
        for (role, variant, region, value), ink in zip(
            cases, _lo.ink_boxes(path, tmp_path / f"lo-{stem}"), strict=True
        ):
            layout = f"keyline:{role}" + (f":{variant}" if variant else "")
            box = _lo.region_pt(pack, layout, region)
            above, left = (x / 12700 for x in pack.free_space(layout, region))
            where = (mode, family, layout, region, value)
            assert ink is not None, where
            assert ink[1] > box[1] - above and ink[0] > box[0] - left, (where, ink, box)
