"""Scripts the fit tables lack (max advance + fallback font), filled to the longest text
the pen accepts, then set by LibreOffice."""
import sys

sys.path.insert(0, "/tmp/keyline-audit05")
from h import W, region_pt, report, to_pdf  # noqa: E402

from keyline.pen import Deck, DoesNotFit  # noqa: E402

V = "/tmp/keyline-audit05/voices/"


def longest(try_fn, unit, sep=" ", limit=400):
    best = None
    for k in range(1, limit):
        s = sep.join([unit] * k)
        try:
            try_fn(s)
        except DoesNotFit:
            return best
        best = s
    return best


def headline_case(deck, unit, sep=" "):
    s = longest(lambda t: Deck.add(deck, "evidence", t) and deck._slides.pop(), unit, sep)
    deck.add("evidence", s)
    return s


def text_case(deck, unit, sep=" ", style="body"):
    b = deck.add("evidence", "Text")

    def attempt(t):
        b.text(t, style=style)
        b._used.discard("main")
        b._plan.shapes.pop()

    s = longest(attempt, unit, sep)
    b.text(s, style=style)
    return s


CASES = [
    # name, mode, voice, kind, unit
    ("courier-cjk-body", "read", V + "courier.toml", "text", "漢字漢字"),
    ("courier-emoji-body", "read", V + "courier.toml", "text", "😀😀"),
    ("arial-cjk-headline", "presented", "neutral", "headline", "漢字漢字"),
    ("arial-thai-headline", "presented", "neutral", "headline", "สวัสดี"),
    ("arial-emoji-headline", "presented", "neutral", "headline", "😀😀😀"),
    ("georgia-viet-caps", "presented", "field", "headline", "ỆỄỀ ẶẴẰ"),
    ("arial-cjk-body", "read", "neutral", "text", "漢字漢字"),
    ("calibri-cjk-body", "read", V + "calibri.toml", "text", "漢字漢字"),
]

for name, mode, voice, kind, unit in CASES:
    deck = Deck(pack="swiss", mode=mode, voice=voice)
    s = headline_case(deck, unit) if kind == "headline" else text_case(deck, unit)
    n = len(s.split())
    out = W / f"fit2-{name}.pptx"
    deck.save(str(out))
    pdf = to_pdf(out)
    region = region_pt("keyline:evidence", "title" if kind == "headline" else "main")
    ws, bad = report(pdf, {1: region}, quiet=True)
    maxy = max((w[4] for w in ws if w[0] == 1), default=0)
    lines = sorted({round(w[4]) for w in ws if w[0] == 1})
    print(f"{name}: accepted {n} words ({len(s)} chars); words past region: {bad}; "
          f"lowest word bottom {maxy:.1f} vs region bottom {region[3]:.1f}; line bottoms {lines}")
