"""The longest table the pen accepts, per voice font, presented and read; LibreOffice's
row pitch against the estimate."""
import sys

sys.path.insert(0, "/tmp/keyline-audit05")
from h import W, region_pt, report, to_pdf  # noqa: E402

from keyline.pen import Deck, DoesNotFit  # noqa: E402

V = "/tmp/keyline-audit05/voices/"
region = region_pt("keyline:evidence", "main")
for mode in ("presented", "read"):
    for voice in ("neutral", "field", V + "times.toml", V + "calibri.toml", V + "cambria.toml",
                  V + "courier.toml"):
        deck = Deck(pack="swiss", mode=mode, voice=voice)
        b = deck.add("evidence", "A table")
        best = None
        for n in range(1, 40):
            rows = [["Style", "Used for"]] + [[f"Row {i}", "Text"] for i in range(n)]
            try:
                b.table(rows)
            except DoesNotFit:
                break
            b._used.discard("main")
            b._plan.shapes.pop()
            best = rows
        b.table(best)
        name = voice.rsplit("/", 1)[-1].replace(".toml", "")
        out = W / f"table2-{mode}-{name}.pptx"
        deck.save(str(out))
        ws, bad = report(to_pdf(out), {1: region}, quiet=True)
        tops = sorted({round(w[2], 2) for w in ws if w[0] == 1 and w[2] > 170})
        pitch = tops[2] - tops[1] if len(tops) > 2 else 0
        low = max(w[4] for w in ws if w[0] == 1)
        print(f"{mode:9} {name:8} rows={len(best) - 1:2} LO row pitch {pitch:.2f} pt; "
              f"lowest word bottom {low:.1f} vs region {region[3]:.1f} -> "
              f"{'OVERFLOW %.1f pt' % (low - region[3]) if low > region[3] else 'inside'}")
