from keyline.ooxml.color import DEFAULT_CLR_MAP, ColorContext
from keyline.ooxml.fill import background, shape_fill
from keyline.ooxml.theme import Theme

from ._xml import el

THEME = Theme(
    colors={"dk1": "000000", "lt1": "FFFFFF", "accent1": "4472C4"},
    fill_styles=[
        el('<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'),
        el("<a:gradFill><a:gsLst/></a:gradFill>"),
    ],
    bg_fill_styles=[el('<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>')],
)
CTX = ColorContext(THEME.colors, dict(DEFAULT_CLR_MAP))


def fill(*chain, style=None, group="none"):
    return shape_fill(
        [el(x) if x else None for x in chain], el(style) if style else None, THEME, CTX, group
    ).fill


def test_own_fill_kinds():
    assert fill('<p:spPr><a:solidFill><a:srgbClr val="1e2761"/></a:solidFill></p:spPr>') == (
        "solid:#1E2761"
    )
    assert fill("<p:spPr><a:gradFill/></p:spPr>") == "gradient"
    assert fill("<p:spPr><a:noFill/></p:spPr>") == "none"
    assert fill("<p:spPr><a:blipFill/></p:spPr>") == "unknown"
    assert fill("<p:spPr/>") == "none"


def test_grpfill_takes_group_fill():
    assert fill("<p:spPr><a:grpFill/></p:spPr>", group="solid:#123456") == "solid:#123456"


def test_placeholder_inheritance_order():
    own = "<p:spPr/>"
    layout = '<p:spPr><a:solidFill><a:srgbClr val="AAAAAA"/></a:solidFill></p:spPr>'
    master = '<p:spPr><a:solidFill><a:srgbClr val="BBBBBB"/></a:solidFill></p:spPr>'
    assert fill(own, layout, master) == "solid:#AAAAAA"
    assert fill(own, None, master) == "solid:#BBBBBB"


def test_fillref():
    ref = '<p:style><a:fillRef idx="{}"><a:schemeClr val="accent1"/></a:fillRef></p:style>'
    assert fill("<p:spPr/>", style=ref.format(1)) == "solid:#4472C4"
    assert fill("<p:spPr/>", style=ref.format(2)) == "gradient"
    assert fill("<p:spPr/>", style=ref.format(0)) == "none"
    # an explicit spPr fill beats the style
    own = "<p:spPr><a:noFill/></p:spPr>"
    assert fill(own, style=ref.format(1)) == "none"


def roots(*bgs):
    return [el(f"<p:sld><p:cSld>{b}</p:cSld></p:sld>") if b is not None else None for b in bgs]


def test_background_order_slide_layout_master():
    solid = '<p:bg><p:bgPr><a:solidFill><a:srgbClr val="{}"/></a:solidFill></p:bgPr></p:bg>'
    b = background(roots("", solid.format("F2F2F0"), solid.format("000000")), THEME, CTX)
    assert (b.fill, b.problem) == ("solid:#F2F2F0", None)
    b = background(roots(solid.format("111111"), solid.format("F2F2F0"), ""), THEME, CTX)
    assert b.fill == "solid:#111111"


def test_background_bgref_is_solid():
    ref = '<p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg>'
    b = background(roots("", "", ref), THEME, CTX)
    assert (b.fill, b.problem) == ("solid:#FFFFFF", None)


def test_background_default_is_white_with_advisory():
    b = background(roots("", "", ""), THEME, CTX)
    assert (b.fill, b.problem) == ("solid:#FFFFFF", "background-default")
    nofill = "<p:bg><p:bgPr><a:noFill/></p:bgPr></p:bg>"
    b = background(roots(nofill, "", ""), THEME, CTX)
    assert (b.fill, b.problem) == ("solid:#FFFFFF", "background-default")


def test_background_gradient_or_image_is_unknown():
    grad = "<p:bg><p:bgPr><a:gradFill/></p:bgPr></p:bg>"
    assert background(roots(grad, "", ""), THEME, CTX).fill == "unknown"
    img = "<p:bg><p:bgPr><a:blipFill/></p:bgPr></p:bg>"
    assert background(roots(img, "", ""), THEME, CTX).fill == "unknown"
