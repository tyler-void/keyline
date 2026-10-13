"""F2: LibreOffice 24.2 does not break a line at a space before U+005C REVERSE SOLIDUS (nor
before U+2044 FRACTION SLASH); the estimator does (break_units splits at every U+0020 except
before B-22 item 4's list). Text with backslash commands (LaTeX, escapes), at the longest
the pen accepts, word by word: LibreOffice sets more lines than the pen estimated and the
last line leaves the region. Run from the keyline checkout root with its venv."""
import sys
sys.path.insert(0, "/tmp/keyline-audit07")
from fractions import Fraction
from hx import *
from keyline.fit import fit, Setting
from keyline.fit.text import paragraphs
from keyline.packs import resolve

PACK = resolve("swiss")
CORPUS = ("In the template, \\alpha sets the angle, \\beta the slope and \\gamma the offset; "
          "\\frac divides two terms, \\sqrt takes the root, \\sum adds the series, \\int "
          "integrates it, \\label names the equation, \\ref cites it and \\cite points to "
          "the source, while \\emph marks a word and \\textbf sets it in bold.").split()

def longest(fn):
    best = None
    for n in range(1, 400):
        t = " ".join(CORPUS[i % len(CORPUS)] for i in range(n))
        try:
            fn(t)
        except DoesNotFit:
            return best
        best = t
    return best

def estimate(deck, style, region_box, text):
    s = deck._setting(PACK.styles[deck._mode][style])
    return sum(len(l) for l in fit(s, paragraphs(text), Fraction(region_box.w, 12700), Fraction(region_box.h, 12700)))

if __name__ == "__main__":
    fams = sys.argv[1:] or ["Arial", "Calibri", "Georgia", "Times New Roman", "Courier New", "Cambria"]
    for mode in ("presented", "read"):
        for fam in fams:
            v = voice(fam)
            d = Deck("swiss", mode, v)
            cases = []
            for role, layout, region, style in (("evidence", "keyline:evidence", "main", "body"),
                                                ("statement", "keyline:statement", "main", "lede"),
                                                ("evidence", "keyline:evidence:figure", "side", "body")):
                variant = "figure" if layout.endswith("figure") else None
                mk = lambda dd, t, role=role, region=region, style=style, variant=variant: dd.add(role, "x", variant=variant).text(t, style=style, region=region)
                t = longest(lambda t: mk(Deck("swiss", mode, v), t))
                n = estimate(d, style, PACK.region_box(layout, region), t)
                cases.append((f"{mode} {fam} {layout} {region} {style}: {len(t.split())} words, pen estimates {n} lines", lambda dd, t=t, mk=mk: mk(dd, t), region))
            stem = f"f2-{mode}-{fam.replace(' ', '')}"
            order = build(d, cases, W / f"{stem}.pptx")
            pdf, imgs = render(W / f"{stem}.pptx")
            measure(order, imgs)
            for i, (label, layout, keep) in enumerate(order):
                b = PACK.region_box(layout, keep)
                y0 = b.y / 12700
                n = len([y for y in lines_on(pdf, 2 * i + 1) if y > y0])
                print(f"    LibreOffice lines in the region's text: {n}")
