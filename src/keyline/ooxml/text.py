"""Run property resolution (A-4).

For a paragraph at level N, each property is looked up in:
  1. the run's a:rPr
  2. the shape's p:txBody/a:lstStyle/a:lvlNpPr/a:defRPr
  3. the matched layout placeholder's lstStyle            (placeholders only)
  4. the matched master placeholder's lstStyle            (placeholders only)
  5. the master p:txStyles: titleStyle (title, ctrTitle), bodyStyle (other placeholders),
     otherStyle (non-placeholder shapes)
  6. p:presentation/p:defaultTextStyle
Then, for font and color only, the shape's p:style/a:fontRef; then color falls back to
tx1 through the clrMap. a:pPr/a:defRPr is not part of the cascade (A-4).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from lxml import etree

from keyline.model import Paragraph, Run
from keyline.ooxml.color import ColorContext, find_color, resolve
from keyline.ooxml.ns import NS, q
from keyline.ooxml.theme import Theme

_TRUE = ("1", "true")


@dataclass
class TextSources:
    """Everything the cascade needs for one shape's text body."""

    shape_lststyle: etree._Element | None
    layout_lststyle: etree._Element | None
    master_lststyle: etree._Element | None
    master_txstyle: etree._Element | None  # titleStyle, bodyStyle or otherStyle
    default_text_style: etree._Element | None
    font_ref: etree._Element | None  # p:style/a:fontRef
    theme: Theme
    color_ctx: ColorContext
    problems: list[str] = field(default_factory=list)

    def level_rprs(self, level: int) -> list[etree._Element]:
        """a:defRPr elements for steps 2–6, in order, skipping missing ones."""
        tag = f"a:lvl{level + 1}pPr"
        out = []
        for style in (
            self.shape_lststyle,
            self.layout_lststyle,
            self.master_lststyle,
            self.master_txstyle,
            self.default_text_style,
        ):
            if style is None:
                continue
            lvl = style.find(tag, NS)
            if lvl is None:
                continue
            d = lvl.find("a:defRPr", NS)
            if d is not None:
                out.append(d)
        return out

    def level_ppr(self, level: int) -> list[etree._Element]:
        tag = f"a:lvl{level + 1}pPr"
        out = []
        for style in (
            self.shape_lststyle,
            self.layout_lststyle,
            self.master_lststyle,
            self.master_txstyle,
            self.default_text_style,
        ):
            if style is None:
                continue
            lvl = style.find(tag, NS)
            if lvl is not None:
                out.append(lvl)
        return out


def _first_attr(chain: list[etree._Element], attr: str) -> str | None:
    for el in chain:
        v = el.get(attr)
        if v is not None:
            return v
    return None


def _font(chain: list[etree._Element], src: TextSources) -> str | None:
    for el in chain:
        latin = el.find("a:latin", NS)
        if latin is not None and latin.get("typeface"):
            return _theme_font(latin.get("typeface"), src)
    if src.font_ref is not None:
        idx = src.font_ref.get("idx")
        if idx == "major":
            return src.theme.major_latin
        if idx == "minor":
            return src.theme.minor_latin
    src.problems.append("font")
    return None


def _theme_font(typeface: str, src: TextSources) -> str | None:
    if typeface == "+mj-lt":
        return src.theme.major_latin
    if typeface == "+mn-lt":
        return src.theme.minor_latin
    if typeface.startswith("+"):
        src.problems.append(f"font:{typeface}")
        return None
    return typeface


_FILL_TAGS = (q("a:solidFill"), q("a:gradFill"), q("a:noFill"), q("a:blipFill"), q("a:pattFill"))


def _color(chain: list[etree._Element], src: TextSources) -> tuple[str | None, bool]:
    """(rgb, hidden)."""
    for el in chain:
        for child in el:
            if child.tag not in _FILL_TAGS:
                continue
            name = etree.QName(child).localname
            if name == "noFill":
                return None, True
            if name == "solidFill":
                r = resolve(find_color(child), src.color_ctx)
                if r.rgb is None:
                    src.problems.append(r.problem or "color")
                return r.rgb, False
            src.problems.append(f"color:{name}")
            return None, False
    if src.font_ref is not None:
        c = find_color(src.font_ref)
        if c is not None:
            r = resolve(c, src.color_ctx)
            if r.rgb is None:
                src.problems.append(r.problem or "color")
            return r.rgb, False
    r = resolve(etree.Element(q("a:schemeClr"), val="tx1"), src.color_ctx)
    if r.rgb is None:
        src.problems.append(r.problem or "color")
    return r.rgb, False


def _run(text: str, rpr: etree._Element | None, level: int, src: TextSources) -> Run:
    chain = ([rpr] if rpr is not None else []) + src.level_rprs(level)
    sz = _first_attr(chain, "sz")
    size = None
    if sz is not None:
        try:
            size = int(sz)
        except ValueError:
            size = None
    if size is None and text.strip():
        src.problems.append("size")
    spc = _first_attr(chain, "spc")
    color, hidden = _color(chain, src)
    return Run(
        text=text,
        size=size,
        bold=(_first_attr(chain, "b") or "0") in _TRUE,
        italic=(_first_attr(chain, "i") or "0") in _TRUE,
        caps=_first_attr(chain, "cap") or "none",
        spacing=int(spc) if spc and spc.lstrip("-").isdigit() else 0,
        font=_font(chain, src) if text.strip() else None,
        color=color,
        hidden=hidden,
    )


def paragraphs(tx_body: etree._Element | None, src: TextSources) -> list[Paragraph]:
    if tx_body is None:
        return []
    out = []
    for p in tx_body.iterfind("a:p", NS):
        ppr = p.find("a:pPr", NS)
        level = 0
        if ppr is not None:
            try:
                level = max(0, min(8, int(ppr.get("lvl", "0"))))
            except ValueError:
                level = 0
        align = (ppr.get("algn") if ppr is not None else None) or _first_attr(
            src.level_ppr(level), "algn"
        )
        runs = []
        for child in p:
            if child.tag in (q("a:r"), q("a:fld")):
                t = child.find("a:t", NS)
                text = (t.text or "") if t is not None else ""
                runs.append(_run(text, child.find("a:rPr", NS), level, src))
            elif child.tag == q("a:br"):
                runs.append(Run(text="\n", size=None))
        out.append(Paragraph(runs=tuple(runs), align=align or "l", level=level))
    return out
