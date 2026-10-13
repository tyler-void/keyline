"""Audit 07 FX-32 (amendment B-27 item 2): some glyphs draw past their advance (Caladea
Bold "f" by 0.078 em, Carlito Bold "ế" by 0.096 em, Gelasio "f"). The fit tables store each
glyph's right reach, and a line's estimated width includes the last glyph's. Before, a
120 pt numeral that ended in such a glyph left the side region by up to 10.7 px: the 0.99
margin does not scale with large type. Repro: evidence/audit07-repros/f1_right.py.
Characters as code points."""

import itertools
import json
from fractions import Fraction as F

import pytest

from keyline.config import load as load_config
from keyline.fit import WEIGHTS, WRAP_MARGIN, Setting, load_table, width
from keyline.packs import resolve
from tests.acceptance.m2 import _lo

pytest.importorskip("pptx")

from keyline.pen import Deck, DoesNotFit

FAMILIES = [f for f, _twin in load_config().portable_fonts]
E_ACUTE = chr(0x1EBF)  # ế
Y_HOOK = chr(0x1B4)  # ƴ
D_CARON = chr(0x10F)  # ď
ZWJ = chr(0x200D)
CASES = [  # mode, family, the audit's value, its tail
    ("presented", "Cambria", "7,1 kf", " kf"),
    ("presented", "Georgia", "1.21f", "f"),
    ("presented", "Calibri", f",,...1{E_ACUTE}", E_ACUTE),
    ("presented", "Arial", f"921{Y_HOOK}", Y_HOOK),
    ("read", "Calibri", f"608 kinh t{E_ACUTE}", f" kinh t{E_ACUTE}"),
    ("read", "Georgia", f"39,77 lo{D_CARON}", f" lo{D_CARON}"),
]


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("weight", WEIGHTS)
def test_the_tables_hold_right_reaches(family, weight):
    t = load_table(family, weight)
    assert t.right and all(v > 0 for v in t.right.values())
    assert set(t.right) <= set(t.advances)


def test_the_audit_glyphs():
    caladea, carlito = load_table("Cambria", "bold"), load_table("Calibri", "bold")
    assert (caladea.right[ord("f")], caladea.units_per_em) == (78, 1000)  # 0.078 em
    assert round(F(carlito.right[ord(E_ACUTE)], carlito.units_per_em), 3) == F(96, 1000)
    assert load_table("Georgia", "bold").right[ord("f")] > 0
    assert ord("1") not in caladea.right and ord("n") not in caladea.right


def plain(setting, text):
    """The advances and the positive kerning pairs, without the last glyph's reach."""
    t = setting.table
    units = sum(t.advance(c) for c in text)
    units += sum(t.kern.get((ord(a), ord(b)), 0) for a, b in itertools.pairwise(text))
    return F(units, t.units_per_em) * setting.size


def test_the_width_adds_the_last_glyphs_reach():
    s = Setting("Cambria", "bold", F(120))
    reach = F(78, 1000) * 120
    assert width(s, "1f") == plain(s, "1f") + reach
    assert width(s, "f1") == plain(s, "f1")  # only the last glyph's
    assert width(s, "ff") == plain(s, "ff") + reach
    calibri = Setting("Calibri", "bold", F(24))
    e_reach = F(calibri.table.right[ord(E_ACUTE)], calibri.table.units_per_em) * 24
    assert width(calibri, f"t{E_ACUTE}") == plain(calibri, f"t{E_ACUTE}") + e_reach
    # a trailing joiner draws nothing: the reach is still the last drawn glyph's
    assert ord(ZWJ) in calibri.table.advances
    joined = f"t{E_ACUTE}{ZWJ}"
    assert width(calibri, joined) == plain(calibri, joined) + e_reach
    caps = Setting("Cambria", "bold", F(120), caps=True)  # set as "KF"
    assert width(caps, "kf") == plain(caps, "KF") + F(caps.table.right.get(ord("F"), 0), 1000) * 120


@pytest.mark.parametrize(("mode", "family", "value", "_tail"), CASES)
def test_the_audit_numerals_count_their_reach(mode, family, value, _tail):
    pack = resolve("swiss")
    style = pack.styles[mode]["numeral"]
    s = Setting(family, style.weight, style.size_pt, line_spacing=style.line_spacing)
    reach = F(s.table.right[ord(value[-1])], s.table.units_per_em) * s.size
    assert reach > 0 and width(s, value) == plain(s, value) + reach


def evidence(tmp_path, values, name):
    path = tmp_path / f"{name}.toml"
    path.write_text(
        'schema = 1\n\n[product]\nname = "Right reach"\nfictional = false\n'
        + "".join(
            f'\n[[evidence]]\nid = "n{i}"\nlabel = "a numeral"\nsource = "test"\n'
            f"value = {json.dumps(v, ensure_ascii=False)}\n"
            for i, v in enumerate(values)
        ),
        encoding="utf-8",
    )
    return str(path)


def accepted(mode, voice, tmp_path, value, name):
    d = Deck(pack="swiss", mode=mode, voice=voice, evidence=evidence(tmp_path, [value], name))
    try:
        d.add("evidence", "x", variant="figure").figure("n0", region="side")
    except DoesNotFit:
        return False
    return True


@_lo.needs_lo(*FAMILIES)
def test_numerals_at_the_limit_stay_in_the_side_region(tmp_path):
    """f1_right.py: per case, the audit's own value when the pen still accepts it, and the
    longest numeral of ones before the same tail. Their ink (the slide less a control)
    ends within 1.5 pt (2 px at 1280 px) of the side region's right edge."""
    pack = resolve("swiss")
    box = _lo.region_pt(pack, "keyline:evidence:figure", "side")
    refused = []
    for k, (mode, family, value, tail) in enumerate(CASES):
        voice = _lo.voice_file(tmp_path, family)
        values = []
        if accepted(mode, voice, tmp_path, value, f"try-{k}"):
            values.append(value)
        else:
            refused.append(value)
        n = 1
        while accepted(mode, voice, tmp_path, "1" * (n + 1) + tail, f"grow-{k}"):
            n += 1
        longest = "1" * n + tail
        assert accepted(mode, voice, tmp_path, longest, f"grow-{k}")
        style = pack.styles[mode]["numeral"]
        s = Setting(family, style.weight, style.size_pt, line_spacing=style.line_spacing)
        assert width(s, longest) <= F(box[2] - box[0]) * WRAP_MARGIN < width(s, "1" + longest)
        values.append(longest)
        d = Deck(pack="swiss", mode=mode, voice=voice, evidence=evidence(tmp_path, values, f"n{k}"))
        for i in range(len(values)):
            d.add("evidence", "x", variant="figure").figure(f"n{i}", region="side")
            d.add("evidence", "x", variant="figure")  # the control
        path = tmp_path / f"right-{k}.pptx"
        d.save(str(path))
        for v, ink in zip(values, _lo.ink_boxes(path, tmp_path / f"lo-{k}"), strict=True):
            assert ink is not None and ink[2] <= box[2] + 1.5, (mode, family, v, ink, box)
    assert refused, "the fix refuses at least one of the audit's values"
