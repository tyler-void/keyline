"""Table first row with tall Vietnamese capitals (field = Georgia): does the ink leave the
region's top edge? header=False puts body text in row 1; header=True the caps label style."""
import sys; sys.path.insert(0, "/tmp/keyline-audit06")
from hx import *
from keyline.pen import Deck
for mode in ("presented", "read"):
    d = Deck("swiss", mode, "field")
    cases = [
        ("table header=False, row 1 'Ẩn số'", lambda d: d.add("evidence", "x").table([["Ẩn số", "Ổn định"], ["a", "b"]], header=False), "main"),
        ("table header=True, 'ẩm thực' (caps label)", lambda d: d.add("evidence", "x").table([["ẩm thực", "ổn định"], ["a", "b"]]), "main"),
        ("evidence main body 'Ẩn số'", lambda d: d.add("evidence", "x").text("Ẩn số và ổn định"), "main"),
    ]
    order = build(d, cases, W / f"tabletop-{mode}.pptx")
    pdf, imgs = render(W / f"tabletop-{mode}.pptx"); print("==", mode, "field"); measure(order, imgs)
