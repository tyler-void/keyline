"""python-pptx helpers for building rule fixtures. Dev-only: never imported by keyline.

Positions and sizes are in cm; colors are "RRGGBB". Every deck is 16:9 (33.867 × 19.05 cm)
and carries the project's identity in its core properties.
"""

from __future__ import annotations

import datetime as dt

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Cm, Pt

BLANK_LAYOUT = 6
FIXED_TIME = dt.datetime(2026, 9, 24, 0, 0, 0)
ALIGN = {"l": PP_ALIGN.LEFT, "ctr": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}


def new_deck():
    prs = Presentation()
    prs.slide_width, prs.slide_height = 12192000, 6858000
    cp = prs.core_properties
    cp.author = cp.last_modified_by = "Tyler"
    cp.title = ""
    cp.revision = 1
    cp.created = cp.modified = FIXED_TIME
    return prs


def slide(prs, bg: str | None = None, notes: str | None = None):
    s = prs.slides.add_slide(prs.slide_layouts[BLANK_LAYOUT])
    if bg is not None:
        s.background.fill.solid()
        s.background.fill.fore_color.rgb = RGBColor.from_string(bg)
    if notes is not None:
        s.notes_slide.notes_text_frame.text = notes
    return s


def role_slide(prs, layout_index: int, layout_name: str, bg=None, notes=None):
    """A slide on layout `layout_index`, renamed to `layout_name` (spec 002 §2 roles live
    in layout names). The layout's placeholders are removed from the slide, so slides on
    different layouts carry exactly the same shapes."""
    layout = prs.slide_layouts[layout_index]
    layout.element.cSld.set("name", layout_name)
    s = prs.slides.add_slide(layout)
    for ph in list(s.placeholders):
        ph.element.getparent().remove(ph.element)
    if bg is not None:
        s.background.fill.solid()
        s.background.fill.fore_color.rgb = RGBColor.from_string(bg)
    if notes is not None:
        s.notes_slide.notes_text_frame.text = notes
    return s


def _style_runs(tf, size, bold, color, font, align):
    for p in tf.paragraphs:
        if align:
            p.alignment = ALIGN[align]
        for r in p.runs:
            r.font.size = Pt(size)
            r.font.bold = bold
            r.font.name = font
            r.font.color.rgb = RGBColor.from_string(color)


def text(
    s,
    x,
    y,
    w,
    h,
    body,
    size=18,
    *,
    name=None,
    bold=False,
    color="111111",
    font="Arial",
    align=None,
    rot=0,
):
    tb = s.shapes.add_textbox(Cm(x), Cm(y), Cm(w), Cm(h))
    tf = tb.text_frame
    tf.word_wrap = True
    lines = body.split("\n")
    tf.text = lines[0]
    for line in lines[1:]:
        tf.add_paragraph().text = line
    _style_runs(tf, size, bold, color, font, align)
    if name:
        tb.name = name
    if rot:
        tb.rotation = rot
    return tb


def rect(
    s,
    x,
    y,
    w,
    h,
    fill="1E2761",
    *,
    name=None,
    body=None,
    size=18,
    color="FFFFFF",
    font="Arial",
    bold=False,
    shape=MSO_SHAPE.RECTANGLE,
):
    sh = s.shapes.add_shape(shape, Cm(x), Cm(y), Cm(w), Cm(h))
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = RGBColor.from_string(fill)
    sh.line.fill.background()
    if body is not None:
        sh.text_frame.text = body
        _style_runs(sh.text_frame, size, bold, color, font, "ctr")
    if name:
        sh.name = name
    return sh


def connector(s, a, b):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, 0, 0, 0, 0)
    c.begin_connect(a, 3)
    c.end_connect(b, 1)
    return c


def picture_placeholder(s, x, y, w, h, name="picture"):
    """A tiny PNG picture (1×1 px, generated in memory)."""
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (1, 1), (200, 200, 200)).save(buf, format="PNG")
    buf.seek(0)
    pic = s.shapes.add_picture(buf, Cm(x), Cm(y), Cm(w), Cm(h))
    pic.name = name
    return pic


# ---------- spec 002: decks from the Swiss templates (what the pen will write) ----------
def swiss_deck(voice: str = "neutral", mode: str = "presented"):
    """A deck opened from the Swiss template of `voice` and `mode`, built in memory
    (amendment B-8.9), with the project's identity in its core properties."""
    import io

    from keyline.packs import resolve
    from keyline.packs.templates import build

    pack = resolve("swiss")
    prs = Presentation(io.BytesIO(build(pack, pack.voice(voice), mode)))
    cp = prs.core_properties
    cp.author = cp.last_modified_by = "Tyler"
    cp.title = ""
    cp.revision = 1
    cp.created = cp.modified = FIXED_TIME
    return prs


def swiss_slide(prs, layout: str, bg: str | None = None, notes: str = "n", **regions):
    """A slide on the named Swiss layout. `regions` maps region name to text: `title`,
    `main`, `side`, `footer`. Placeholders left unfilled are removed, as the pen does."""
    from keyline.packs import resolve

    idx = {"title": 0, **resolve("swiss").placeholder_idx}
    s = prs.slides.add_slide(prs.slide_layouts.get_by_name(layout))
    by_idx = {ph.placeholder_format.idx: ph for ph in s.placeholders}
    for region, body in regions.items():
        by_idx.pop(idx[region]).text_frame.text = body
    for ph in by_idx.values():
        ph.element.getparent().remove(ph.element)
    if bg is not None:
        s.background.fill.solid()
        s.background.fill.fore_color.rgb = RGBColor.from_string(bg)
    if notes is not None:
        s.notes_slide.notes_text_frame.text = notes
    return s


def keyline_rule(s, color: str):
    """The Swiss device: a full-width filled rule at grid row 18 (§5.2)."""
    from keyline.packs import resolve

    pack = resolve("swiss")
    g, rule = pack.grid, pack.keyline_rule
    y = g.margin_y_emu + rule["row"] * g.row_emu
    w = 12192000 - 2 * g.margin_x_emu
    sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, g.margin_x_emu, y, w, rule["thickness_emu"])
    sh.fill.solid()
    sh.fill.fore_color.rgb = RGBColor.from_string(color)
    sh.line.fill.background()
    sh.name = "keyline"
    return sh


def autofit(shape, font_scale: int):
    """normAutofit with fontScale in 1/1000 % (90000 = 90 %)."""
    from pptx.oxml.ns import qn

    body = shape.text_frame._txBody.find(qn("a:bodyPr"))
    for child in list(body):
        if child.tag in (qn("a:noAutofit"), qn("a:normAutofit"), qn("a:spAutoFit")):
            body.remove(child)
    fit = body.makeelement(qn("a:normAutofit"), {"fontScale": str(font_scale)})
    body.append(fit)
    return shape
