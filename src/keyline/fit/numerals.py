"""The numeral set (amendment B-26, the ruling on Q-52): the characters a figure's value
may use.

It is B-25's measured set minus every character whose top or left reach is not smaller
than the smallest free space above, or beside, any region that allows a figure, so that
B-25 item 3 holds for the numeral style. A reach is computed in each of the six twins,
regular and bold, at each mode's numeral size: the top reach is size × the glyph's top
less the first baseline (B-25 item 2), and the left reach is size × how far the glyph
reaches left of its origin (B-24).

tools/gen_fit_tables.py measures each character's largest reach over the twins from their
outlines, and writes it to tables/numerals.json with the twins' versions. It also writes the
excluded characters of each bundled pack, which a test re-derives. The pen and `keyline
brief` derive a pack's excluded characters from that reach and the pack's geometry, so a
pack directory gets its own.
"""

from __future__ import annotations

import functools
import json
from fractions import Fraction

from keyline.fit import BELOW_BASELINE_EM, TABLES, WEIGHTS, load_table
from keyline.fit.text import code_point, measured

NUMERALS = TABLES / "numerals.json"
FIGURE = "figure"
NUMERAL_STYLE = "numeral"  # the figure's first style (§6.1)
EMU_PER_PT = 12700


@functools.cache
def _data() -> dict:
    return json.loads(NUMERALS.read_text(encoding="utf-8"))


@functools.cache
def reach() -> dict[str, tuple[Fraction, Fraction]]:
    """Per character of the measured set that some twin draws: (the highest its glyph rises
    above the baseline, the furthest it reaches left of its origin), in em, the largest
    over the twins."""
    return {chr(cp): (Fraction(top), Fraction(left)) for cp, top, left in _data()["reach"]}


def _first_baseline_em(line_spacing: Fraction) -> Fraction:
    """The first baseline below the box's top, in em, the smallest over the twins (B-25
    item 2): all six have line_pitch_em = 1.2."""
    from keyline.config import load as load_config

    pitch = min(
        load_table(family, weight).line_pitch_em
        for family, _twin in load_config().portable_fonts
        for weight in WEIGHTS
    )
    return pitch * line_spacing - BELOW_BASELINE_EM


def limits(pack) -> dict:
    """What B-26 measures against in a pack: the numeral's size, line spacing and caps per
    mode, and the smallest free space above and beside the regions that allow a figure, in
    EMU (None when no region does)."""
    sizes, above, left = {}, [], []
    for mode in pack.modes:
        for role in pack.roles.values():
            if FIGURE not in role.components.get(mode, {}):
                continue
            style = pack.styles[mode][NUMERAL_STYLE]
            sizes[mode] = (style.size_pt, style.line_spacing, style.caps)
            for layout in role.layouts:
                for region in pack.regions[layout]:
                    if region in ("title", "footer"):
                        continue
                    a, b = pack.free_space(layout, region)
                    above.append(a)
                    left.append(b)
    return {
        "numeral": sizes,
        "free_above_emu": min(above, default=None),
        "free_left_emu": min(left, default=None),
    }


def derive(pack, reaches: dict[str, tuple[Fraction, Fraction]]) -> dict[str, str]:
    """The characters B-26 excludes for a pack, each with the edge it reaches past ("top",
    "left" or "top+left"), from a reach per character."""
    lim = limits(pack)
    if lim["free_above_emu"] is None:
        return {}
    above = Fraction(lim["free_above_emu"], EMU_PER_PT)
    left = Fraction(lim["free_left_emu"], EMU_PER_PT)
    out = {}
    for ch in sorted(reaches):
        edges = []
        for size, line_spacing, caps in lim["numeral"].values():
            top_em, left_em = reaches.get(ch.upper(), reaches[ch]) if caps else reaches[ch]
            if size * top_em - size * _first_baseline_em(line_spacing) >= above:
                edges.append("top")
            if size * left_em >= left:
                edges.append("left")
        if edges:
            out[ch] = "+".join(e for e in ("top", "left") if e in edges)
    return out


_excluded: dict = {}


def excluded(pack) -> dict[str, str]:
    """The characters a figure's value may not use in this pack, beyond those outside the
    measured set."""
    if pack.directory not in _excluded:
        _excluded[pack.directory] = derive(pack, reach())
    return _excluded[pack.directory]


def numeral_problem(text: str, pack) -> str | None:
    """Why a figure's value cannot be set as a numeral in this pack (B-26), or None. The
    message names the first character outside the numeral set and suggests the label."""
    out = excluded(pack)
    for ch in text:
        if not measured(ch):
            why = "it is outside the measured set (B-25)"
        elif ch in out:
            edge = {"top": "above", "left": "left of", "top+left": "above and left of"}[out[ch]]
            why = f"it reaches {edge} the figure's region (B-26)"
        else:
            continue
        return f"contains {code_point(ch)}, which a numeral cannot hold: {why}; put it in the label"
    return None
