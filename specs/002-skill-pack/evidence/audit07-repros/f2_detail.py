"""F2 detail: the presented Arial statement lede, estimator lines vs LibreOffice lines."""
import sys
sys.path.insert(0, "/tmp/keyline-audit07")
from fractions import Fraction
from f2_backslash import *
mode, fam = "presented", "Arial"
v = voice(fam)
mk = lambda dd, t: dd.add("statement", "x").text(t, style="lede", region="main")
t = longest(lambda t: mk(Deck("swiss", mode, v), t))
d = Deck("swiss", mode, v)
s = d._setting(PACK.styles[mode]["lede"])
b = PACK.region_box("keyline:statement", "main")
est = fit(s, paragraphs(t), Fraction(b.w, 12700), Fraction(b.h, 12700))
print("pen accepts:", repr(t))
for i, l in enumerate(est[0]):
    print(f"  estimate line {i+1}: {l}")
order = build(d, [("lede", lambda dd: mk(dd, t), "main")], W / "f2-detail.pptx")
pdf, imgs = render(W / "f2-detail.pptx")
measure(order, imgs)
ws = [w for w in words(pdf) if w[0] == 1 and w[2] > b.y / 12700]
ys = sorted({round(w[4]) for w in ws})
for i, y in enumerate(ys):
    print(f"  LibreOffice line {i+1}: " + " ".join(w[5] for w in ws if round(w[4]) == y))
