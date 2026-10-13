"""Sweep: descender-heavy Vietnamese/Latin and punctuation runs at the longest the pen
accepts, word by word: bottom-anchored titles, tables, bullets, caps labels, attribution.
Measured as AC-13(b) with B-24/B-25 allowances (computed from the twin, chars as set)."""
import sys, io, contextlib
sys.path.insert(0, "/tmp/keyline-audit07")
sys.path.insert(0, "./tools")
from hx import *
from fit_stress import glyph_top, left_bearings, PX_PER_PT
from keyline.fit import Setting
from keyline.packs import resolve
PACK = resolve("swiss")
CORPORA = {
    "desc": "Mỹ Tỵ Kỷ Lý Quý Thủy Gấp Pháp Giày Quậy Ngày Vậy Tỷ Dặm Ąę Ţş Męąţ Quỵ Gỹ ỹ ỷ ỵ ţęş jąg".split(),
    "punct": "… — – ‘a’ “b” «c» ‹d› 5‰ 3′ 4″ €12 12₫ ¥7 x—y a–b ‚q‘ „w“ ‘’ “” —–— ……".split(),
}
def longest(fn, ws, start=0):
    best = None
    for n in range(1, 500):
        t = " ".join(ws[(start + i) % len(ws)] for i in range(n))
        try:
            fn(t)
        except DoesNotFit:
            return best
        except PenError as e:
            return best
        best = t
    return best
def table_fn(t):
    w = t.split(); k = max(1, len(w) // 6)
    cells = [" ".join(w[i*k:(i+1)*k]) or "x" for i in range(8)]
    return [cells[0:2], cells[2:4], cells[4:6], cells[6:8]]
ITEMS = [
    ("cover title", lambda d, t: d.add("cover", t), "title", ["cover_title"]),
    ("evidence title", lambda d, t: d.add("evidence", t), "title", ["headline"]),
    ("close title", lambda d, t: d.add("close", t), "title", ["cover_title"]),
    ("statement title", lambda d, t: d.add("statement", t), "title", ["statement"]),
    ("section label", lambda d, t: d.add("section", "x").text(t, style="label"), "main", ["label"]),
    ("quote attribution", lambda d, t: d.add("quote", "x").attribution(t), "main", ["label"]),
    ("bullets", lambda d, t: d.add("evidence", "x").bullets([t, t]), "main", ["body"]),
    ("table", lambda d, t: d.add("evidence", "x").table(table_fn(t)), "main", ["body", "label"]),
    ("side body", lambda d, t: d.add("evidence", "x", variant="figure").text(t, region="side"), "side", ["body"]),
]
fams = sys.argv[1:] or ["Arial", "Georgia", "Calibri", "Times New Roman", "Courier New", "Cambria"]
rows = []
for mode in ("presented", "read"):
    for fam in fams:
        v = voice(fam); vo = PACK.voice(v)
        d = Deck("swiss", mode, v)
        cases = []
        for cname, ws in CORPORA.items():
            if fam == "Cambria" and cname == "desc":
                continue  # Caladea lacks Vietnamese (out of scope)
            for k, (name, fn, keep, styles) in enumerate(ITEMS):
                t = longest(lambda t: fn(Deck("swiss", mode, v), t), ws, start=3 * k)
                if t is None:
                    continue
                shown = t
                ta = la = 0.0
                for sn in styles:
                    st = PACK.styles[mode][sn]
                    tf = vo.font(st.font)
                    chars = {c for c in (t.upper() if st.caps else t) if not c.isspace()} | ({st.bullet_marker} if name == "bullets" and st.bullet_marker else set())
                    top = max(glyph_top(tf, st.weight, c) for c in chars)
                    se = Setting(tf, st.weight, st.size_pt, line_spacing=st.line_spacing)
                    ta = max(ta, (top * float(st.size_pt) - float(se.first_baseline)) * PX_PER_PT)
                    b, upm = left_bearings(tf, st.weight)
                    la = max(la, -min(b.get(ord(c), 0) for c in chars) / upm * float(st.size_pt) * PX_PER_PT)
                cases.append((f"{mode}|{fam}|{cname}|{name}|{ta:.2f}|{la:.2f}|{len(t.split())}", lambda dd, t=t, fn=fn: fn(dd, t), keep))
        stem = f"sweep-{mode}-{fam.replace(' ', '')}"
        order = build(d, cases, W / f"{stem}.pptx")
        pdf, imgs = render(W / f"{stem}.pptx")
        with contextlib.redirect_stdout(io.StringIO()):
            res = measure(order, imgs)
        for label, e in res:
            m, f, c, n, ta, la, nw = label.split("|")
            ta, la = float(ta), float(la)
            ex = {"left": e["left"] - la, "top": e["top"] - ta, "right": e["right"], "bottom": e["bottom"]} if e else None
            worst = max(ex, key=ex.get) if ex else None
            rows.append((ex[worst] - 2 if ex else None, label, worst, e))
rows.sort(key=lambda r: -(r[0] if r[0] is not None else 99))
for r in rows[:10]:
    print(f"{r[0]:+.1f} px past the {r[2]} limit | {r[1]} | " + " ".join(f"{k}{v:+.1f}" for k, v in r[3].items()))
print("texts:", len(rows), "past a limit:", sum(1 for r in rows if r[0] is not None and r[0] > 0), "no ink:", sum(1 for r in rows if r[0] is None))
