"""Audit 06 FX-26 (amendment B-25 item 4): a word's width is its advances plus its positive
kerning pairs inside the measured set; negative pairs are ignored. Carlito (Calibri) has
V+ĩ and T+ĩ at +0.063 em, Caladea (Cambria) f+’ at +0.083 em. Before the fix, repeated
"Vĩ Tĩ" in a Calibri voice ended +74.6 px below a statement title, and "staff’s" in Cambria
+24.8 px below the body (LibreOffice 24.2). Repro: evidence/audit06-repros/t_kern.py."""

from fractions import Fraction as F

import pytest

from keyline.config import load as load_config
from keyline.fit import WEIGHTS, Setting, load_table, width
from keyline.fit.text import measured
from keyline.packs import resolve
from tests.acceptance.m2 import _lo

pytest.importorskip("pptx")

from keyline.pen import Deck, DoesNotFit

FAMILIES = [f for f, _twin in load_config().portable_fonts]
I_TILDE, RSQUO = chr(0x129), chr(0x2019)
VI_TI = f"V{I_TILDE} T{I_TILDE}"
STAFFS = f"chef{RSQUO}s staff{RSQUO}s cliff{RSQUO}s"


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("weight", WEIGHTS)
def test_the_tables_hold_positive_pairs_of_the_measured_set(family, weight):
    t = load_table(family, weight)
    assert all(v > 0 for v in t.kern.values())
    assert all(measured(chr(a)) and measured(chr(b)) for a, b in t.kern)
    assert all(a in t.advances and b in t.advances for a, b in t.kern)


def test_the_audit_pairs_and_the_width():
    carlito = load_table("Calibri", "regular")
    assert carlito.kern[ord("V"), 0x129] == 130 and carlito.units_per_em == 2048
    assert load_table("Cambria", "regular").kern[ord("f"), 0x2019] == 83
    s = Setting("Calibri", "regular", F(24))
    plain = F(carlito.advances[ord("V")] + carlito.advances[0x129], 2048) * 24
    assert width(s, f"V{I_TILDE}") == plain + F(130, 2048) * 24
    assert (
        width(s, f"{I_TILDE}V")
        == F(carlito.advances[0x129] + carlito.advances[ord("V")], 2048) * 24
    )


def longest(accepts, unit, limit=600):
    lo, hi = 0, 1
    while hi <= limit and accepts(" ".join([unit] * hi)):
        lo, hi = hi, hi * 2
    hi = min(hi, limit + 1)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if accepts(" ".join([unit] * mid)) else (lo, mid)
    assert lo > 0
    return " ".join([unit] * lo)


def accepts(deck, role, region):
    def run(text):
        before = len(deck._slides)
        try:
            s = deck.add(role, text if region == "title" else "Text")
            if region != "title":
                s.text(text)
        except DoesNotFit:
            return False
        finally:
            del deck._slides[before:]
        return True

    return run


@_lo.needs_lo("Calibri", "Cambria")
@pytest.mark.parametrize("mode", ["presented", "read"])
def test_the_longest_kerned_texts_stay_in_their_region(mode, tmp_path):
    pack = resolve("swiss")
    cases = [
        ("Calibri", "statement", "title", VI_TI),
        ("Calibri", "evidence", "title", VI_TI),
        ("Calibri", "evidence", "main", VI_TI),
        ("Cambria", "evidence", "title", STAFFS),
        ("Cambria", "evidence", "main", STAFFS),
    ]
    built = []
    for i, (family, role, region, unit) in enumerate(cases):
        d = Deck(pack="swiss", mode=mode, voice=_lo.voice_file(tmp_path, family))
        scratch = Deck(pack="swiss", mode=mode, voice=_lo.voice_file(tmp_path, family))
        text = longest(accepts(scratch, role, region), unit)
        s = d.add(role, text if region == "title" else "Text")
        if region != "title":
            s.text(text)
        d.save(str(tmp_path / f"k{i}.pptx"))
        layout = pack.roles[role].layouts[0]
        built.append((f"{family} {role} {region}", tmp_path / f"k{i}.pptx", layout, region))
    for name, path, layout, region in built:
        (page,) = _lo.chars(path, tmp_path / f"lo-{path.stem}")
        box = _lo.region_pt(pack, layout, region)
        mine = [c for c in page if c[4] > box[1] - 20] if region == "main" else page
        assert max(c[4] for c in mine) <= box[3] + 1.5, name  # 2 px at 1280 px
        assert max(c[3] for c in mine) <= box[2] + 1.5, name
