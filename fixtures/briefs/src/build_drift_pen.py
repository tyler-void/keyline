"""Build the AC-8 drift decks again, pen-built (spec 002 amendment B-3, task T-29):

    python fixtures/briefs/src/build_drift_pen.py [OUT_DIR]

base.pptx is written by the pen from drift/base.brief.toml (`Deck.from_brief`), with the
same content as the A1 base that build_drift.py writes by hand. Each drift is that base,
opened with python-pptx, with the same pinned change as in A1 (build_drift.DRIFTS), so
that exactly one finding moves. Output goes through zipnorm, so rebuilding gives
identical bytes.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

import build_drift  # noqa: E402
from pptx import Presentation  # noqa: E402

from keyline.pen import Deck  # noqa: E402

BRIEF = HERE / "drift/base.brief.toml"
OUT = HERE / "drift-pen"


def base(path: Path) -> bytes:
    deck = Deck.from_brief(str(BRIEF))
    deck.next().text("A slow dating app for trees and their keepers", style="lede")
    deck.next()
    deck.next().text("12,400 trees are waiting for a keeper").source()
    deck.next().text("71% of keepers are still active after 90 days").source()
    deck.next().text("Join the waitlist as a keeper this season", style="lede").note()
    deck.save(str(path), author="Tyler")
    return path.read_bytes()


def build(out: Path = OUT) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    data = base(out / "base.pptx")
    written = [out / "base.pptx"]
    for name, change in build_drift.DRIFTS.items():
        prs = Presentation(io.BytesIO(data))
        change(prs)
        written.append(build_drift._save(prs, out, name))
    return written


if __name__ == "__main__":
    for p in build(Path(sys.argv[1]) if len(sys.argv) > 1 else OUT):
        print(p)
