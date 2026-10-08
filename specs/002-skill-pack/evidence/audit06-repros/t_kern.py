"""Positive kerning: the estimator sums advances without kerning (§6.4); Carlito (Calibri)
has positive pairs such as V+ĩ and T+ĩ (+0.063 em), Caladea (Cambria) f+’ (+0.083 em).
Longest accepted text, LibreOffice 24.2: does LibreOffice set more lines?"""
import sys; sys.path.insert(0, "/tmp/keyline-audit06")
from hx import *
from keyline.pen import Deck, DoesNotFit

def longest(fn, words, mode, v):
    best = None
    for n in range(1, 600):
        t = " ".join(words[i % len(words)] for i in range(n))
        try:
            fn(Deck("swiss", mode, v), t)
        except DoesNotFit:
            return best
        best = t
    return best

PROV = "Vĩnh Long, Hà Tĩnh, Vĩnh Phúc, Vĩnh Yên, Tĩnh Gia, Vĩnh Châu,".split()
ADV = ["Vĩ", "Tĩ"]
CAMB = "chef’s staff’s cliff’s".split()
for fam, texts in (("Calibri", {"provinces": PROV, "adversarial": ADV}), ("Cambria", {"staff’s": CAMB})):
    for mode in ("presented", "read"):
        v = voice(fam)
        d = Deck("swiss", mode, v)
        cases = []
        for name, ws in texts.items():
            h = longest(lambda d, t: d.add("evidence", t), ws, mode, v)
            cases.append((f"{fam} {mode} headline {name}", lambda d, h=h: d.add("evidence", h), "title"))
            b = longest(lambda d, t: d.add("evidence", "x").text(t), ws, mode, v)
            cases.append((f"{fam} {mode} body {name}", lambda d, b=b: d.add("evidence", "x").text(b), "main"))
            s = longest(lambda d, t: d.add("statement", t), ws, mode, v)
            cases.append((f"{fam} {mode} statement {name}", lambda d, s=s: d.add("statement", s), "title"))
        stem = f"kern-{mode}-{fam}"
        order = build(d, cases, W / f"{stem}.pptx")
        pdf, imgs = render(W / f"{stem}.pptx")
        measure(order, imgs)
