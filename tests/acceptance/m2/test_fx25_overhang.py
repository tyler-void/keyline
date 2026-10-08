"""Audit 06 FX-25 (amendment B-25 items 2 and 3): diacritics stacked on a capital rise above
the cap line, and so above a region's top, as punctuation hangs into a margin. AC-13(b)'s
top edge gets an allowance: size × (the highest glyph top among the text's characters −
the first baseline) when positive, the first baseline being 1.2 em × line spacing − 0.2 em
(B-21, measured on both LibreOffice versions). The pack invariant: in every region, for
every style allowed there and every portable family, the largest top and left overhang
over the measured set is smaller than the free space beside the region. Repros:
evidence/audit06-repros/t_top.py and t_top2.py. Characters as code points."""

import re
from fractions import Fraction as F

import pytest

from keyline.config import load as load_config
from keyline.fit import BELOW_BASELINE_EM, Setting, load_table
from keyline.packs import resolve
from tests.acceptance.m2 import _lo
from tests.conftest import ROOT

pytest.importorskip("pptx")

from keyline.pen import Deck, DoesNotFit
from keyline.pen._regions import rule_box

FAMILIES = [f for f, _twin in load_config().portable_fonts]
EMU_PER_PT = 12700
SLIDE_W, SLIDE_H = 12192000, 6858000
EVIDENCE = ROOT / "specs/002-skill-pack/evidence"
MEASUREMENTS = {
    "24.2.7.2": EVIDENCE / "audit06-repros/measure_lo-on-24.2.7.2.txt",
    "26.8.0.3": EVIDENCE / "lo-26.8.0.3-measurements.txt",
}
PITCH = re.compile(
    r"^\s+(?P<family>[A-Z][\w ]+?)\s+(?P<weight>regular|bold)\s+(?P<size>[\d.]+)\s+"
    r"(?P<ls>[\d.]+)\s+(?:br|p)\s+(?:-?[\d.]+\s+){4}(?P<first>[\d.]+)\s"
)
A_HOOK = chr(0x1EA8)  # Ẩ, LATIN CAPITAL LETTER A WITH CIRCUMFLEX AND HOOK ABOVE
A_BREVE_HOOK = chr(0x1EB2)  # Ẳ
O_TILDE = chr(0x1ED6)  # Ỗ
SO = "s" + chr(0x1ED1)  # số
THUC = "th" + chr(0x1EF1) + "c"  # thực


def first_baselines(path):
    """(size, line spacing, first baseline in em) per pitch probe of a measure_lo output."""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("pitch: four lines"))
    end = next(i for i in range(start, len(lines)) if not lines[i].strip())
    found = [PITCH.match(line) for line in lines[start:end]]
    return [(float(m["size"]), F(m["ls"]), float(m["first"])) for m in found if m]


@pytest.mark.parametrize("version", list(MEASUREMENTS))
def test_the_first_baseline_is_measured(version):
    """1.00 em below the box's top at line spacing 1.0, 1.12 em at 1.1: within 0.06 pt
    (two of LibreOffice's 0.01 mm units) on every probe."""
    probes = first_baselines(MEASUREMENTS[version])
    assert len(probes) == 198 and {ls for _s, ls, _f in probes} == {1, F(11, 10)}
    for size, ls, first in probes:
        model = Setting("Arial", "regular", F(size), line_spacing=ls).first_baseline
        assert abs(first * size - float(model)) <= 0.06, (version, size, ls, first)
    assert F(6, 5) * F(11, 10) - BELOW_BASELINE_EM == F(28, 25)  # 1.12 em


def test_the_overhangs():
    s = Setting("Georgia", "bold", F(60))
    gelasio = load_table("Georgia", "bold")
    assert s.first_baseline == 60
    assert s.top_overhang == 60 * gelasio.top_em - 60 > 0
    assert s.left_overhang == 60 * gelasio.left_em
    arial = Setting("Arial", "regular", F(24), line_spacing=F(11, 10))
    assert arial.first_baseline == 24 * F(28, 25) and arial.top_overhang == 0


# -- the pack invariant (B-25 item 3) -----------------------------------------------------


def styles_in(pack, mode, role, region):
    """The styles a region may set text in: the role's title style in the title, the
    source and note styles in the footer, and every other component's styles elsewhere."""
    components = pack.roles[role].components[mode]
    if region == "title":
        return [pack.roles[role].title]
    footer = ("source", "note")
    keys = footer if region == "footer" else [k for k in components if k not in footer]
    return list(dict.fromkeys(s for k in keys for s in components.get(k, ())))


def free_space(pack, role, layout, region):
    """(above, left) of a region, in pt: the gap to the nearest region or keyline rule
    above it (or to its left) that overlaps it, or to the slide's edge."""
    boxes = [pack.region_box(layout, r) for r in pack.regions[layout] if r != region]
    if role == "evidence":
        boxes.append(rule_box(pack))
    b = pack.region_box(layout, region)
    x0, y0, x1, y1 = b.x, b.y, b.x + b.w, b.y + b.h
    above = [o.y + o.h for o in boxes if o.x < x1 and o.x + o.w > x0 and o.y + o.h <= y0]
    left = [o.x + o.w for o in boxes if o.y < y1 and o.y + o.h > y0 and o.x + o.w <= x0]
    return F(y0 - max(above, default=0), EMU_PER_PT), F(x0 - max(left, default=0), EMU_PER_PT)


