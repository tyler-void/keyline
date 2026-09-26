from lxml import etree

from keyline.ooxml.color import (
    DEFAULT_CLR_MAP,
    ColorContext,
    apply_override,
    parse_clr_map,
    resolve,
)
from keyline.ooxml.theme import parse_theme

A = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
P = 'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'

THEME = etree.fromstring(
    f"""<a:theme {A}><a:themeElements>
  <a:clrScheme name="t">
    <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
    <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
    <a:dk2><a:srgbClr val="44546A"/></a:dk2><a:lt2><a:srgbClr val="E7E6E6"/></a:lt2>
    <a:accent1><a:srgbClr val="4472C4"/></a:accent1><a:accent2><a:srgbClr val="ED7D31"/></a:accent2>
    <a:accent3><a:srgbClr val="A5A5A5"/></a:accent3><a:accent4><a:srgbClr val="FFC000"/></a:accent4>
    <a:accent5><a:srgbClr val="5B9BD5"/></a:accent5><a:accent6><a:srgbClr val="70AD47"/></a:accent6>
    <a:hlink><a:srgbClr val="0563C1"/></a:hlink><a:folHlink><a:srgbClr val="954F72"/></a:folHlink>
  </a:clrScheme>
  <a:fontScheme name="f"><a:majorFont><a:latin typeface="Calibri Light"/></a:majorFont>
    <a:minorFont><a:latin typeface="Calibri"/></a:minorFont></a:fontScheme>
  <a:fmtScheme name="m"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
  </a:fillStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
  </a:bgFillStyleLst></a:fmtScheme>
</a:themeElements></a:theme>"""
)
theme = parse_theme(THEME)
CTX = ColorContext(theme.colors, dict(DEFAULT_CLR_MAP))


def color(xml: str, ctx: ColorContext = CTX):
    return resolve(etree.fromstring(f"<w {A}>{xml}</w>")[0], ctx)


def test_theme_parse():
    assert theme.colors["dk1"] == "000000" and theme.colors["lt1"] == "FFFFFF"
    assert theme.colors["accent1"] == "4472C4"
    assert (theme.major_latin, theme.minor_latin) == ("Calibri Light", "Calibri")
    assert len(theme.fill_styles) == 1 and len(theme.bg_fill_styles) == 1


def test_srgb_and_sys():
    assert color('<a:srgbClr val="e8422e"/>').rgb == "E8422E"
    assert color('<a:sysClr val="window" lastClr="FFFFFF"/>').rgb == "FFFFFF"


def test_scheme_through_clrmap():
    assert color('<a:schemeClr val="tx1"/>').rgb == "000000"
    assert color('<a:schemeClr val="bg1"/>').rgb == "FFFFFF"
    assert color('<a:schemeClr val="accent2"/>').rgb == "ED7D31"
    assert color('<a:schemeClr val="dk2"/>').rgb == "44546A"


def test_clrmap_override():
    master = parse_clr_map(
        etree.fromstring(
            f'<p:clrMap {P} bg1="dk1" tx1="lt1" bg2="dk2" tx2="lt2" accent1="accent1" '
            'accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" '
            'accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
        )
    )
    dark = ColorContext(theme.colors, master)
    assert color('<a:schemeClr val="bg1"/>', dark).rgb == "000000"
    keep = etree.fromstring(f"<p:clrMapOvr {P} {A}><a:masterClrMapping/></p:clrMapOvr>")
    assert apply_override(master, keep) is master
    ovr = etree.fromstring(
        f'<p:clrMapOvr {P} {A}><a:overrideClrMapping bg1="lt1" tx1="dk1" bg2="lt2" '
        'tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" '
        'accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/></p:clrMapOvr>'
    )
    light = ColorContext(theme.colors, apply_override(master, ovr))
    assert color('<a:schemeClr val="bg1"/>', light).rgb == "FFFFFF"


def test_phclr():
    assert color('<a:schemeClr val="phClr"/>', CTX.with_ph("123456")).rgb == "123456"
    assert color('<a:schemeClr val="phClr"/>').problem == "color:phClr-unbound"


def test_lummod_lumoff():
    # accent1 at 75% lightness mod (the Office "darker 25%" swatch)
    r = color('<a:schemeClr val="accent1"><a:lumMod val="75000"/></a:schemeClr>')
    assert r.rgb == "2F5597"
    # bg1 darker 15%
    r = color('<a:schemeClr val="bg1"><a:lumMod val="85000"/></a:schemeClr>')
    assert r.rgb == "D9D9D9"
    # tx1 lighter 50%: lumMod 50% + lumOff 50% on black
    r = color('<a:schemeClr val="tx1"><a:lumMod val="50000"/><a:lumOff val="50000"/></a:schemeClr>')
    assert r.rgb == "808080"


def test_tint_and_shade():
    assert color('<a:srgbClr val="000000"><a:tint val="50000"/></a:srgbClr>').rgb == "808080"
    assert color('<a:srgbClr val="FFFFFF"><a:shade val="50000"/></a:srgbClr>').rgb == "808080"
    assert color('<a:srgbClr val="FF0000"><a:tint val="100000"/></a:srgbClr>').rgb == "FF0000"


def test_alpha_policy():
    assert color('<a:srgbClr val="FF0000"><a:alpha val="100000"/></a:srgbClr>').rgb == "FF0000"
    r = color('<a:srgbClr val="FF0000"><a:alpha val="50000"/></a:srgbClr>')
    assert (r.rgb, r.problem) == (None, "transform:alpha")


def test_unsupported():
    assert color('<a:srgbClr val="FF0000"><a:satMod val="50000"/></a:srgbClr>').problem == (
        "transform:satMod"
    )
    assert color('<a:prstClr val="black"/>').problem == "color:prstClr"
    assert color('<a:hslClr hue="0" sat="0" lum="0"/>').problem == "color:hslClr"
    assert color('<a:scrgbClr r="0" g="0" b="0"/>').problem == "color:scrgbClr"
    assert color('<a:srgbClr val="XYZ"/>').rgb is None
