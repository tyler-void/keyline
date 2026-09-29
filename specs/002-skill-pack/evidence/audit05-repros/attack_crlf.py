"""text() with Windows line endings: each paragraph keeps a trailing CR."""
import sys

sys.path.insert(0, "/tmp/keyline-audit05")
from h import W, region_pt, report, to_pdf  # noqa: E402

from keyline.pen import Deck, DoesNotFit  # noqa: E402

deck = Deck(pack="swiss", mode="presented", voice="neutral")
b = deck.add("evidence", "Windows line endings")
best = None
for n in range(1, 20):
    t = "\r\n".join(["Margins keep a clear edge"] * n)
    try:
        b.text(t)
    except DoesNotFit:
        break
    b._used.discard("main")
    b._plan.shapes.pop()
    best = t
b.text(best)
out = W / "crlf.pptx"
deck.save(str(out))
region = region_pt("keyline:evidence", "main")
ws, bad = report(to_pdf(out), {1: region}, quiet=True)
print("paragraphs accepted:", best.count("\n") + 1, "| lowest word bottom",
      round(max(w[4] for w in ws if w[0] == 1), 1), "| region bottom", round(region[3], 1),
      "| words past region:", bad)
