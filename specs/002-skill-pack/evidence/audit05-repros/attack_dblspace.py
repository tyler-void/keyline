"""Two spaces after each full stop: the estimator collapses them, LibreOffice sets both."""
import random
import sys

sys.path.insert(0, "/tmp/keyline-audit05")
from h import W, region_pt, report, to_pdf  # noqa: E402

from keyline.pen import Deck, DoesNotFit  # noqa: E402

SENT = ["The grid has twelve columns.", "Rows set the rhythm.", "Margins keep a clear edge.",
        "Gutters part the columns.", "Every region spans whole columns.", "Type steps up."]
region = region_pt("keyline:evidence", "main")
hits = 0
for mode in ("read", "presented"):
    for seed in range(12):
        rng = random.Random(seed)
        sents = [rng.choice(SENT) for _ in range(80)]
        deck = Deck(pack="swiss", mode=mode, voice="neutral")
        b = deck.add("evidence", "Double spaces")
        best = None
        for n in range(1, 80):
            t = "  ".join(sents[:n])
            try:
                b.text(t)
            except DoesNotFit:
                break
            b._used.discard("main")
            b._plan.shapes.pop()
            best = t
        b.text(best)
        out = W / f"dbl-{mode}-{seed}.pptx"
        deck.save(str(out))
        ws, bad = report(to_pdf(out), {1: region}, quiet=True)
        low = max(w[4] for w in ws if w[0] == 1)
        if bad:
            hits += 1
            print(f"{mode} seed {seed}: {best.count('  ') + 1} sentences accepted; lowest word bottom "
                  f"{low:.1f} vs region {region[3]:.1f}: OVERFLOW ({out.name})")
    print(mode, "done")
print("overflows:", hits)
