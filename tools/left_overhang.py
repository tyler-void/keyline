"""How far a line's first glyph can reach left of its text box (report A2, AC-13(b)):

    python tools/left_overhang.py

For each Swiss voice font's metric twin, regular and bold (as fontconfig resolves it),
the letters and digits with the most negative left side bearing (fontTools `hmtx`), and
for every Swiss style that sets that font and weight, the overhang of the worst one in
px at 1280 px across a 960 pt slide. A line that starts with such a glyph puts ink that
far left of the region box; LibreOffice's anti-aliasing adds up to about one pixel. Dev
only (fontTools).
"""

from __future__ import annotations

import string
import subprocess

from fontTools.ttLib import TTFont

from keyline.packs import resolve

PX_PER_PT = 1280 / 960
CHARS = string.ascii_letters + string.digits


def font_file(family: str, weight: str) -> str:
    style = "Bold" if weight == "bold" else "Regular"
    out = subprocess.run(
        ["fc-match", "-f", "%{family}|%{file}", f"{family}:style={style}"],
        capture_output=True,
        text=True,
    )
    return out.stdout


def main() -> None:
    pack = resolve("swiss")
    uses: dict[str, set[str]] = {}  # family -> the font roles (display, text) it fills
    for name in pack.voices():
        voice = pack.voice(name)
        for role in ("display", "text"):
            uses.setdefault(voice.font(role), set()).add(role)
    for family in sorted(uses):
        for weight in ("regular", "bold"):
            resolved, path = font_file(family, weight).split("|", 1)
            font = TTFont(path)
            upm, cmap, hmtx = font["head"].unitsPerEm, font.getBestCmap(), font["hmtx"]
            worst = sorted((hmtx[cmap[ord(c)]][1], c) for c in CHARS if ord(c) in cmap)[:5]
            listed = ", ".join(f"{c} {lsb}" for lsb, c in worst)
            print(f"{family} {weight} -> {resolved.split(',')[0]} ({upm} upm): {listed}")
            lsb, c = worst[0]
            if lsb >= 0:
                continue
            for mode in ("presented", "read"):
                for name, style in sorted(pack.styles[mode].items()):
                    if style.weight != weight or style.font not in uses[family]:
                        continue
                    px = -lsb / upm * float(style.size_pt) * PX_PER_PT
                    flag = "  > 2 px" if px > 2 else ""
                    print(
                        f"  {mode:<9} {name:<12} {float(style.size_pt):>5.1f} pt  "
                        f"'{c}' reaches {px:.2f} px left{flag}"
                    )


if __name__ == "__main__":
    main()
