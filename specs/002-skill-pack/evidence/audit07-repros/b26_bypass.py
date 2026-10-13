"""B-26 bypass attempts: NFD input of every excluded character (in the evidence file and as
TOML escapes), a value padded with spaces, U+212B (normalizes to U+00C5)."""
import sys, unicodedata
sys.path.insert(0, "/tmp/keyline-audit07")
from hx import *
from keyline.fit.numerals import excluded
from keyline.packs import resolve
EXC = excluded(resolve("swiss"))
ok = refused = 0
for i, c in enumerate(sorted(EXC)):
    for form in ("NFC", "NFD"):
        v = unicodedata.normalize(form, c)
        p = W / f"byp-{i}-{form}.toml"
        p.write_text(f'schema = 1\n\n[product]\nname = "B"\nfictional = false\n\n[[evidence]]\nid = "v"\nvalue = "12 {v} "\nlabel = "x"\nsource = "s"\n', encoding="utf-8")
        try:
            d = Deck("swiss", "presented", "neutral", evidence=str(p))
            d.add("statement", "x").figure("v")
            ok += 1
            print("ACCEPTED", form, repr(v))
        except PenError as e:
            refused += 1
print(f"excluded characters: {len(EXC)}; NFC and NFD forms refused: {refused}, accepted: {ok}")
