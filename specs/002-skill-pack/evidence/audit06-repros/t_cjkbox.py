"""Text boxes (B-21: 1.2 em pitch): mostly Latin lines with one CJK character each."""
import sys; sys.path.insert(0, "/tmp/keyline-audit06")
from hx import *
from keyline.pen import Deck, DoesNotFit

def longest(fn, words, mode, v):
    best = None
    for n in range(1, 800):
        t = " ".join(words[i % len(words)] for i in range(n))
        try:
            fn(Deck("swiss", mode, v), t)
        except DoesNotFit:
            return best
        best = t
    return best

W1 = "revenue in the 市 region grew faster than any other market in the quarter".split()
for fam in ("Arial", "Georgia"):
    for mode in ("presented", "read"):
        v = voice(fam)
        d = Deck("swiss", mode, v)
        cases = []
        b = longest(lambda d, t: d.add("evidence", "x").text(t), W1, mode, v)
        cases.append((f"{fam} {mode} body CJK-sprinkled", lambda d, b=b: d.add("evidence", "x").text(b), "main"))
        h = longest(lambda d, t: d.add("statement", t), W1, mode, v)
        cases.append((f"{fam} {mode} statement title", lambda d, h=h: d.add("statement", h), "title"))
        e = longest(lambda d, t: d.add("evidence", t), W1, mode, v)
        cases.append((f"{fam} {mode} evidence title", lambda d, e=e: d.add("evidence", e), "title"))
        items = [longest(lambda d, t: d.add("evidence", "x").bullets([t]), W1, mode, v)]
        cases.append((f"{fam} {mode} one bullet", lambda d, i=items: d.add("evidence", "x").bullets(i), "main"))
        stem = f"cjkbox-{mode}-{fam}"
        order = build(d, cases, W / f"{stem}.pptx")
        pdf, imgs = render(W / f"{stem}.pptx")
        measure(order, imgs)
