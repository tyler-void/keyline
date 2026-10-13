"""F1: a figure's numeral ending in a glyph whose ink reaches right of its advance
(negative right side bearing), at (near) the longest the pen accepts, in the side region of
keyline:evidence:figure. AC-13(b) as amended by B-24: the right edge is judged at 2 px with
no allowance. Run from the keyline checkout root with its venv."""
import sys
sys.path.insert(0, "/tmp/keyline-audit07")
from fractions import Fraction
from hx import *
from keyline.fit import width, WRAP_MARGIN
from keyline.packs import resolve

PACK = resolve("swiss")
CASES = [  # mode, family, value
    ("presented", "Cambria", "7,1 kf"),
    ("presented", "Georgia", "1.21f"),
    ("presented", "Calibri", ",,...1ế"),
    ("presented", "Arial", "921ƴ"),
    ("read", "Calibri", "608 kinh tế"),
    ("read", "Georgia", "39,77 loď"),
]

def evidence_file(value, path):
    Path(path).write_text(
        f'schema = 1\n\n[product]\nname = "F1"\nfictional = false\n\n[[evidence]]\nid = "v"\n'
        f'value = "{value}"\nlabel = "a numeral"\nsource = "f1_right.py"\n', encoding="utf-8")
    return str(path)

for k, (mode, fam, value) in enumerate(CASES):
    v = voice(fam)
    ev = evidence_file(value, W / f"f1-{k}.toml")
    d = Deck("swiss", mode, v, evidence=ev)
    s = d._setting(PACK.styles[mode]["numeral"])
    b = PACK.region_box("keyline:evidence:figure", "side")
    room = Fraction(b.w, 12700) * WRAP_MARGIN
    est = width(s, value)
    fn = lambda d: d.add("evidence", "x", variant="figure").figure("v", region="side")
    order = build(d, [(f"{mode} {fam} figure {value!r} (estimate {float(est):.2f} pt of {float(room):.2f} pt room)", fn, "side")], W / f"f1-{k}.pptx")
    pdf, imgs = render(W / f"f1-{k}.pptx")
    measure(order, imgs)
