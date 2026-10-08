"""Scripts LibreOffice sets in the theme's CTL/Asian font (cs/ea typeface ""), not the twin,
while the twin HAS the glyphs, so the estimator uses the twin's advances: Hebrew in the
Liberation twins. Longest accepted text, LibreOffice 24.2."""
import sys; sys.path.insert(0, "/tmp/keyline-audit06")
from hx import *
from keyline.pen import Deck, DoesNotFit, PenError

HE = ("שלום עולם זהו מבחן של טקסט ארוך בעברית כדי לבדוק את ההתאמה של השורות בתוך האזור "
      "המוקצה לכותרת ולגוף הטקסט במצגת הזאת עם מילים רבות נוספות לאורך כל השורה").split()

def longest(fn, words):
    best = None
    for n in range(1, 400):
        t = " ".join(words[i % len(words)] for i in range(n))
        try:
            fn(Deck("swiss", MODE, VOICE), t)
        except DoesNotFit:
            return best
        best = t
    return best

for fam in ["Arial", "Times New Roman", "Courier New"]:
    for MODE in ("presented", "read"):
        VOICE = voice(fam)
        d = Deck("swiss", MODE, VOICE)
        cases = []
        h = longest(lambda d, t: d.add("evidence", t), HE)
        cases.append(("evidence headline (Hebrew, longest)", lambda d, h=h: d.add("evidence", h), "title"))
        b = longest(lambda d, t: d.add("evidence", "x").text(t, style="body"), HE)
        cases.append(("evidence main body (Hebrew, longest)", lambda d, b=b: d.add("evidence", "x").text(b, style="body"), "main"))
        s = longest(lambda d, t: d.add("statement", t), HE)
        cases.append(("statement headline (Hebrew, longest)", lambda d, s=s: d.add("statement", s), "title"))
        stem = f"ctl-{MODE}-{fam.replace(' ','')}"
        order = build(d, cases, W / f"{stem}.pptx")
        pdf, imgs = render(W / f"{stem}.pptx")
        print(f"== {MODE} {fam}")
        measure(order, imgs)
