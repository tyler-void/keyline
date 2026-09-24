"""Theme part: color scheme, latin fonts, fill and background style lists."""

from __future__ import annotations

from dataclasses import dataclass, field

from lxml import etree

from keyline.ooxml.ns import NS, q

SCHEME_NAMES = (
    "dk1",
    "lt1",
    "dk2",
    "lt2",
    "accent1",
    "accent2",
    "accent3",
    "accent4",
    "accent5",
    "accent6",
    "hlink",
    "folHlink",
)


@dataclass
class Theme:
    colors: dict[str, str] = field(default_factory=dict)  # name -> "RRGGBB"
    major_latin: str | None = None
    minor_latin: str | None = None
    fill_styles: list[etree._Element] = field(default_factory=list)
    bg_fill_styles: list[etree._Element] = field(default_factory=list)


def _base_hex(el: etree._Element) -> str | None:
    """A scheme slot holds srgbClr or sysClr (use lastClr, the cached system value)."""
    for child in el:
        if child.tag == q("a:srgbClr"):
            return (child.get("val") or "").upper() or None
        if child.tag == q("a:sysClr"):
            return (child.get("lastClr") or "").upper() or None
    return None


def parse_theme(root: etree._Element | None) -> Theme:
    theme = Theme()
    if root is None:
        return theme
    scheme = root.find("a:themeElements/a:clrScheme", NS)
    if scheme is not None:
        for name in SCHEME_NAMES:
            el = scheme.find(f"a:{name}", NS)
            if el is not None:
                value = _base_hex(el)
                if value is not None:
                    theme.colors[name] = value
    fonts = root.find("a:themeElements/a:fontScheme", NS)
    if fonts is not None:
        major = fonts.find("a:majorFont/a:latin", NS)
        minor = fonts.find("a:minorFont/a:latin", NS)
        theme.major_latin = (major.get("typeface") or None) if major is not None else None
        theme.minor_latin = (minor.get("typeface") or None) if minor is not None else None
    fmt = root.find("a:themeElements/a:fmtScheme", NS)
    if fmt is not None:
        fills = fmt.find("a:fillStyleLst", NS)
        bgs = fmt.find("a:bgFillStyleLst", NS)
        theme.fill_styles = list(fills) if fills is not None else []
        theme.bg_fill_styles = list(bgs) if bgs is not None else []
    return theme
