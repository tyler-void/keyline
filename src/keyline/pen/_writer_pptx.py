"""The python-pptx writer (D-015): the only module of the pen that imports python-pptx.
It opens the voice's template, adds one slide per plan on the named layout, fills the
layout's placeholders or adds shapes at their region boxes, removes the placeholders it
did not fill, and writes speaker notes. Every text body gets `a:noAutofit`, wrap on and
zero insets (§6.2)."""

from __future__ import annotations

import io

from lxml import etree

from keyline.fit.text import normalize, paragraphs
from keyline.pen._plan import (
    ChartSpec,
    ParaSpec,
    PictureSpec,
    RectSpec,
    SlidePlan,
    TableSpec,
    TextSpec,
)

C = "http://schemas.openxmlformats.org/drawingml/2006/chart"
NO_STYLE = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"  # "No Style, No Grid"
AXIS_ID_BASE = 500000000  # §6.6: positive, deterministic UInt32 axis ids

A = "http://schemas.openxmlformats.org/drawingml/2006/main"


def _a(tag: str) -> str:
    return f"{{{A}}}{tag}"


def _body_pr(tf, anchor: str, inset_bottom: int = 0) -> None:
    body = tf._txBody.find(_a("bodyPr"))
    for child in list(body):
        if child.tag in (_a("noAutofit"), _a("normAutofit"), _a("spAutoFit")):
            body.remove(child)
    for key in ("lIns", "tIns", "rIns"):
        body.set(key, "0")
    body.set("bIns", str(inset_bottom))
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
        # B-25 item 7: complex scripts in the voice's family too (+mj-cs / +mn-cs)
        etree.SubElement(rpr, _a("cs"), typeface=run.font.replace("-lt", "-cs"))
        etree.SubElement(r, _a("t")).text = normalize(run.text)  # as estimated (B-22)
    return p


def _fill(shape, spec: TextSpec) -> None:
    tf = shape.text_frame
    _body_pr(tf, spec.anchor, spec.inset_bottom)
    body = tf._txBody
    for p in body.findall(_a("p")):
        body.remove(p)
    for para in spec.paragraphs:
        body.append(_paragraph(para))


def _table(slide, spec: TableSpec) -> None:
    from pptx.util import Emu

    b = spec.box
    rows, cols = len(spec.row_heights), len(spec.col_widths)
    frame = slide.shapes.add_table(rows, cols, Emu(b.x), Emu(b.y), Emu(b.w), Emu(b.h))
    frame.name = spec.name
    table = frame.table
    tbl_pr = table._tbl.tblPr
    for attr in ("firstRow", "bandRow", "firstCol", "lastRow", "lastCol", "bandCol"):
        tbl_pr.attrib.pop(attr, None)
    style = tbl_pr.find(_a("tableStyleId"))
    if style is None:
        style = etree.SubElement(tbl_pr, _a("tableStyleId"))
    style.text = NO_STYLE
    for i, width in enumerate(spec.col_widths):
        table.columns[i].width = Emu(width)
    for r, height in enumerate(spec.row_heights):
        table.rows[r].height = Emu(height)
        for c in range(cols):
            cell = table.cell(r, c)
            left, right, top, bottom = spec.margins
            cell.margin_left, cell.margin_right = Emu(left), Emu(right)
            cell.margin_top, cell.margin_bottom = Emu(top), Emu(bottom)
            body = cell._tc.txBody
            for p in body.findall(_a("p")):
                body.remove(p)
            for para in spec.cells[r][c]:
                body.append(_paragraph(para))
            tc_pr = cell._tc.get_or_add_tcPr()
            for side in ("lnL", "lnR", "lnT", "lnB"):
                ln = etree.SubElement(tc_pr, _a(side))
                if side == "lnB":
                    ln.set("w", str(spec.rule_width))
                    fill = etree.SubElement(ln, _a("solidFill"))
                    etree.SubElement(fill, _a("srgbClr"), val=spec.rule)
                else:
                    ln.set("w", "0")
                    etree.SubElement(ln, _a("noFill"))
            etree.SubElement(tc_pr, _a("noFill"))
    # §6.3: a pen shape's box is its full region box, not the height of its rows
    frame.height = Emu(b.h)


