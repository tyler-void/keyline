"""(a) LB14 with template placeholders '{{ name }}'; (b) hyphen/en dash/non-breaking hyphen
compounds at the pen's limit; (c) decomposed (NFD) Vietnamese at the limit; (d) a box-drawing
separator (deeper than descent_em) in a bottom-anchored title."""
import sys, unicodedata; sys.path.insert(0, "/tmp/keyline-audit06")
from hx import *
from t_break import make
from keyline.pen import Deck, DoesNotFit

def longest(fn, words, mode="presented", v="neutral"):
    best = None
    for n in range(1, 600):
        t = " ".join(words[i % len(words)] for i in range(n))
        try: fn(Deck("swiss", mode, v), t)
        except DoesNotFit: return best
        best = t
    return best

sc = Deck("swiss", "presented", "neutral")
tmpl = make(sc, "evidence", after_tok="{{")
cases = [("LB14 '{{ ' headline", lambda d, t=tmpl[0]: d.add("evidence", t), "title")]
HY = "state-of-the-art long-term cross-border well–known non‑breaking re‑entry follow-up".split()
h = longest(lambda d, t: d.add("evidence", t), HY)
cases.append(("hyphenated headline at limit", lambda d, h=h: d.add("evidence", h), "title"))
b = longest(lambda d, t: d.add("evidence", "x").text(t), HY)
cases.append(("hyphenated body at limit", lambda d, b=b: d.add("evidence", "x").text(b), "main"))
VN = unicodedata.normalize("NFD", "Người dân miền Tây đã quen với mùa nước nổi từ nhiều thế hệ trước").split()
v = longest(lambda d, t: d.add("evidence", t), VN, v="field")
cases.append(("NFD Vietnamese headline at limit (field)", lambda d, v=v: d.add("evidence", v), "title"))
BX = ["Revenue", "│", "Quarter", "│", "Region"]
cases.append(("box-drawing separator, bottom-anchored title", lambda d: d.add("evidence", "Revenue │ Quarter │ Region"), "title"))
print("LB14 headline:", repr(tmpl[0]))
d = Deck("swiss", "presented", "neutral")
order = build(d, cases[:3] + cases[4:], W / "misc.pptx")
pdf, imgs = render(W / "misc.pptx"); measure(order, imgs)
d = Deck("swiss", "presented", "field")
order = build(d, [cases[3]], W / "misc2.pptx")
pdf, imgs = render(W / "misc2.pptx"); measure(order, imgs)
