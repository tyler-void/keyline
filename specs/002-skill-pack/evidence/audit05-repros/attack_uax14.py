"""The estimator breaks at every space; LibreOffice follows UAX #14 and never breaks before
'/', '!', '?', ')', ',', ';' or ':' even after a space (LB13). Find headlines the pen
accepts whose estimated break falls before such a character with the last line full, and
let LibreOffice set them."""
import random
import sys
from fractions import Fraction

sys.path.insert(0, "/tmp/keyline-audit05")
from h import W, region_pt, report, to_pdf  # noqa: E402

from keyline.fit import WRAP_MARGIN, fit, width  # noqa: E402
from keyline.pen import Deck, DoesNotFit  # noqa: E402

EMU_PER_PT = 12700
mode, voice, role, layout = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
SEP = sys.argv[5] if len(sys.argv) > 5 else "/"
deck = Deck(pack="swiss", mode=mode, voice=voice)
style = deck._pack.styles[mode][deck._pack.roles[role].title]
setting = deck._setting(style)
tb = deck._pack.region_box(layout, "title")
bw, bh = Fraction(tb.w, EMU_PER_PT), Fraction(tb.h, EMU_PER_PT)
room = bw * WRAP_MARGIN

WORDS = ("plan build ship measure learn repeat grid rule column margin gutter rhythm type "
         "scale voice paper ink signal red blue orders district minutes faster").split()
rng = random.Random(7)
found = []
for _ in range(200000):
    n = rng.randint(4, 20)
    text = f" {SEP} ".join(rng.choice(WORDS) for _ in range(n))
    try:
        lines = fit(setting, [text], bw, bh, "headline")[0]
    except DoesNotFit:
        continue
    held = int(bh // setting.pitch)
    if len(lines) != held:
        continue
    # re-wrap as LibreOffice must: a line may not start with "/"
    ok, lo = True, []
    words = text.split(" ")
    cur = []
    for w in words:
        cand = cur + [w]
        if width(setting, " ".join(cand)) <= room or not cur:
            cur = cand
        else:
            # cannot break before "/": move the previous word down too
            if w == SEP:
                prev = cur.pop()
                lo.append(" ".join(cur))
                cur = [prev, w]
            else:
                lo.append(" ".join(cur))
                cur = [w]
    lo.append(" ".join(cur))
    if len(lo) > held:
        found.append(text)
        if len(found) >= 3:
            break

pages = {}
for text in found:
    deck.add(role, text)
    pages[len(deck._slides)] = text
    print("accepted:", text)
out = W / f"uax14-{mode}-{voice}-{ord(SEP)}.pptx"
deck.save(str(out))
region = region_pt(layout, "title")
ws, bad = report(to_pdf(out), {p: region for p in pages}, quiet=True)
for p in pages:
    lines = sorted({round(w[4]) for w in ws if w[0] == p and w[4] < region[3] + 150})
    print(f"slide {p}: word bottoms {lines}, region bottom {region[3]:.1f}")
print("words past the title region:", bad)
