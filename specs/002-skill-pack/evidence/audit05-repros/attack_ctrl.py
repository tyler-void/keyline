"""Control characters: accepted by a verb, then what happens at save()."""
import sys

from keyline.pen import Deck, DoesNotFit, PenError

CASES = {
    "FF": "Grid\x0cworks",
    "VT": "Grid\x0bworks",
    "x1c": "Grid\x1cworks",
    "NUL": "Grid\x00works",
    "BEL": "Grid\x07works",
    "surrogate": "Grid\ud800works",
    "U+FFFE": "Grid￾works",
}
for name, s in CASES.items():
    for verb in ("headline", "notes", "text", "table"):
        deck = Deck(pack="swiss", mode="presented", voice="neutral")
        try:
            if verb == "headline":
                deck.add("evidence", s)
            elif verb == "notes":
                deck.add("evidence", "A headline").notes(s)
            elif verb == "text":
                deck.add("evidence", "A headline").text(s)
            else:
                deck.add("evidence", "A headline").table([["A", "B"], [s, "x"]])
        except (PenError, DoesNotFit) as exc:
            print(f"{name:9} {verb:8}: refused at the verb: {type(exc).__name__}: {exc}")
            continue
        try:
            deck.save(f"/tmp/keyline-audit05/ctrl-{name}-{verb}.pptx")
            print(f"{name:9} {verb:8}: accepted, saved")
        except Exception as exc:  # noqa: BLE001
            print(f"{name:9} {verb:8}: accepted, save() raised {type(exc).__module__}.{type(exc).__name__}: {str(exc)[:90]}"
                  f" | isinstance PenError={isinstance(exc, PenError)}")
sys.exit(0)
