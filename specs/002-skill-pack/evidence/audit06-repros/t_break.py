"""Break units: tokens after which LibreOffice may NOT break (UAX #14 LB14/LB15a) or before
which it may not break (LB13, characters outside B-22 item 4's list), placed where the
estimator breaks. Presented evidence headline (2 lines max, bottom-anchored), Arial."""
import sys; sys.path.insert(0, "/tmp/keyline-audit06")
from fractions import Fraction
from hx import *
from keyline.pen import Deck, DoesNotFit
from keyline.fit import wrap, width, WRAP_MARGIN
from keyline.pen._regions import box

CORPUS = ("harbour library opens early market days fishers return borrowed nets before "
          "tide turns stalls fill crates lemons bread salted volunteers keep ledger every "
          "loan pencil spring copy worn pages fresh book children sort returned hooks size "
          "nobody remembers suggested lending tools novels shelf chisels planes clamps").split()

def make(d, role, after_tok=None, before_tok=None):
    """headline whose estimated line 1 ends in after_tok (or line 2 starts with before_tok),
    with line 2 filled so that LibreOffice needs a third line if it cannot break there."""
    b = d.add(role, "x")
    st = d._pack.styles[d._mode][b._role.title]
    s = d._setting(st)
    tb = box(d._pack, b._layout, "title")
    avail = Fraction(tb.w, 12700)
    room = avail * WRAP_MARGIN
    best = None
    for start in range(len(CORPUS)):
        words = CORPUS[start:] + CORPUS[:start]
        # A: longest prefix with A + " " + tok fitting
        A = []
        for w in words:
            cand = " ".join(A + [w])
            if after_tok:
                if width(s, cand + " " + after_tok) > room: break
            else:
                if width(s, cand) > room: break
            A.append(w)
        rest = words[len(A):] + words[:len(A)]
        # B: fill line 2 as close to room as possible
        B = []
        for w in rest:
            lead = [before_tok] if before_tok and not B else []
            cand = " ".join(lead + B + [w]) if not before_tok else " ".join([before_tok] + B + [w])
            if width(s, cand) > room: break
            B.append(w)
        if after_tok:
            line1, line2 = " ".join(A + [after_tok]), " ".join(B)
            hard = width(s, after_tok + " " + line2)  # LO's line 2 if no break after tok
        else:
            line1, line2 = " ".join(A), " ".join([before_tok] + B)
            hard = width(s, line1.rsplit(" ", 1)[1] + " " + line2)  # LO's line 2 if no break before tok
        text = line1 + " " + line2
        try:
            lines = wrap(s, text, avail)
        except DoesNotFit:
            continue
        if len(lines) != 2:
            continue
        slack = float(width(s, line2) / avail)
        over = float(hard / avail)
        if best is None or over > best[2]:
            best = (text, lines, over, slack)
    return best


def main():
    TOKS_AFTER = ["«", "“", "‘", "(", "[", "¿", "¡", "„", "‹"]
    TOKS_BEFORE = ["！", "？", "，", "。", "」", "）", "،", "؟", "⁄", "‼", "›", "…", "—", "‐"]
    cases, meta = [], []
    scratch = Deck("swiss", "presented", "neutral")
    for tok in TOKS_AFTER:
        r = make(scratch, "evidence", after_tok=tok)
        if r: cases.append((f"after {tok!r}", r[0])); meta.append(r)
    for tok in TOKS_BEFORE:
        r = make(scratch, "evidence", before_tok=tok)
        if r: cases.append((f"before {tok!r}", r[0])); meta.append(r)
    d = Deck("swiss", "presented", "neutral")
    spec = []
    for (label, text), m in zip(cases, meta):
        d2 = Deck("swiss", "presented", "neutral"); d2.add("evidence", text)  # accepted?
        spec.append((f"{label} est=2 lines, LO-line2-if-unbreakable={m[2]:.3f}x", lambda d, t=text: d.add("evidence", t), "title"))
    order = build(d, spec, W / "break.pptx")
    pdf, imgs = render(W / "break.pptx")
    res = measure(order, imgs)
    for i, ((label, text), m) in enumerate(zip(cases, meta)):
        ys = lines_on(pdf, 2 * i + 1)
        print(f"  {label}: LO lines={len(ys)}  text={text!r}")

if __name__ == '__main__':
    main()
