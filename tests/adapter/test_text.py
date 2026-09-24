from keyline.ooxml.color import DEFAULT_CLR_MAP, ColorContext
from keyline.ooxml.text import TextSources, paragraphs
from keyline.ooxml.theme import Theme

from ._xml import el, lst

THEME = Theme(
    colors={"dk1": "000000", "lt1": "FFFFFF", "accent1": "4472C4", "dk2": "44546A"},
    major_latin="Calibri Light",
    minor_latin="Calibri",
)
CTX = ColorContext(THEME.colors, dict(DEFAULT_CLR_MAP))

RPR1 = '<a:rPr sz="3600" b="1"/>'
RPR2 = '<a:rPr sz="1200"/>'
RPR3 = '<a:rPr sz="1200"><a:noFill/></a:rPr>'
RPR4 = '<a:rPr sz="1200"><a:gradFill/></a:rPr>'


def src(**kw):
    base = dict(
        shape_lststyle=None,
        layout_lststyle=None,
        master_lststyle=None,
        master_txstyle=None,
        default_text_style=None,
        font_ref=None,
        theme=THEME,
        color_ctx=CTX,
    )
    base.update(kw)
    return TextSources(**base)


def body(inner: str):
    return el(f"<p:txBody><a:bodyPr/>{inner}</p:txBody>")


def run(text="hello world", rpr=""):
    return f"<a:r>{rpr}<a:t>{text}</a:t></a:r>"


def test_run_rpr_wins():
    s = src(shape_lststyle=lst('<a:lvl1pPr><a:defRPr sz="1000"/></a:lvl1pPr>'))
    (p,) = paragraphs(body(f"<a:p>{run(rpr=RPR1)}</a:p>"), s)
    r = p.runs[0]
    assert (r.size, r.bold) == (3600, True)


def test_cascade_order_levels_2_to_6():
    levels = [
        ("shape_lststyle", "a:lstStyle", 1100),
        ("layout_lststyle", "a:lstStyle", 1200),
        ("master_lststyle", "a:lstStyle", 1300),
        ("master_txstyle", "p:bodyStyle", 1400),
        ("default_text_style", "p:defaultTextStyle", 1500),
    ]
    for i, (key, _tag, size) in enumerate(levels):
        # every later source also defines a size; the earliest present one must win
        kw = {k: lst(f'<a:lvl1pPr><a:defRPr sz="{s}"/></a:lvl1pPr>', t) for k, t, s in levels[i:]}
        (p,) = paragraphs(body(f"<a:p>{run()}</a:p>"), src(**kw))
        assert p.runs[0].size == size, key


def test_ppr_defrpr_is_not_in_the_cascade():
    s = src(default_text_style=lst('<a:lvl1pPr><a:defRPr sz="1800"/></a:lvl1pPr>'))
    xml = f'<a:p><a:pPr><a:defRPr sz="4400"/></a:pPr>{run()}</a:p>'
    (p,) = paragraphs(body(xml), s)
    assert p.runs[0].size == 1800  # A-4 dropped a:pPr/a:defRPr


def test_level_selects_lvlN():
    s = src(
        master_txstyle=lst(
            '<a:lvl1pPr><a:defRPr sz="3200"/></a:lvl1pPr><a:lvl2pPr><a:defRPr sz="2800"/>'
            "</a:lvl2pPr>",
            "p:bodyStyle",
        )
    )
    xml = f'<a:p>{run()}</a:p><a:p><a:pPr lvl="1"/>{run()}</a:p>'
    p1, p2 = paragraphs(body(xml), s)
    assert (p1.runs[0].size, p2.runs[0].size, p2.level) == (3200, 2800, 1)


def test_unresolved_size_is_none_and_reported():
    s = src()
    (p,) = paragraphs(body(f"<a:p>{run()}</a:p>"), s)
    assert p.runs[0].size is None
    assert "size" in s.problems


def test_theme_fonts_and_fontref():
    s = src(
        shape_lststyle=lst(
            '<a:lvl1pPr><a:defRPr><a:latin typeface="+mj-lt"/></a:defRPr></a:lvl1pPr>'
        )
    )
    (p,) = paragraphs(body(f"<a:p>{run(rpr=RPR2)}</a:p>"), s)
    assert p.runs[0].font == "Calibri Light"
    s = src(font_ref=el('<a:fontRef idx="minor"><a:schemeClr val="accent1"/></a:fontRef>'))
    (p,) = paragraphs(body(f"<a:p>{run(rpr=RPR2)}</a:p>"), s)
    assert (p.runs[0].font, p.runs[0].color) == ("Calibri", "4472C4")


def test_color_fallback_tx1_and_explicit():
    s = src()
    rpr = '<a:rPr sz="1200"><a:solidFill><a:srgbClr val="E8422E"/></a:solidFill></a:rPr>'
    xml = f"<a:p>{run(rpr=rpr)}{run(rpr=RPR2)}</a:p>"
    (p,) = paragraphs(body(xml), s)
    assert [r.color for r in p.runs] == ["E8422E", "000000"]


def test_nofill_text_is_hidden_and_gradient_unknown():
    s = src()
    xml = f"<a:p>{run(rpr=RPR3)}{run(rpr=RPR4)}</a:p>"
    (p,) = paragraphs(body(xml), s)
    assert (p.runs[0].hidden, p.runs[0].has_ink) == (True, False)
    assert p.runs[1].color is None and "color:gradFill" in s.problems


def test_alignment_caps_spacing_and_fields():
    s = src(
        shape_lststyle=lst(
            '<a:lvl1pPr algn="ctr"><a:defRPr sz="1000" cap="all" spc="140"/></a:lvl1pPr>'
        )
    )
    xml = '<a:p><a:fld type="slidenum"><a:t>3</a:t></a:fld><a:br/>' + run("x") + "</a:p>"
    (p,) = paragraphs(body(xml), s)
    assert p.align == "ctr"
    assert p.text == "3\nx"
    assert (p.runs[0].caps, p.runs[0].spacing) == ("all", 140)
