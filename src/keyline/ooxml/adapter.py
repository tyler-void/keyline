"""Build the normalized Deck model from a .pptx package (spec §2, plan §2).

Parts are reached only through relationships, and shapes only through spTree order and
their ids, never by position in any other tool's numbering (L-001).
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from keyline import progress
from keyline.findings import Finding
from keyline.geom import Box, rotated_aabb
from keyline.model import Deck, Shape, Slide
from keyline.ooxml.color import ColorContext, apply_override, parse_clr_map
from keyline.ooxml.fill import background, shape_fill
from keyline.ooxml.geometry import (
    FULL_TURN,
    Placement,
    Xfrm,
    apply_group,
    parse_xfrm,
    xfrm_element,
)
from keyline.ooxml.ns import (
    NS,
    RT_NOTES_SLIDE,
    RT_SLIDE_LAYOUT,
    RT_SLIDE_MASTER,
    RT_THEME,
    clark,
    q,
)
from keyline.ooxml.numbers import collect, integer
from keyline.ooxml.package import Package, ScanError
from keyline.ooxml.placeholders import MASTER_TYPE, Ph, match_layout, match_master, ph_of
from keyline.ooxml.text import TextSources, paragraphs
from keyline.ooxml.theme import Theme, parse_theme
from keyline.registry import RuleSpec, register

UNRESOLVED = register(
    RuleSpec(
        id="adapter-unresolved",
        category="quality",
        severity="advisory",
        scope="slide",
        basis="structure",
        since="0.1.0",
        summary="The adapter could not resolve a property; rules that need it skip it",
        rationale="L-001",
    )
)
UNSUPPORTED = register(
    RuleSpec(
        id="unsupported-content",
        category="quality",
        severity="advisory",
        scope="slide",
        basis="structure",
        since="0.1.0",
        summary="Content the M1 model does not read (SmartArt, OLE, table text, ...)",
        rationale="L-001",
    )
)

STRICT_P = "http://purl.oclc.org/ooxml/presentationml/main"
CHART_URI = "http://schemas.openxmlformats.org/drawingml/2006/chart"
TABLE_URI = "http://schemas.openxmlformats.org/drawingml/2006/table"
LEAF_TAGS = {q("p:sp"): "sp", q("p:pic"): "pic", q("p:cxnSp"): "cxnSp", q("p:graphicFrame"): "gf"}
NV_TAGS = ("p:nvSpPr", "p:nvPicPr", "p:nvCxnSpPr", "p:nvGraphicFramePr", "p:nvGrpSpPr")

WHAT_TEXT = {
    "geometry": "position and size could not be resolved",
    "size": "text size could not be resolved; the rules skip these runs",
    "font": "latin font could not be resolved",
    "background-default": "no background found; assuming white (A-5)",
}


@dataclass
class MasterInfo:
    root: etree._Element
    theme: Theme
    clr_map: dict[str, str]


@dataclass
class _Ctx:
    """Per-slide state while walking the shape tree."""

    slide: int
    layout: etree._Element | None
    master: MasterInfo
    default_text_style: etree._Element | None
    color: ColorContext
    diags: list[Finding] = field(default_factory=list)
    seen: set[tuple] = field(default_factory=set)
    z: int = 0
    hidden: int = 0
    level_cache: dict = field(default_factory=dict)
    _txstyles: dict = field(default_factory=dict)

    def txstyle(self, ph: Ph | None) -> etree._Element | None:
        key = None if ph is None else ph.is_title
        if key not in self._txstyles:
            self._txstyles[key] = _txstyle(self.master.root, ph)
        return self._txstyles[key]

    def diag(self, spec: RuleSpec, shape: Shape | None, what: str, message: str) -> None:
        key = (spec.id, None if shape is None else shape.id, what)
        if key in self.seen:
            return
        self.seen.add(key)
        self.diags.append(spec.finding(self.slide, shape, message))


def _unresolved_message(what: str) -> str:
    if what in WHAT_TEXT:
        return WHAT_TEXT[what]
    if what.startswith("number:"):
        return f"could not parse {what.split(':', 1)[1]}; the value was dropped (A-17)"
    if what.startswith("transform:"):
        return f"color transform {what.split(':', 1)[1]} is not supported"
    if what.startswith("color:") or what == "color":
        return f"color could not be resolved ({what})"
    if what.startswith("font:"):
        return f"theme font {what.split(':', 1)[1]} is not supported"
    if what.startswith("background"):
        return f"background is not a solid fill ({what}); background rules skip this slide"
    return f"could not resolve {what}"


_NV_QNAMES = frozenset(q(t) for t in NV_TAGS)


def _nv(el: etree._Element) -> etree._Element | None:
    if len(el) and el[0].tag in _NV_QNAMES:  # first child in valid OOXML
        return el[0]
    for tag in NV_TAGS:
        nv = el.find(tag, NS)
        if nv is not None:
            return nv
    return None


def _id_name(el: etree._Element) -> tuple[int, str]:
    nv = _nv(el)
    c = nv.find(clark("p:cNvPr")) if nv is not None else None
    if c is None:
        return 0, ""
    sid = integer(c.get("id"), "cNvPr@id")
    return sid or 0, c.get("name", "")


def _txstyle(master: etree._Element, ph: Ph | None) -> etree._Element | None:
    styles = master.find(clark("p:txStyles"))
    if styles is None:
        return None
    if ph is None:
        return styles.find(clark("p:otherStyle"))
    if ph.is_title:
        return styles.find(clark("p:titleStyle"))
    return styles.find(clark("p:bodyStyle"))


def _lststyle(el: etree._Element | None) -> etree._Element | None:
    return None if el is None else el.find(clark("p:txBody/a:lstStyle"))


def _sppr(el: etree._Element | None) -> etree._Element | None:
    return None if el is None else el.find(clark("p:spPr"))


def _iter_tree(
    parent: etree._Element, groups: tuple[Xfrm, ...], group_fill: str, ctx: _Ctx
) -> Iterator[tuple[etree._Element, tuple[Xfrm, ...], str]]:
    """Leaves of the shape tree in document (z) order, with their enclosing groups
    (innermost first) and the nearest group fill."""
    for child in parent:
        if not isinstance(child.tag, str):
            continue
        if _is_hidden(child):
            ctx.hidden += _count_leaves(child)
            continue
        if child.tag in LEAF_TAGS:
            yield child, groups, group_fill
        elif child.tag == q("p:grpSp"):
            g = parse_xfrm(xfrm_element(child))
            gfill = shape_fill(
                [child.find(clark("p:grpSpPr"))], None, ctx.master.theme, ctx.color, group_fill
            ).fill
            inner = ((g,) if g is not None else ()) + groups
            yield from _iter_tree(child, inner, gfill, ctx)
        elif child.tag == q("mc:AlternateContent"):
            fallback = child.find(clark("mc:Fallback"))
            first = None
            if fallback is not None:
                for sub in _iter_tree(fallback, groups, group_fill, ctx):
                    first = first or sub[0]
                    yield sub
            sid, name = _id_name(first) if first is not None else (0, "")
            stub = Shape(id=sid, name=name, kind="sp", z=ctx.z) if first is not None else None
            ctx.diag(
                UNSUPPORTED,
                stub,
                "alternate-content",
                "mc:AlternateContent: only the mc:Fallback content was read",
            )
        elif child.tag == q("p:contentPart"):
            ctx.diag(UNSUPPORTED, None, "contentPart", "p:contentPart (ink) is not read")


def _is_hidden(el: etree._Element) -> bool:
    """A-12: cNvPr/@hidden="1" removes the shape (or the whole group) from the model."""
    nv = _nv(el)
    c = nv.find(clark("p:cNvPr")) if nv is not None else None
    return c is not None and c.get("hidden") in ("1", "true")


def _count_leaves(el: etree._Element) -> int:
    if el.tag in LEAF_TAGS:
        return 1
    return sum(1 for d in el.iter(*LEAF_TAGS))


def _kind(el: etree._Element) -> str:
    tag = LEAF_TAGS[el.tag]
    if tag != "gf":
        return tag
    data = el.find(clark("a:graphic/a:graphicData"))
    uri = data.get("uri", "") if data is not None else ""
    if uri == CHART_URI:
        return "graphicFrame:chart"
    if uri == TABLE_URI:
        return "graphicFrame:table"
    return "graphicFrame:other"


def _build_shape(el: etree._Element, groups: tuple[Xfrm, ...], group_fill: str, ctx: _Ctx) -> Shape:
    sid, name = _id_name(el)
    kind = _kind(el)
    shape = Shape(id=sid, name=name, kind=kind, z=ctx.z)
    ctx.z += 1

    ph = ph_of(el)
    layout_ph = master_ph = None
    if ph is not None:
        shape.ph_type, shape.ph_idx = ph.type, ph.idx
        layout_ph = match_layout(ph, ctx.layout)
        master_key = ph_of(layout_ph) if layout_ph is not None else ph
        master_ph = match_master(master_key or ph, ctx.master.root)

    # geometry
    xfrm = parse_xfrm(xfrm_element(el))
    if xfrm is None:
        for inherited in (layout_ph, master_ph):
            if inherited is not None:
                xfrm = parse_xfrm(xfrm_element(inherited))
                if xfrm is not None:
                    break
    if xfrm is None:
        ctx.diag(UNRESOLVED, shape, "geometry", _unresolved_message("geometry"))
    else:
        if not groups:  # the common case: integer EMU straight from the xfrm (A-18)
            shape.x, shape.y, shape.w, shape.h = xfrm.x, xfrm.y, xfrm.cx, xfrm.cy
            shape.rot = xfrm.rot % FULL_TURN
            shape.box = (
                Box(xfrm.x, xfrm.y, xfrm.cx, xfrm.cy)
                if shape.rot == 0
                else rotated_aabb(xfrm.x, xfrm.y, xfrm.cx, xfrm.cy, shape.rot)
            )
        else:
            p = Placement.from_xfrm(xfrm)
            for g in groups:
                p = apply_group(p, g)
            shape.x, shape.y, shape.w, shape.h = p.rect()
            shape.rot = p.rot
            shape.box = p.box()

    sppr = el.find(clark("p:spPr"))
    prst = sppr.find(clark("a:prstGeom")) if sppr is not None else None
    if prst is not None:
        shape.geometry = prst.get("prst")
    elif sppr is not None and sppr.find(clark("a:custGeom")) is not None:
        shape.geometry = "custom"

    # fill
    if kind == "pic":
        shape.fill = "unknown"
    elif kind.startswith("graphicFrame"):
        shape.fill = "none"
    else:
        r = shape_fill(
            [sppr, _sppr(layout_ph), _sppr(master_ph)],
            el.find(clark("p:style")),
            ctx.master.theme,
            ctx.color,
            group_fill,
        )
        shape.fill = r.fill
        if r.problem:
            ctx.diag(UNRESOLVED, shape, r.problem, _unresolved_message(r.problem))

    # connectors
    if kind == "cxnSp":
        cnv = el.find(clark("p:nvCxnSpPr/p:cNvCxnSpPr"))
        if cnv is not None:
            st, end = cnv.find(clark("a:stCxn")), cnv.find(clark("a:endCxn"))
            shape.st_cxn = integer(st.get("id"), "stCxn@id") if st is not None else None
            shape.end_cxn = integer(end.get("id"), "endCxn@id") if end is not None else None

    # text
    if kind == "sp":
        style = el.find(clark("p:style"))
        src = TextSources(
            shape_lststyle=_lststyle(el),
            layout_lststyle=_lststyle(layout_ph),
            master_lststyle=_lststyle(master_ph),
            master_txstyle=ctx.txstyle(ph),
            default_text_style=ctx.default_text_style,
            font_ref=style.find(clark("a:fontRef")) if style is not None else None,
            theme=ctx.master.theme,
            color_ctx=ctx.color,
            level_cache=ctx.level_cache,
        )
        shape.paragraphs = paragraphs(el.find(clark("p:txBody")), src)
        for what in dict.fromkeys(src.problems):
            ctx.diag(UNRESOLVED, shape, what, _unresolved_message(what))
    elif kind == "graphicFrame:table":
        ctx.diag(UNSUPPORTED, shape, "table", "table text is not read in M1")
    elif kind == "graphicFrame:other":
        ctx.diag(UNSUPPORTED, shape, "graphicFrame", "SmartArt, OLE or media frame is not read")
    return shape


def _notes_text(pkg: Package, slide_part: str) -> bool:
    for part in pkg.rel_targets(slide_part, RT_NOTES_SLIDE):
        if not pkg.has(part):
            continue
        root = pkg.xml(part)
        for sp in root.iter(q("p:sp")):
            ph = ph_of(sp)
            if ph is None or ph.type != "body":
                continue
            text = "".join(t.text or "" for t in sp.iter(q("a:t")))
            if text.strip():
                return True
    return False


def _one(pkg: Package, part: str, rel_type: str, what: str) -> str:
    targets = pkg.rel_targets(part, rel_type)
    if not targets or not pkg.has(targets[0]):
        raise ScanError(f"{part} has no {what}")
    return targets[0]


def load_deck(path: str | Path) -> tuple[Deck, list[Finding]]:
    with Package(path) as pkg:
        return build_deck(pkg)


def build_deck(pkg: Package) -> tuple[Deck, list[Finding]]:
    progress.reading.set(pkg.main_part)
    pres = pkg.xml(pkg.main_part)
    if etree.QName(pres).namespace == STRICT_P or pres.get("conformance") == "strict":
        raise ScanError("Strict Open XML (ISO/IEC 29500 Strict) is not supported yet")
    size = pres.find(clark("p:sldSz"))
    width = integer(size.get("cx"), "sldSz@cx") if size is not None else None
    height = integer(size.get("cy"), "sldSz@cy") if size is not None else None
    if not width or not height or width <= 0 or height <= 0:
        raise ScanError("presentation.xml has no valid p:sldSz")
    default_text_style = pres.find(clark("p:defaultTextStyle"))

    masters: dict[str, MasterInfo] = {}
    deck = Deck(width=width, height=height)
    diags: list[Finding] = []
    pres_rels = pkg.rels(pkg.main_part)

    slide_ids = pres.findall(clark("p:sldIdLst/p:sldId"))
    for index, sld in enumerate(slide_ids, start=1):
        rid = sld.get(q("r:id"))
        rel = pres_rels.get(rid or "")
        if rel is None or not pkg.has(rel.target):
            raise ScanError(f"slide {index} ({rid}) is missing from the package")
        slide_part = rel.target
        progress.reading.set(slide_part)
        slide_root = pkg.xml(slide_part)
        layout_part = _one(pkg, slide_part, RT_SLIDE_LAYOUT, "slide layout")
        layout_root = pkg.xml(layout_part)
        master_part = _one(pkg, layout_part, RT_SLIDE_MASTER, "slide master")
        if master_part not in masters:
            mroot = pkg.xml(master_part)
            theme_targets = pkg.rel_targets(master_part, RT_THEME)
            theme_root = pkg.xml(theme_targets[0]) if theme_targets else None
            masters[master_part] = MasterInfo(
                mroot, parse_theme(theme_root), parse_clr_map(mroot.find(clark("p:clrMap")))
            )
        master = masters[master_part]
        if index == 1:
            deck.theme_colors = dict(master.theme.colors)
            deck.major_font, deck.minor_font = master.theme.major_latin, master.theme.minor_latin

        clr_map = apply_override(master.clr_map, layout_root.find(clark("p:clrMapOvr")))
        clr_map = apply_override(clr_map, slide_root.find(clark("p:clrMapOvr")))
        color = ColorContext(master.theme.colors, clr_map)
        ctx = _Ctx(index, layout_root, master, default_text_style, color)

        with collect() as dropped:
            bg = background([slide_root, layout_root, master.root], master.theme, color)
        for what in dict.fromkeys(dropped):
            ctx.diag(UNRESOLVED, None, f"number:{what}", _unresolved_message(f"number:{what}"))
        if bg.problem:
            ctx.diag(UNRESOLVED, None, bg.problem, _unresolved_message(bg.problem))
        cSld = layout_root.find(clark("p:cSld"))
        slide = Slide(
            index=index,
            layout_name=cSld.get("name") if cSld is not None else None,
            background=bg.fill,
            has_notes=_notes_text(pkg, slide_part),
        )
        tree = slide_root.find(clark("p:cSld/p:spTree"))
        if tree is not None:
            for el, groups, gfill in list(_iter_tree(tree, (), "none", ctx)):
                with collect() as dropped:
                    shape = _build_shape(el, groups, gfill, ctx)
                for what in dict.fromkeys(dropped):
                    ctx.diag(
                        UNRESOLVED, shape, f"number:{what}", _unresolved_message(f"number:{what}")
                    )
                slide.shapes.append(shape)
        if ctx.hidden:
            n = ctx.hidden
            ctx.diag(
                UNSUPPORTED,
                None,
                "hidden",
                f"{n} hidden shape{'s' if n != 1 else ''} not linted (A-12)",
            )
        deck.slides.append(slide)
        diags.extend(ctx.diags)
    return deck, diags


__all__ = ["MASTER_TYPE", "UNRESOLVED", "UNSUPPORTED", "build_deck", "load_deck"]
