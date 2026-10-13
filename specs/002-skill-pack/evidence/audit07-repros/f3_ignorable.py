"""F3: positive kerning across a default-ignorable format character. B-25 item 4 adds the
positive pairs between adjacent characters as set; Carlito (Calibri) has U+200C, U+200D and
U+200E in its cmap at zero advance, so 'V<U+200D>ĩ' is estimated without the V+ĩ pair, but
HarfBuzz skips the ignorable and LibreOffice applies the pair. Longest accepted text, word
by word. Run from the keyline checkout root with its venv."""
import sys
sys.path.insert(0, "/tmp/keyline-audit07")
from fractions import Fraction
from hx import *
from keyline.fit import fit
from keyline.fit.text import paragraphs
from keyline.packs import resolve
PACK = resolve("swiss")

def longest(fn, ws):
    best = None
    for n in range(1, 600):
        t = " ".join(ws[i % len(ws)] for i in range(n))
        try:
            fn(t)
        except DoesNotFit:
            return best
        best = t
    return best

JOINERS = {"none": "", "ZWNJ U+200C": "‌", "ZWJ U+200D": "‍", "LRM U+200E": "‎"}
for mode in ("presented", "read"):
    v = voice("Calibri")
    d = Deck("swiss", mode, v)
    cases = []
    for jname, j in JOINERS.items():
        ws = [f"V{j}ĩ{j}T{j}ĩ{j}V{j}ĩ", f"T{j}ĩ{j}V{j}ĩ{j}T{j}ĩ"]
        for role, layout, region, style in (("evidence", "keyline:evidence", "main", "body"),
                                            ("statement", "keyline:statement", "main", "lede")):
            mk = lambda dd, t, role=role, region=region, style=style: dd.add(role, "x").text(t, style=style, region=region)
            t = longest(lambda t: mk(Deck("swiss", mode, v), t), ws)
            s = d._setting(PACK.styles[mode][style]); b = PACK.region_box(layout, region)
            n = sum(len(x) for x in fit(s, paragraphs(t), Fraction(b.w, 12700), Fraction(b.h, 12700)))
            cases.append((f"{mode} Calibri {layout} {region} {style}, {jname}: {len(t.split())} words, pen estimates {n} lines",
                          lambda dd, t=t, mk=mk: mk(dd, t), region))
    stem = f"f3-{mode}"
    order = build(d, cases, W / f"{stem}.pptx")
    pdf, imgs = render(W / f"{stem}.pptx")
    measure(order, imgs)
    for i, (label, layout, keep) in enumerate(order):
        y0 = PACK.region_box(layout, keep).y / 12700
        print(f"    {label[:60]}...: LibreOffice lines {len([y for y in lines_on(pdf, 2 * i + 1) if y > y0])}")
