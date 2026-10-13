"""B-26 boundary: the kept characters with the largest top and left reach, alone as a
numeral, in each region that allows a figure, both modes, six families. Measures the ink
against the region box, the B-24/B-25 allowances, and the free space (7.09 pt above,
14.17 pt beside)."""
import sys
sys.path.insert(0, "/tmp/keyline-audit07")
sys.path.insert(0, "./tools")
from hx import *
from fit_stress import glyph_top, left_bearings, PX_PER_PT
from keyline.fit import Setting
from keyline.fit.numerals import excluded, reach
from keyline.packs import resolve
PACK = resolve("swiss")
EXC = excluded(PACK)
R = reach()
kept = [c for c in R if c not in EXC and not c.isspace()]
tops = sorted(kept, key=lambda c: -R[c][0])[:6]
lefts = sorted(kept, key=lambda c: -R[c][1])[:4]
extra = [c for c in "ẦỶỒ" if c in kept]
CH = list(dict.fromkeys(tops + lefts + extra))
print("kept, tallest:", tops, "leftmost:", lefts)
REGIONS = [("statement", None, "keyline:statement", "main"), ("evidence", "figure", "keyline:evidence:figure", "side"),
           ("evidence", "figure", "keyline:evidence:figure", "main"), ("close", None, "keyline:close", "main"), ("evidence", None, "keyline:evidence", "main")]
worst = []
for mode in ("presented", "read"):
    for fam in ("Arial", "Georgia", "Calibri", "Cambria", "Times New Roman", "Courier New"):
        v = voice(fam)
        st = PACK.styles[mode]["numeral"]
        vo = PACK.voice(v)
        twin_fam = vo.font(st.font)
        bearings, upm = left_bearings(twin_fam, st.weight)
        chars = [c for c in CH if ord(c) in bearings]
        ev = W / f"b26-{mode}-{fam}.toml"
        lines = ["schema = 1", "", "[product]", 'name = "B26"', "fictional = false"]
        for i, c in enumerate(chars):
            lines += ["", "[[evidence]]", f'id = "c{i}"', f'value = "{c}"', 'label = "a numeral"', 'source = "b26"']
        ev.write_text("\n".join(lines) + "\n", encoding="utf-8")
        d = Deck("swiss", mode, v, evidence=str(ev))
        cases = []
        for i, c in enumerate(chars):
            for role, var, layout, region in REGIONS:
                cases.append(((c, layout, region), lambda dd, i=i, role=role, var=var, region=region: dd.add(role, "x", variant=var).figure(f"c{i}", region=region), region))
        stem = f"b26-{mode}-{fam.replace(' ', '')}"
        order = build(d, [(f"{c[0]}|{c[1]}|{c[2]}", f, k) for c, f, k in cases], W / f"{stem}.pptx")
        import io, contextlib
        pdf, imgs = render(W / f"{stem}.pptx")
        with contextlib.redirect_stdout(io.StringIO()):
            res = measure(order, imgs)
        setting = Setting(twin_fam, st.weight, st.size_pt, line_spacing=st.line_spacing)
        for (label, e) in res:
            c, layout, region = label.split("|")
            top_allow = max(0, (glyph_top(twin_fam, st.weight, c) * float(st.size_pt) - float(setting.first_baseline)) * PX_PER_PT)
            left_allow = max(0, -bearings.get(ord(c), 0) / upm * float(st.size_pt) * PX_PER_PT)
            # the label box also inks; its own allowance is small (14/10 pt caps)
            over_top = e["top"] - top_allow - 2
            over_left = e["left"] - left_allow - 2
            free_above = 7.09 * PX_PER_PT
            worst.append((max(over_top, over_left, e["right"] - 2, e["bottom"] - 2), mode, fam, c, layout, region, e, top_allow, left_allow))
worst.sort(reverse=True, key=lambda x: x[0])
for w in worst[:12]:
    ex, mode, fam, c, layout, region, e, ta, la = w
    print(f"{ex:+.1f} px vs limit | {mode} {fam} {c!r} U+{ord(c):04X} {layout} {region}: " + " ".join(f"{k}{v:+.1f}" for k, v in e.items()) + f" top allowance {ta:.1f} left allowance {la:.1f}; top vs free space above ({7.09*PX_PER_PT:.1f} px): {e['top'] - 7.09*PX_PER_PT:+.1f}")
print("cases:", len(worst), "past a limit:", sum(1 for w in worst if w[0] > 0))
print("max top reach past region top:", max(w[6]["top"] for w in worst), "px; free space above", 7.09 * PX_PER_PT, "px")
for w in sorted(worst, key=lambda w: -w[6]["top"])[:4]:
    print("tallest ink:", w[1], w[2], repr(w[3]), w[4], w[5], f"top {w[6]['top']:+.1f} px, allowance {w[7]:.1f} px")
