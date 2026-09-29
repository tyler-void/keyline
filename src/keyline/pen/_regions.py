"""Regions (§6.3): the layouts a role offers, the regions of a layout, and their boxes."""

from __future__ import annotations

from keyline.geom import Box
from keyline.packs import Pack
from keyline.pen._errors import PenError


def layout_for(pack: Pack, role: str, variant: str | None) -> str:
    """`keyline:<role>`, or `keyline:<role>:<variant>` when the role offers it."""
    layouts = pack.roles[role].layouts
    if variant is None:
        return layouts[0]
    name = f"keyline:{role}:{variant}"
    if name not in layouts:
        offered = ", ".join(x.rsplit(":", 1)[-1] for x in layouts if x.count(":") == 2) or "none"
        raise PenError(f"role {role} has no variant {variant!r} (variants: {offered})")
    return name


def regions(pack: Pack, layout: str) -> list[str]:
    """The layout's regions other than the title, in pack order."""
    return [r for r in pack.regions[layout] if r != "title"]


def box(pack: Pack, layout: str, region: str) -> Box:
    return pack.region_box(layout, region)


def rule_box(pack: Pack) -> Box:
    """The keyline device: full content width at the pack's rule row (§5.2)."""
    g, rule = pack.grid, pack.keyline_rule
    y = g.margin_y_emu + rule["row"] * g.row_emu
    return Box(g.margin_x_emu, y, 12192000 - 2 * g.margin_x_emu, rule["thickness_emu"])
