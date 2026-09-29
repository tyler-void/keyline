"""§6.2: label text over caption_exempt_words words raises PenError. text(style='label')."""
from keyline.pen import Deck, DoesNotFit, PenError

OUT = "/tmp/keyline-audit05"
for mode in ("presented", "read"):
    deck = Deck(pack="swiss", mode=mode, voice="neutral")
    s = deck.add("section", "How the pack sets a slide")
    words = "one two six ten red map sea".split()
    try:
        s.text(" ".join(words), style="label")
        print(f"{mode}: text(style='label') with {len(words)} words accepted (caption_exempt_words = 5)")
    except (PenError, DoesNotFit) as exc:
        print(f"{mode}: refused: {type(exc).__name__}: {exc}")
    deck.add("statement", "Every value comes from the pack").text("Short", style="lede")
    deck.save(f"{OUT}/label-{mode}.pptx")
    # the same words as a figure label and an attribution are refused
    q = deck.add("quote", "Space is the point.")
    try:
        q.attribution(" ".join(words))
    except PenError as exc:
        print(f"{mode}: attribution with {len(words)} words refused: {exc}")
