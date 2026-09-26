"""Placeholder matching (A-6).

Slide -> layout: match by idx first; if no layout placeholder has that idx, fall back to
the first with the same type. (python-pptx 1.0.2 matches by idx only; the type fallback
is keyline's own.)
Layout -> master: match by type after mapping to the master's types.
"""

from __future__ import annotations

from dataclasses import dataclass

from lxml import etree

from keyline.ooxml.ns import NS, q
from keyline.ooxml.numbers import integer

MASTER_TYPE = {
    "ctrTitle": "title",
    "title": "title",
    "subTitle": "body",
    "obj": "body",
    "body": "body",
    "tbl": "body",
    "chart": "body",
    "dgm": "body",
    "media": "body",
    "clipArt": "body",
    "pic": "body",
    "dt": "dt",
    "ftr": "ftr",
    "sldNum": "sldNum",
    "hdr": "hdr",
}

_PH_PATHS = ("p:nvSpPr/p:nvPr/p:ph", "p:nvPicPr/p:nvPr/p:ph", "p:nvGraphicFramePr/p:nvPr/p:ph")


@dataclass(frozen=True, slots=True)
class Ph:
    type: str
    idx: int

    @property
    def is_title(self) -> bool:
        return self.type in ("title", "ctrTitle")


_NV_TAGS = frozenset(q(f"p:{t}") for t in ("nvSpPr", "nvPicPr", "nvGraphicFramePr", "nvCxnSpPr"))
_NVPR = q("p:nvPr")
_PH = q("p:ph")


def ph_of(shape: etree._Element) -> Ph | None:
    # the non-visual properties element is the shape's first child in valid OOXML
    nv = shape[0] if len(shape) and shape[0].tag in _NV_TAGS else None
    if nv is None:
        for path in _PH_PATHS:  # tolerate unusual ordering
            el = shape.find(path, NS)
            if el is not None:
                break
        else:
            return None
    else:
        nvpr = nv.find(_NVPR)
        el = nvpr.find(_PH) if nvpr is not None else None
        if el is None:
            return None
    idx = integer(el.get("idx"), "ph@idx")
    return Ph(el.get("type", "obj"), idx or 0)


def placeholders(root: etree._Element | None) -> list[tuple[Ph, etree._Element]]:
    """Placeholders on a layout or master, in document order."""
    if root is None:
        return []
    tree = root.find("p:cSld/p:spTree", NS)
    if tree is None:
        return []
    out = []
    for el in tree.iter():
        if not isinstance(el.tag, str):
            continue
        ph = ph_of(el)
        if ph is not None:
            out.append((ph, el))
    return out


def match_layout(ph: Ph, layout_root: etree._Element | None) -> etree._Element | None:
    candidates = placeholders(layout_root)
    for cand, el in candidates:
        if cand.idx == ph.idx:
            return el
    for cand, el in candidates:
        if cand.type == ph.type:
            return el
    return None


def match_master(ph: Ph, master_root: etree._Element | None) -> etree._Element | None:
    wanted = MASTER_TYPE.get(ph.type, ph.type)
    for cand, el in placeholders(master_root):
        if MASTER_TYPE.get(cand.type, cand.type) == wanted:
            return el
    return None