def _renumber_axes(chart_space) -> None:
    """§6.6: python-pptx writes negative axis ids, which officecli validate rejects as
    UInt32; renumber them in document order, keeping each axId and crossAx paired."""
    mapping: dict[str, str] = {}
    for el in chart_space.iter(f"{{{C}}}axId"):
        val = el.get("val")
        if val not in mapping:
            mapping[val] = str(AXIS_ID_BASE + len(mapping) + 1)
        el.set("val", mapping[val])
    for el in chart_space.iter(f"{{{C}}}crossAx"):
        el.set("val", mapping.get(el.get("val"), el.get("val")))


def _chart(slide, spec: ChartSpec) -> None:
    from pptx.chart.data import CategoryChartData
    from pptx.dml.color import RGBColor
    from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
    from pptx.util import Emu, Pt

    data = CategoryChartData(number_format=spec.number_format)
    data.categories = [normalize(c) for c in spec.categories]
    data.add_series("series", list(spec.values))
    b = spec.box
    frame = slide.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED, Emu(b.x), Emu(b.y), Emu(b.w), Emu(b.h), data
    )
    frame.name = spec.name
    chart = frame.chart
    chart.has_legend = False
    chart.has_title = False
    chart.font.size = Pt(spec.size / 100)
    chart.font.name = spec.font
    chart.font.color.rgb = RGBColor.from_string(spec.text)
    plot = chart.plots[0]
    plot.gap_width = 60
    plot.has_data_labels = True
    labels = plot.data_labels
    labels.number_format, labels.number_format_is_linked = spec.number_format, False
    labels.position = XL_LABEL_POSITION.OUTSIDE_END
    series = plot.series[0]
    series.format.fill.solid()
    series.format.fill.fore_color.rgb = RGBColor.from_string(spec.bar)
    series.format.line.fill.background()
    if spec.highlight is not None:
        point = series.points[spec.highlight]
        point.format.fill.solid()
        point.format.fill.fore_color.rgb = RGBColor.from_string(spec.accent)
    value_axis = chart.value_axis
    value_axis.has_major_gridlines = True
    value_axis.major_gridlines.format.line.color.rgb = RGBColor.from_string(spec.rule)
    value_axis.major_gridlines.format.line.width = Emu(6350)
    value_axis.format.line.fill.background()
    value_axis.visible = False
    category_axis = chart.category_axis
    category_axis.format.line.color.rgb = RGBColor.from_string(spec.rule)
    category_axis.has_major_gridlines = False
    _renumber_axes(chart._chartSpace)


def _picture(slide, spec: PictureSpec) -> None:
    from pptx.util import Emu

    b = spec.box
    pic = slide.shapes.add_picture(io.BytesIO(spec.data), Emu(b.x), Emu(b.y), Emu(b.w), Emu(b.h))
    pic.name = spec.name
    pic._element.nvPicPr.cNvPr.set("descr", normalize(spec.descr))


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
            elif isinstance(spec, TableSpec):
                _table(slide, spec)
            elif isinstance(spec, ChartSpec):
                _chart(slide, spec)
            elif isinstance(spec, PictureSpec):
                _picture(slide, spec)
            else:  # pragma: no cover - a plan type the writer does not know
                raise TypeError(f"unknown plan {type(spec).__name__}")
        for idx, ph in placeholders.items():
            if idx not in used:
                ph.element.getparent().remove(ph.element)
        if plan.notes:
            slide.notes_slide.notes_text_frame.text = "\n".join(paragraphs(plan.notes))
    cp = prs.core_properties
    cp.author = cp.last_modified_by = author
    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()