def overhangs(mode):
    """Per region, style and family of the Swiss pack: (where, top overhang, free above,
    left overhang, free to the left), in pt."""
    pack = resolve("swiss")
    out = []
    for role in pack.roles:
        for layout in pack.roles[role].layouts:
            for region in pack.regions[layout]:
                above, left = free_space(pack, role, layout, region)
                for name in styles_in(pack, mode, role, region):
                    style = pack.styles[mode][name]
                    for family in FAMILIES:
                        s = Setting(
                            family, style.weight, style.size_pt, line_spacing=style.line_spacing
                        )
                        where = f"{mode} {layout} {region} {name} {family}"
                        out.append((where, s.top_overhang, above, s.left_overhang, left))
    return out


@pytest.mark.xfail(
    strict=True,
    reason="FX-25: the numeral style fails the invariant (Gelasio's stacked capitals above "
    "the main regions, U+2044 left of the side region); the remedy is Tyler's call",
)
@pytest.mark.parametrize("mode", ["presented", "read"])
def test_the_pack_holds_its_overhangs(mode):
    found = overhangs(mode)
    assert len({w.split()[1] for w, *_ in found}) == 7  # every layout
    bad = [
        f"{where}: top {float(top):.1f} pt / {float(above):.1f} free, "
        f"left {float(lft):.1f} pt / {float(left):.1f} free"
        for where, top, above, lft, left in found
        if top >= above or lft >= left
    ]
    assert not bad, "\n".join(bad)


# -- LibreOffice: the audit's titles, within the top allowance ----------------------------


def allowance_pt(setting, text):
    """B-25 item 2's top allowance, from the twin's outlines (tools/fit_stress.py)."""
    from tests.acceptance.m2.test_ac13b_fit_stress import fit_stress

    top = max(fit_stress.glyph_top(setting.family, setting.weight, c) for c in text if c != " ")
    return max(0.0, top * float(setting.size) - float(setting.first_baseline))


def covers(family, text):
    """Whether the family's twin has every character of the text, in both weights (B-25
    item 1: a fallback font sets the others, and nothing is promised for them)."""
    return all(ord(c) in load_table(family, w).advances for w in ("regular", "bold") for c in text)


def longest_title(voice, mode, role, first):
    filler = (
        "v" + chr(0xE0) + " nh" + chr(0x1EEF) + "ng " + chr(0x111) + "i" + chr(0x1EC1) + "u"
        " ch" + chr(0x1B0) + "a t" + chr(0x1EEB) + "ng " + chr(0x111) + chr(0x1B0) + chr(0x1EE3)
        + "c k" + chr(0x1EC3) + " v" + chr(0x1EC1) + " th" + chr(0x1ECB) + " tr" + chr(0x1B0)
        + chr(0x1EDD) + "ng mi" + chr(0x1EC1) + "n T" + chr(0xE2) + "y n" + chr(0x103) + "m nay"
    ).split()  # fmt: skip
    best = first
    for n in range(1, len(filler) + 1):
        text = " ".join([first, *filler[:n]])
        try:
            Deck(pack="swiss", mode=mode, voice=voice).add(role, text)
        except DoesNotFit:
            break
        best = text
    return best


@_lo.needs_lo(*FAMILIES)
@pytest.mark.parametrize("mode", ["presented", "read"])
def test_tall_capitals_stay_within_the_top_allowance(mode, tmp_path):
    """t_top.py and t_top2.py: short and two-line titles that open on stacked capitals, in
    each family whose twin has them (Caladea does not). Each glyph's top stays within the
    region's top less the allowance and 1.5 pt (2 px at 1280 px), and never reaches the box
    or rule above."""
    pack = resolve("swiss")
    tall = O_TILDE + A_BREVE_HOOK + A_HOOK + SO + THUC
    families = [f for f in FAMILIES if covers(f, tall)]
    assert families == [f for f in FAMILIES if f != "Cambria"]
    for family in families:
        voice = _lo.voice_file(tmp_path, family)
        cases = [  # role, region, style (None: the title's), text
            ("statement", "title", None, f"{A_HOOK}n {SO}"),
            ("statement", "title", None, f"{O_TILDE} {A_BREVE_HOOK} {A_HOOK}"),
            ("section", "title", None, f"{A_HOOK}m {THUC}"),
            ("quote", "title", None, f"{A_HOOK}n m" + chr(0xEC) + "nh"),
            ("evidence", "title", None, longest_title(voice, mode, "evidence", f"{A_HOOK}n {SO}")),
            ("cover", "title", None, longest_title(voice, mode, "cover", f"{A_HOOK}n {SO}")),
            ("statement", "main", "lede", f"{A_HOOK}m {THUC} Vi" + chr(0x1EC7) + "t Nam"),
            ("section", "main", "label", chr(0x1EA9) + f"m {THUC}"),  # caps: set as Ẩ
            ("close", "main", "lede", f"{A_HOOK}n {SO}"),
        ]
        d = Deck(pack="swiss", mode=mode, voice=voice)
        for role, region, style, text in cases:
            if region == "title":
                d.add(role, text)
            else:
                d.add(role, "x").text(text, style=style)
        path = tmp_path / f"top-{family.replace(' ', '')}.pptx"
        d.save(str(path))
        pages = _lo.chars(path, tmp_path / f"lo-{path.stem}")
        for (role, region, name, text), page in zip(cases, pages, strict=True):
            layout = pack.roles[role].layouts[0]
            style = pack.styles[mode][name or pack.roles[role].title]
            s = Setting(family, style.weight, style.size_pt, line_spacing=style.line_spacing)
            box = _lo.region_pt(pack, layout, region)
            above, _left = free_space(pack, role, layout, region)
            title_bottom = _lo.region_pt(pack, layout, "title")[3]
            mine = [c for c in page if (region == "title") == (c[2] + c[4] < 2 * title_bottom)]
            top = min(c[2] for c in mine)
            shown = text.upper() if style.caps else text
            where = (mode, family, role, region, text)
            assert top >= box[1] - allowance_pt(s, shown) - 1.5, where
            assert top > box[1] - float(above), where
