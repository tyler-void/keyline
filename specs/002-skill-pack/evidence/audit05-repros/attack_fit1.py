"""Fit attacks on a headline (evidence slide, presented, neutral/Arial): each case is a
headline the pen should refuse if LibreOffice would set it past the title region."""
import sys

sys.path.insert(0, "/tmp/keyline-audit05")
from h import W, region_pt, report, to_pdf  # noqa: E402

from keyline.pen import Deck, DoesNotFit, PenError  # noqa: E402

FILL1 = "Regions snap to one grid on every slide in"  # ~1 line at 48 pt bold
CASES = {
    "control-2lines": "Regions snap to one grid on every slide in the deck so text lines up well",
    "tabs": "x\t" * 40 + "x",
    "leading-spaces": " " * 70 + "Regions snap to one grid on every slide",
    "space-runs": "Regions" + " " * 60 + "snap" + " " * 60 + "to one grid",
    "LF": "Line one\nLine two\nLine three",
    "CR": "Line one\rLine two\rLine three",
    "U+2028": "Line one Line two Line three",
    "U+2029": "Line one Line two Line three",
    "NEL": "Line one\x85Line two\x85Line three",
    "NBSP": " ".join(["grid"] * 45),
    "CJK": "漢字" * 12 + " " + "漢字" * 12,
    "CJK-3x": " ".join(["漢字漢字漢字漢字"] * 6),
    "emoji": " ".join(["😀😀😀"] * 8),
    "thai": "สวัสดี " * 10,
    "zalgo": "Grid" + "́̀̂̃̄̆̇̈" * 6 + " works",
}


def main():
    deck = Deck(pack="swiss", mode="presented", voice="neutral")
    pages = {}
    for name, headline in CASES.items():
        try:
            deck.add("evidence", headline)
        except (DoesNotFit, PenError) as exc:
            print(f"{name}: REFUSED {type(exc).__name__}: {exc}")
            continue
        pages[len(deck._slides)] = name
        print(f"{name}: accepted as slide {len(deck._slides)}")
    out = W / "fit1.pptx"
    try:
        deck.save(str(out))
    except Exception as exc:  # noqa: BLE001
        print("SAVE FAILED:", type(exc).__name__, exc)
        return
    pdf = to_pdf(out)
    title = region_pt("keyline:evidence", "title")
    ws, _ = report(pdf, {p: title for p in pages})
    for p, name in pages.items():
        lines = sorted({round(w[4]) for w in ws if w[0] == p and w[4] < 300})
        maxy = max((w[4] for w in ws if w[0] == p and w[2] < 300), default=0)
        print(f"slide {p} {name}: word baselines-ish yMax={lines} (region bottom {title[3]:.1f})")


main()
