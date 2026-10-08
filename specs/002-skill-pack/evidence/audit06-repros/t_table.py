"""Table cells (B-22 item 5, Deviation A): cells whose text LibreOffice sets in another
font (CJK -> Asian font slot; emoji -> fallback; Hebrew -> CTL slot). As many rows as the
pen accepts; LibreOffice 24.2."""
import sys; sys.path.insert(0, "/tmp/keyline-audit06")
from hx import *
from keyline.pen import Deck, DoesNotFit

def most_rows(mode, v, cell, cols=2, region="main", variant=None):
    best = None
    for n in range(1, 60):
        rows = [["Item", "Value"][:cols]] + [[cell] * cols for _ in range(n)]
        try:
            Deck("swiss", mode, v).add("evidence", "x", variant=variant).table(rows, region=region)
        except DoesNotFit:
            return best
        best = rows
    return best

CELLS = {"latin": "Harbour", "cjk": "市场", "emoji": "📈", "hebrew": "שלום", "thai": "ตลาด",
         "arabic": "سوق", "devanagari": "बाज़ार", "mixed": "Q3 市场"}
for fam in ("Arial", "Georgia", "Calibri"):
    for mode in ("presented", "read"):
        v = voice(fam)
        d = Deck("swiss", mode, v)
        cases = []
        for name, cell in CELLS.items():
            rows = most_rows(mode, v, cell)
            cases.append((f"{fam} {mode} table {name} x{len(rows)-1} rows", lambda d, rows=rows: d.add("evidence", "x").table(rows), "main"))
        stem = f"table-{mode}-{fam}"
        order = build(d, cases, W / f"{stem}.pptx")
        pdf, imgs = render(W / f"{stem}.pptx")
        measure(order, imgs)
