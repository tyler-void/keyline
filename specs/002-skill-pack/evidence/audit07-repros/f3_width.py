"""F3 check: one line of the same words with and without the format characters: LibreOffice's
ink width vs the estimator's width (presented body, Calibri)."""
import sys
sys.path.insert(0, "/tmp/keyline-audit07")
from hx import *
from keyline.fit import width
from keyline.packs import resolve
PACK = resolve("swiss")
v = voice("Calibri")
d = Deck("swiss", "presented", v)
s = d._setting(PACK.styles["presented"]["body"])
cases = []
for jname, j in {"none": "", "ZWNJ": "‌", "ZWJ": "‍", "LRM": "‎"}.items():
    t = " ".join([f"V{j}ĩ{j}T{j}ĩ{j}V{j}ĩ"] * 6)
    cases.append((f"{jname}: estimate {float(width(s, t)) * 1280 / 960:.1f} px", lambda dd, t=t: dd.add("evidence", "x").text(t), "main"))
order = build(d, cases, W / "f3w.pptx")
pdf, imgs = render(W / "f3w.pptx")
for (label, layout, keep), r in zip(order, measure(order, imgs)):
    pass
