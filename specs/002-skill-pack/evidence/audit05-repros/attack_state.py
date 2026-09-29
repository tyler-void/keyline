"""Refusal paths and builder state."""
import zipfile

from keyline.pen import Deck, DoesNotFit, PenError

OUT = "/tmp/keyline-audit05"


def texts(path):
    z = zipfile.ZipFile(path)
    names = sorted(n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml"))
    import re
    return {n: re.findall(r"<a:t>([^<]*)</a:t>", z.read(n).decode()) for n in names}


# (b) a refused source() erases an accepted note() and blocks a retry
deck = Deck(pack="swiss", mode="presented", voice="neutral")
s = deck.add("evidence", "Regions snap to one grid")
s.text("Body text here.")
s.note("the note that was accepted")
try:
    s.source("a very long source line " * 12)
except DoesNotFit as exc:
    print("(b) source refused:", exc)
try:
    s.source("pack.toml")
except PenError as exc:
    print("(b) retry with a short source refused:", exc)
deck.save(f"{OUT}/state-b.pptx")
print("(b) saved slide texts:", texts(f"{OUT}/state-b.pptx"))

# (c) body text in the footer region, then source() silently replaces it
deck = Deck(pack="swiss", mode="presented", voice="neutral")
s = deck.add("evidence", "Regions snap to one grid")
s.text("Revenue grew 40 percent", region="footer")
print("(c) text(region='footer') accepted in the body style")
s.source("pack.toml")
deck.save(f"{OUT}/state-c.pptx")
print("(c) saved slide texts:", texts(f"{OUT}/state-c.pptx"))

# (d) bullets in two regions: 2 x bullets_max on one slide
deck = Deck(pack="swiss", mode="presented", voice="neutral")
s = deck.add("evidence", "Regions snap to one grid", variant="figure")
s.bullets(["one", "two", "three", "four"], region="main")
s.bullets(["five", "six", "seven", "eight"], region="side")
print("(d) 8 bullets on one presented slide (bullets_max 4): accepted")

# (e) a truthy non-bool where a flag is expected: a raw colour is not refused
deck = Deck(pack="swiss", mode="read", voice="neutral", evidence="./fixtures/packs/swiss-specimen.evidence.toml")
s = deck.add("evidence", "Regions snap to one grid", variant="figure")
s.figure("grid_columns", accent="#00FF00")
print("(e) figure(accent='#00FF00') accepted; accents spent:", s._accents)
s2 = deck.add("evidence", "A table")
s2.table([["A", "B"], ["1", "2"]], header="2cm")
print("(e) table(header='2cm') accepted")
