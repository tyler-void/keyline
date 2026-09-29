"""NBSP: Python's str.split() breaks at U+00A0, LibreOffice does not."""
import sys

sys.path.insert(0, "/tmp/keyline-audit05")
from h import W, region_pt, report, to_pdf  # noqa: E402

from keyline.pen import Deck  # noqa: E402

deck = Deck(pack="swiss", mode="presented", voice="neutral")
t = " ".join("Regions snap to one grid on every slide in the deck so text".split())
deck.add("evidence", t)
print("accepted NBSP headline:", t.replace(" ", "~"))
out = W / "nbsp.pptx"
deck.save(str(out))
ws, bad = report(to_pdf(out), {1: region_pt("keyline:evidence", "title")}, quiet=False)
print([(round(w[1]), round(w[3]), round(w[4]), w[5]) for w in ws])
