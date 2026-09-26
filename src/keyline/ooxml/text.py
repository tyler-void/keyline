"""Run property resolution (A-4, A-11).

Size, bold, italic, caps and spacing (A-4), for a paragraph at level N:
  1. the run's a:rPr
  2. the shape's p:txBody/a:lstStyle/a:lvlNpPr/a:defRPr
  3. the matched layout placeholder's lstStyle            (placeholders only)
  4. the matched master placeholder's lstStyle            (placeholders only)
  5. the master p:txStyles: titleStyle (title, ctrTitle), bodyStyle (other placeholders),
     otherStyle (non-placeholder shapes)
  6. p:presentation/p:defaultTextStyle
Color and latin font (A-11) take the shape's p:style/a:fontRef third, right after the
shape's own lstStyle and before the layout; color then falls back to tx1 through the
clrMap. a:pPr/a:defRPr is not part of either cascade (A-4).
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from fractions import Fraction

from lxml import etree

from keyline.model import Paragraph, Run
from keyline.ooxml.color import ColorContext, find_color, resolve
from keyline.ooxml.ns import clark, q
from keyline.ooxml.numbers import integer
from keyline.ooxml.theme import Theme
from keyline.units import round_half_away

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
    _cache: dict = field(default_factory=dict, repr=False)
    # (id(style element), level) -> (style, a:lvlNpPr, a:defRPr), shared across a slide's
    # shapes. Each entry holds the style element itself, so its id cannot be reused.
    level_cache: dict = field(default_factory=dict, repr=False)

    def _level(self, style: etree._Element | None, level: int):
        if style is None or len(style) == 0:
            return None, None
        key = (id(style), level)
        hit = self.level_cache.get(key)
        if hit is None or hit[0] is not style:
            lvl = style.find(clark(f"a:lvl{level + 1}pPr"))
            hit = (style, lvl, lvl.find(clark("a:defRPr")) if lvl is not None else None)
            self.level_cache[key] = hit
        return hit[1], hit[2]

    def level_rprs(self, level: int) -> list[etree._Element]:
        """a:defRPr elements for steps 2–6, in order, skipping missing ones."""
        return self._level_rprs(level, first=0)

    def inherited_rprs(self, level: int) -> list[etree._Element]:
        """Steps 3–6 only: what comes after the shape's own lstStyle."""
        return self._level_rprs(level, first=1)

    def _level_rprs(self, level: int, first: int) -> list[etree._Element]:
        key = ("rpr", level, first)
        if key not in self._cache:
            self._cache[key] = self._find_level_rprs(level, first)
        return self._cache[key]

    def _styles(self) -> tuple:
        return (
            self.shape_lststyle,
            self.layout_lststyle,
            self.master_lststyle,
            self.master_txstyle,
            self.default_text_style,
        )

    def _find_level_rprs(self, level: int, first: int) -> list[etree._Element]:
        found = (self._level(style, level)[1] for style in self._styles()[first:])
        return [d for d in found if d is not None]

    def level_ppr(self, level: int) -> list[etree._Element]:
        found = (self._level(style, level)[0] for style in self._styles())
        return [lvl for lvl in found if lvl is not None]


def _first_attr(chain: list[etree._Element], attr: str) -> str | None:
    for el in chain:
        v = el.get(attr)
        if v is not None:
            return v
    return None


def _latin(chain: list[etree._Element], src: TextSources) -> tuple[bool, str | None]:
    for el in chain:
        latin = el.find(clark("a:latin"))
        if latin is not None and latin.get("typeface"):
            return True, _theme_font(latin.get("typeface"), src)
    return False, None


def _font(
    own: list[etree._Element], inherited: list[etree._Element], src: TextSources
) -> str | None:
    """A-11: run rPr and shape lstStyle, then p:style/a:fontRef, then inherited styles."""
    found, font = _latin(own, src)
    if found:
        return font
    if src.font_ref is not None:
        idx = src.font_ref.get("idx")
        if idx == "major":
            return src.theme.major_latin
        if idx == "minor":
            return src.theme.minor_latin
    found, font = _latin(inherited, src)
    if found:
        return font
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


