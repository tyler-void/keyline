"""next() after add() on a brief deck: next() indexes the brief by the deck's slide count."""
from keyline.pen import Deck, PenError

B = "./fixtures/packs/swiss-specimen-read-field.brief.toml"
deck = Deck.from_brief(B)
deck.add("statement", "An extra slide the brief does not have")
s = deck.next()
print("first next() gave role", s._role.name, "- the brief's first slide is 'cover'")
n = 1
try:
    while True:
        deck.next()
        n += 1
except PenError as exc:
    print(f"next() gave {n} slides, then: {exc}")
