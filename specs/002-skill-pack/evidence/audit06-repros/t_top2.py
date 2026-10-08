"""Top edge across the six families; bottom-anchored 2-line titles with a tall capital in line 1."""
import sys; sys.path.insert(0, "/tmp/keyline-audit06")
from hx import *
from keyline.pen import Deck, DoesNotFit

FAM = ["Arial", "Times New Roman", "Courier New", "Georgia", "Calibri", "Cambria"]

def longest_title(d, role, first):
    """first + filler words, as long as the pen accepts (2 lines in a bottom-anchored title)"""
    filler = "và những điều chưa từng được kể về thị trường miền Tây năm nay khi mùa nước nổi về sớm hơn mọi năm".split()
    best = first
    for n in range(1, len(filler) + 1):
        t = first + " " + " ".join(filler[:n])
        try:
            d.add(role, t)
        except DoesNotFit:
            break
        best = t
    return best

for mode in ("presented",):
    for fam in FAM:
        v = voice(fam)
        d = Deck("swiss", mode, v)
        scratch = Deck("swiss", mode, v)
        ev = longest_title(scratch, "evidence", "Ẩn số")
        cv = longest_title(scratch, "cover", "Ẩn số")
        cases = [
            ("statement title 'Ẩn số'", lambda d: d.add("statement", "Ẩn số"), "title"),
            ("statement title 'Ǻ'", lambda d: d.add("statement", "Ǻ Ấn Độ"), "title"),
            (f"evidence title 2 lines", lambda d, ev=ev: d.add("evidence", ev), "title"),
            (f"cover title 2 lines", lambda d, cv=cv: d.add("cover", cv), "title"),
            ("section main label", lambda d: d.add("section", "x").text("ẩm thực", style="label"), "main"),
        ]
        stem = f"top2-{mode}-{fam.replace(' ', '')}"
        order = build(d, cases, W / f"{stem}.pptx")
        pdf, imgs = render(W / f"{stem}.pptx")
        print(f"== {mode} {fam}  (evidence title: {ev!r})")
        measure(order, imgs)
