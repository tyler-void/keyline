"""Which spaces does LibreOffice refuse to break at, where the estimator breaks?
'before' probe: line 1 is filled so that ' X' does not fit; the estimator breaks before X.
'after' probe: line 1 is filled so that ' X' fits but ' X next' does not; the estimator
breaks after X. pdftotext tells which line the boundary words landed on."""
import sys, unicodedata
sys.path.insert(0, "/tmp/keyline-audit07")
from fractions import Fraction
from hx import *
from keyline.fit import width, wrap, WRAP_MARGIN
from keyline.fit.text import MEASURED, inked, refused, normalize
from keyline.packs import resolve
PACK = resolve("swiss")
MODE, FAM = "presented", (sys.argv[1] if len(sys.argv) > 1 else "Arial")
v = voice(FAM)
d0 = Deck("swiss", MODE, v)
s = d0._setting(PACK.styles[MODE]["body"])
W_ = Fraction(PACK.region_box("keyline:evidence", "main").w, 12700)
room = W_ * WRAP_MARGIN

def fill_line(target_left_lo, target_left_hi, full=False):
    """tokens whose width leaves leftover in [lo, hi)"""
    toks = []
    k = 0
    while True:
        t = f"q{k:02d}"
        cand = " ".join(toks + [t])
        if width(s, cand) > room:
            break
        toks.append(t); k += 1
    # adjust last token by appending i's / removing tokens until leftover in range
    for drop in range(0, 4):
        base = toks[: len(toks) - drop]
        for m in range(0, 60):
            last = base[-1] + "i" * m
            line = " ".join(base[:-1] + [last])
            L = (W_ if full else room) - width(s, line)
            if room - width(s, line) < 0:
                break
            if target_left_lo <= L < target_left_hi:
                return base[:-1] + [last]
    return None

chars = [c for c in MEASURED if inked(c) and unicodedata.category(c)[0] in "PS" and ord(c) in s.table.advances]
cases = []
for X in chars:
    wx = width(s, " " + X)
    toks = fill_line(width(s, " ") + Fraction(3, 10), wx - Fraction(3, 10), full=True)  # in LO's width the space fits, X does not
    if toks:
        text = " ".join(toks) + f" {X} zz1 zz2"
        lines = wrap(s, normalize(text), W_)
        if lines[0] == " ".join(toks):
            cases.append(("before", X, toks[-1], text))
    wn = width(s, " " + X + " zz1")
    toks = fill_line(wx + Fraction(3, 10), wx + width(s, " ") + width(s, "z") - Fraction(3, 10), full=True)  # after-probe: in LO's width ' X' and the next space fit, 'z' does not
    if toks and width(s, " ".join(toks) + " " + X) > room:
        toks = None
    if toks:
        text = " ".join(toks) + f" {X} zz1 zz2"
        lines = wrap(s, normalize(text), W_)
        if lines[0].endswith(" " + X) and lines[0] == " ".join(toks) + " " + X:
            cases.append(("after", X, toks[-1], text))
print(len(cases), "probes")
d = Deck("swiss", MODE, v)
for kind, X, last, text in cases:
    d.add("evidence", "x").text(text)
d.save(str(W / f"probeB-{FAM}.full.pptx"))
import shutil
shutil.copy(W / f"probeB-{FAM}.full.pptx", W / f"probeB-{FAM}.pptx")
pdf, _ = render(W / f"probeB-{FAM}.pptx")
ws = words(pdf)
bad = []
for i, (kind, X, last, text) in enumerate(cases):
    page = [w for w in ws if w[0] == i + 1]
    ys = sorted({round(w[4]) for w in page if w[2] > 175})  # baselines in main
    def line_of(tok):
        for w in page:
            if w[5] == tok:
                return min(range(len(ys)), key=lambda j: abs(ys[j] - w[4]))
        return None
    if kind == "before":
        li = line_of(last)
        ok = li == 0
    else:
        li = line_of(X)
        ok = li == 0
    if not ok:
        bad.append((kind, X, li))
        print(f"{kind:6} U+{ord(X):04X} {X} ({unicodedata.name(X,'')}): LibreOffice did not break where the estimator did (token on line {li})")
print("done; refused breaks:", len(bad))
