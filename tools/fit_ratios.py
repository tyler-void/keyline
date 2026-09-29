"""Print AC-13(a)'s ratios for report A2 (task T-22): per twin and weight, each committed
test string's estimate ÷ Pillow's width, the largest ratio, and any plain-Latin string
above 1.05 (audit 04: an estimator that would refuse text that fits; informational).

    python tools/fit_ratios.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from keyline.fit import WEIGHTS  # noqa: E402
from tests.acceptance.m2.test_ac13a_fit_widths import FAMILIES, ratios  # noqa: E402

if __name__ == "__main__":
    flagged = []
    for family, twin in FAMILIES:
        for weight in WEIGHTS:
            rows, skipped = ratios(family, twin, weight)
            if rows is None:
                print(f"{twin:<18} {weight:<7} not installed: skipped")
                continue
            worst = max(rows, key=lambda r: r[1])
            cells = "  ".join(f"{n} {r:.4f}" for n, r, _ in rows)
            print(f"{twin:<18} {weight:<7} largest {worst[1]:.4f} ({worst[0]})  {cells}")
            if skipped:
                print(f"{'':<27}skipped, missing glyphs: {', '.join(skipped)}")
            flagged += [(twin, weight, n, r) for n, r, latin in rows if latin and r > 1.05]
    print("plain-Latin strings above 1.05:", flagged or "none")