def _fill_color(chain: list[etree._Element], src: TextSources) -> tuple[bool, str | None, bool]:
    """(found, rgb, hidden) from the first fill element in the chain."""
    for el in chain:
        for child in el:
            if child.tag not in _FILL_TAGS:
                continue
            name = etree.QName(child).localname
            if name == "noFill":
                return True, None, True
            if name == "solidFill":
                r = resolve(find_color(child), src.color_ctx)
                if r.rgb is None:
                    src.problems.append(r.problem or "color")
                return True, r.rgb, False
            src.problems.append(f"color:{name}")
            return True, None, False
    return False, None, False


def _color(
    own: list[etree._Element], inherited: list[etree._Element], src: TextSources
) -> tuple[str | None, bool]:
    """(rgb, hidden). A-11: run rPr and shape lstStyle, then p:style/a:fontRef, then
    the inherited styles, then tx1."""
    found, rgb, hidden = _fill_color(own, src)
    if found:
        return rgb, hidden
    if src.font_ref is not None:
        c = find_color(src.font_ref)
        if c is not None:
            r = resolve(c, src.color_ctx)
            if r.rgb is None:
                src.problems.append(r.problem or "color")
            return r.rgb, False
    found, rgb, hidden = _fill_color(inherited, src)
    if found:
        return rgb, hidden
    r = resolve(etree.Element(q("a:schemeClr"), val="tx1"), src.color_ctx)
    if r.rgb is None:
        src.problems.append(r.problem or "color")
    return r.rgb, False


_RUN_ATTRS = ("sz", "spc", "b", "i", "cap")


def _run(text: str, rpr: etree._Element | None, level: int, src: TextSources) -> Run:
    chain = ([rpr] if rpr is not None else []) + src.level_rprs(level)
    inherited = src.inherited_rprs(level)
    own = chain[: len(chain) - len(inherited)]  # the run's rPr and the shape's lstStyle
    # one pass over the chain: the first source that sets an attribute wins
    found: dict[str, str] = {}
    for el in chain:
        for attr in _RUN_ATTRS:
            if attr not in found:
                v = el.get(attr)
                if v is not None:
                    found[attr] = v
        if len(found) == len(_RUN_ATTRS):
            break
    size = integer(found.get("sz"), "rPr@sz")
    if size is None and text.strip():
        src.problems.append("size")
    color, hidden = _color(own, inherited, src)
    return Run(
        text=text,
        size=size,
        bold=found.get("b", "0") in _TRUE,
        italic=found.get("i", "0") in _TRUE,
        caps=found.get("cap") or "none",
        spacing=integer(found.get("spc"), "rPr@spc") or 0,
        font=_font(own, inherited, src) if text.strip() else None,
        color=color,
        hidden=hidden,
    )


def _font_scale(tx_body: etree._Element) -> int | None:
    """A-14: bodyPr/normAutofit@fontScale in 1/1000 % (100000 = 100%); None at 100%."""
    fit = tx_body.find(clark("a:bodyPr/a:normAutofit"))
    if fit is None:
        return None
    scale = integer(fit.get("fontScale"), "normAutofit@fontScale", percent=True)
    if scale is None or scale <= 0 or scale >= 100000:
        return None
    return scale


def _scaled(run: Run, scale: int | None) -> Run:
    """Effective size = resolved sz × fontScale, rounded to 1/100 pt."""
    if scale is None or run.size is None:
        return run
    size = round_half_away(Fraction(run.size * scale, 100000))
    return dataclasses.replace(run, size=size, autofit=scale)


_P, _PPR, _T, _RPR, _BR = (q(n) for n in ("a:p", "a:pPr", "a:t", "a:rPr", "a:br"))
_RUN_TAGS = frozenset((q("a:r"), q("a:fld")))


def paragraphs(tx_body: etree._Element | None, src: TextSources) -> list[Paragraph]:
    if tx_body is None:
        return []
    scale = _font_scale(tx_body)
    out = []
    for p in tx_body.iterfind(_P):
        ppr = p.find(_PPR)
        level = 0
        if ppr is not None:
            level = max(0, min(8, integer(ppr.get("lvl"), "pPr@lvl") or 0))
        align = (ppr.get("algn") if ppr is not None else None) or _first_attr(
            src.level_ppr(level), "algn"
        )
        runs = []
        for child in p:
            tag = child.tag
            if tag in _RUN_TAGS:
                t = child.find(_T)
                text = (t.text or "") if t is not None else ""
                runs.append(_scaled(_run(text, child.find(_RPR), level, src), scale))
            elif tag == _BR:
                runs.append(Run(text="\n", size=None))
        out.append(Paragraph(runs=tuple(runs), align=align or "l", level=level))
    return out
