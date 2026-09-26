"""Shape fill (plan §2.5) and slide background (plan §2.6, A-5)."""

from __future__ import annotations

from dataclasses import dataclass

from lxml import etree

from keyline.ooxml.color import ColorContext, find_color, resolve
from keyline.ooxml.ns import NS, q
from keyline.ooxml.numbers import integer
from keyline.ooxml.theme import Theme

FILL_TAGS = {
    q("a:solidFill"): "solid",
    q("a:gradFill"): "gradient",
    q("a:noFill"): "none",
    q("a:blipFill"): "unknown",
    q("a:pattFill"): "unknown",
    q("a:grpFill"): "group",
}

WHITE = "solid:#FFFFFF"


@dataclass(frozen=True)
class FillResult:
    fill: str  # solid:#RRGGBB | gradient | none | unknown
    problem: str | None = None


def _fill_child(sppr: etree._Element | None) -> etree._Element | None:
    if sppr is None:
        return None
    for child in sppr:
        if child.tag in FILL_TAGS:
            return child
    return None


def _from_fill_element(el: etree._Element, ctx: ColorContext, group_fill: str) -> FillResult:
    kind = FILL_TAGS[el.tag]
    if kind == "solid":
        r = resolve(find_color(el), ctx)
        return FillResult(f"solid:#{r.rgb}") if r.rgb else FillResult("unknown", r.problem)
    if kind == "group":
        return FillResult(group_fill)
    return FillResult(kind)


def _style_entry(entry: etree._Element, ref: etree._Element, ctx: ColorContext) -> FillResult:
    ph = resolve(find_color(ref), ctx).rgb if find_color(ref) is not None else None
    return (
        _from_fill_element(entry, ctx.with_ph(ph), "none")
        if entry.tag in FILL_TAGS
        else (FillResult("unknown"))
    )


def shape_fill(
    sppr_chain: list[etree._Element | None],
    style: etree._Element | None,
    theme: Theme,
    ctx: ColorContext,
    group_fill: str = "none",
) -> FillResult:
    """Own spPr, then inherited placeholder spPr, then p:style/a:fillRef, then none."""
    for sppr in sppr_chain:
        child = _fill_child(sppr)
        if child is not None:
            return _from_fill_element(child, ctx, group_fill)
    ref = style.find("a:fillRef", NS) if style is not None else None
    if ref is not None:
        idx = integer(ref.get("idx", "0"), "fillRef@idx")
        if idx is None:
            return FillResult("unknown", "fill:fillRef")
        if idx == 0:
            return FillResult("none")
        styles = theme.bg_fill_styles if idx >= 1001 else theme.fill_styles
        pos = idx - 1001 if idx >= 1001 else idx - 1
        if 0 <= pos < len(styles):
            return _style_entry(styles[pos], ref, ctx)
        return FillResult("unknown", "fill:fillRef")
    return FillResult("none")


@dataclass(frozen=True)
class Background:
    fill: str  # solid:#RRGGBB | unknown
    problem: str | None = None  # e.g. "background-default" (A-5)


def background(roots: list[etree._Element | None], theme: Theme, ctx: ColorContext) -> Background:
    """First p:cSld/p:bg on the slide, layout, master (in that order)."""
    for root in roots:
        if root is None:
            continue
        bg = root.find("p:cSld/p:bg", NS)
        if bg is None:
            continue
        bgpr = bg.find("p:bgPr", NS)
        if bgpr is not None:
            child = _fill_child(bgpr)
            if child is None or child.tag == q("a:noFill"):
                return Background(WHITE, "background-default")
            r = _from_fill_element(child, ctx, "none")
            if r.fill.startswith("solid:"):
                return Background(r.fill)
            return Background("unknown", r.problem or f"background:{r.fill}")
        ref = bg.find("p:bgRef", NS)
        if ref is not None:
            r = shape_fill([], _wrap_ref(ref), theme, ctx)
            if r.fill.startswith("solid:"):
                return Background(r.fill)
            if r.fill == "none":
                return Background(WHITE, "background-default")
            return Background("unknown", r.problem or f"background:{r.fill}")
        return Background("unknown", "background")
    return Background(WHITE, "background-default")


def _wrap_ref(bg_ref: etree._Element) -> etree._Element:
    """Present a p:bgRef as a p:style/a:fillRef so one lookup serves both."""
    style = etree.Element(q("p:style"))
    ref = etree.SubElement(style, q("a:fillRef"), idx=bg_ref.get("idx", "0"))
    for child in bg_ref:
        ref.append(etree.fromstring(etree.tostring(child)))
    return style
