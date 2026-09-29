"""The python-pptx writer (D-015): the only module of the pen that imports python-pptx.
It opens the voice's template, adds one slide per plan on the named layout, fills the
layout's placeholders or adds shapes at their region boxes, removes the placeholders it
did not fill, and writes speaker notes. Every text body gets `a:noAutofit`, wrap on and
zero insets (§6.2)."""

from __future__ import annotations

import io

from lxml import etree

from keyline.pen._plan import ParaSpec, RectSpec, SlidePlan, TextSpec

A = "http://schemas.openxmlformats.org/drawingml/2006/main"


def _a(tag: str) -> str:
    return f"{{{A}}}{tag}"


def _body_pr(tf, anchor: str) -> None:
    body = tf._txBody.find(_a("bodyPr"))
    for child in list(body):
        if child.tag in (_a("noAutofit"), _a("normAutofit"), _a("spAutoFit")):
            body.remove(child)
    for key in ("lIns", "tIns", "rIns", "bIns"):
        body.set(key, "0")
    body.set("wrap", "square")
    body.set("anchor", anchor)
    # schema order: an optional prstTxWarp, then the autofit choice, then the rest
    warp = body.find(_a("prstTxWarp"))
    body.insert(0 if warp is None else 1, etree.Element(_a("noAutofit")))


def _paragraph(spec: ParaSpec) -> etree._Element:
    p = etree.Element(_a("p"))
    ppr = etree.SubElement(p, _a("pPr"), marL=str(spec.indent), algn="l")
    ppr.set("indent", str(-spec.indent) if spec.bullet else "0")
    etree.SubElement(etree.SubElement(ppr, _a("lnSpc")), _a("spcPct"), val=str(spec.line_spacing))
    etree.SubElement(etree.SubElement(ppr, _a("spcBef")), _a("spcPts"), val=str(spec.space_before))
    etree.SubElement(etree.SubElement(ppr, _a("spcAft")), _a("spcPts"), val=str(spec.space_after))
    if spec.bullet:
        etree.SubElement(ppr, _a("buChar"), char=spec.bullet)
    else:
        etree.SubElement(ppr, _a("buNone"))
    for run in spec.runs:
        r = etree.SubElement(p, _a("r"))
        rpr = etree.SubElement(
            r,
            _a("rPr"),
            lang="en-US",
            sz=str(run.size),
            b="1" if run.bold else "0",
            i="0",
            spc=str(run.spacing),
        )
        if run.caps:
            rpr.set("cap", "all")
        fill = etree.SubElement(rpr, _a("solidFill"))
        etree.SubElement(fill, _a("srgbClr"), val=run.color)
        etree.SubElement(rpr, _a("latin"), typeface=run.font)
        etree.SubElement(r, _a("t")).text = run.text
    return p


def _fill(shape, spec: TextSpec) -> None:
    tf = shape.text_frame
    _body_pr(tf, spec.anchor)
    body = tf._txBody
    for p in body.findall(_a("p")):
        body.remove(p)
    for para in spec.paragraphs:
        body.append(_paragraph(para))


def write(template: bytes, slides: list[SlidePlan], author: str) -> bytes:
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.util import Emu

    prs = Presentation(io.BytesIO(template))
    layouts = {layout.name: layout for layout in prs.slide_layouts}
    for plan in slides:
        slide = prs.slides.add_slide(layouts[plan.layout])
        placeholders = {ph.placeholder_format.idx: ph for ph in slide.placeholders}
        used = set()
        for spec in plan.shapes:
            if isinstance(spec, TextSpec):
                if spec.placeholder is not None:
                    shape = placeholders[spec.placeholder]
                    used.add(spec.placeholder)
                else:
                    b = spec.box
                    shape = slide.shapes.add_textbox(Emu(b.x), Emu(b.y), Emu(b.w), Emu(b.h))
                shape.name = spec.name
                _fill(shape, spec)
            elif isinstance(spec, RectSpec):
                b = spec.box
                rect = slide.shapes.add_shape(
                    MSO_SHAPE.RECTANGLE, Emu(b.x), Emu(b.y), Emu(b.w), Emu(b.h)
                )
                rect.name = spec.name
                rect.fill.solid()
                rect.fill.fore_color.rgb = RGBColor.from_string(spec.fill)
                rect.line.fill.background()
                rect.shadow.inherit = False
            else:  # pragma: no cover - a plan type the writer does not know
                raise TypeError(f"unknown plan {type(spec).__name__}")
        for idx, ph in placeholders.items():
            if idx not in used:
                ph.element.getparent().remove(ph.element)
        if plan.notes:
            slide.notes_slide.notes_text_frame.text = plan.notes
    cp = prs.core_properties
    cp.author = cp.last_modified_by = author
    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()
