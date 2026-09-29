"""Build a pack's templates from its pack.toml, as raw OOXML (spec 002 §5.3, plan Q-17).

One template per mode: a 16:9 package with no slides, one master, one layout per layout
name in the pack's regions, and a theme whose colours and fonts are pack values. Master
and layouts hold placeholders only (FP-2: spec 001 does not lint layout or master
shapes); every placeholder sits on a region box and carries its style's size, weight,
colour, caps, tracking and spacing in its lstStyle, so text typed by hand lands on scale.

Output is byte-stable (zipnorm). Uses lxml only: lint never imports this module and the
pen extra is not needed to rebuild templates.
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from lxml import etree

from keyline import zipnorm
from keyline.packs import SLIDE_H, SLIDE_W, THEME_SLOTS, Pack, Style

CREATED = "2026-09-27T00:00:00Z"  # fixed, so the pen can copy it into every deck (§6.5)
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS = f'xmlns:a="{A}" xmlns:r="{R}" xmlns:p="{P}"'
RT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT_P = "application/vnd.openxmlformats-officedocument.presentationml"
PROMPTS = {"title": "Headline", "main": "Text", "side": "Text", "footer": "Source: …"}


def _xml(text: str) -> bytes:
    """Parse (so every part is well-formed) and serialise deterministically."""
    root = etree.fromstring(text.encode("utf-8"))
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


PKG_RT = "http://schemas.openxmlformats.org/package/2006/relationships"


def _rels(items: list[tuple[str, str, str]]) -> bytes:
    """(id, type, target); a type starting with "pkg:" is a package relationship type."""

    def full(t: str) -> str:
        return f"{PKG_RT}/{t[4:]}" if t.startswith("pkg:") else f"{RT}/{t}"

    body = "".join(f'<Relationship Id="{i}" Type="{full(t)}" Target="{g}"/>' for i, t, g in items)
    return _xml(
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{body}</Relationships>"
    )


def _solid(hex_rgb: str) -> str:
    return f'<a:solidFill><a:srgbClr val="{hex_rgb}"/></a:solidFill>'


def _ppr(pack: Pack, style: Style, surface: str, level: int, title: bool) -> str:
    """One a:lvlNpPr carrying the style (lstStyle, txStyles and defaultTextStyle use it)."""
    colour = pack.hex(style.color.get(surface, next(iter(style.color.values()))))
    spc = int(style.tracking * style.size_pt * 100)  # tracking as 1/100 pt
    caps = ' cap="all"' if style.caps else ""
    bold = "1" if style.weight == "bold" else "0"
    font = "+mj-lt" if title else "+mn-lt"
    return (
        f'<a:lvl{level}pPr marL="0" indent="0" algn="l">'
        f'<a:lnSpc><a:spcPct val="{int(style.line_spacing * 100000)}"/></a:lnSpc>'
        f'<a:spcBef><a:spcPts val="{int(style.space_before_pt * 100)}"/></a:spcBef>'
        f'<a:spcAft><a:spcPts val="{int(style.space_after_pt * 100)}"/></a:spcAft>'
        "<a:buNone/>"
        f'<a:defRPr sz="{style.size_hundredths}" b="{bold}" i="0"{caps} spc="{spc}">'
        f'{_solid(colour)}<a:latin typeface="{font}"/></a:defRPr></a:lvl{level}pPr>'
    )


def _levels(pack: Pack, style: Style, surface: str, title: bool) -> str:
    return "".join(_ppr(pack, style, surface, n, title) for n in range(1, 10))


_BODY_PR = (
    '<a:bodyPr vert="horz" wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" rtlCol="0" '
    'anchor="t"><a:noAutofit/></a:bodyPr>'
)


def _placeholder(sid, name, ph, box, lst_style, prompt) -> str:
    return (
        f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{name}"/>'
        '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
        f"<p:nvPr>{ph}</p:nvPr></p:nvSpPr>"
        f'<p:spPr><a:xfrm><a:off x="{box.x}" y="{box.y}"/><a:ext cx="{box.w}" cy="{box.h}"/>'
        '</a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
        f"<p:txBody>{_BODY_PR}<a:lstStyle>{lst_style}</a:lstStyle>"
        f'<a:p><a:r><a:rPr lang="en-US"/><a:t>{escape(prompt)}</a:t></a:r></a:p>'
        "</p:txBody></p:sp>"
    )


_TREE_HEAD = (
    '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
    '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/>'
    '<a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
)


def _bg(hex_rgb: str) -> str:
    return f"<p:bg><p:bgPr>{_solid(hex_rgb)}<a:effectLst/></p:bgPr></p:bg>"


def _layout(pack: Pack, mode: str, layout: str) -> bytes:
    role = pack.layout_role(layout)
    surface = pack.surfaces[role.surface]
    styles = pack.styles[mode]
    shapes = []
    sid = 2
    for region in pack.regions[layout]:
        box = pack.region_box(layout, region)
        if region == "title":
            style = styles[role.title]
            ph = '<p:ph type="title" hasCustomPrompt="1"/>'
            is_title = True
        else:
            style = styles[pack.placeholder_styles[layout][region]]
            ph = f'<p:ph type="body" idx="{pack.placeholder_idx[region]}" hasCustomPrompt="1"/>'
            is_title = False
        lst = _ppr(pack, style, role.surface, 1, is_title)
        shapes.append(_placeholder(sid, region.capitalize(), ph, box, lst, PROMPTS[region]))
        sid += 1
    background = _bg(pack.hex(surface.background)) if role.surface != "paper" else ""
    return _xml(
        f'<p:sldLayout {NS} preserve="1" userDrawn="1"><p:cSld name="{layout}">{background}'
        f"<p:spTree>{_TREE_HEAD}{''.join(shapes)}</p:spTree></p:cSld>"
        "<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>"
    )


def _master(pack: Pack, mode: str, layout_count: int) -> bytes:
    styles = pack.styles[mode]
    title, body = styles["headline"], styles["body"]
    ref = "keyline:evidence"
    shapes = _placeholder(
        2,
        "Title",
        '<p:ph type="title"/>',
        pack.region_box(ref, "title"),
        _ppr(pack, title, "paper", 1, True),
        PROMPTS["title"],
    ) + _placeholder(
        3,
        "Main",
        f'<p:ph type="body" idx="{pack.placeholder_idx["main"]}"/>',
        pack.region_box(ref, "main"),
        _ppr(pack, body, "paper", 1, False),
        PROMPTS["main"],
    )
    clr_map = (
        'bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" '
        'accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" '
        'hlink="hlink" folHlink="folHlink"'
    )
    ids = "".join(
        f'<p:sldLayoutId id="{2147483649 + i}" r:id="rId{i + 1}"/>' for i in range(layout_count)
    )
    return _xml(
        f"<p:sldMaster {NS}><p:cSld>{_bg(pack.hex('paper'))}<p:spTree>{_TREE_HEAD}{shapes}"
        f"</p:spTree></p:cSld><p:clrMap {clr_map}/><p:sldLayoutIdLst>{ids}</p:sldLayoutIdLst>"
        "<p:txStyles>"
        f"<p:titleStyle>{_levels(pack, title, 'paper', True)}</p:titleStyle>"
        f"<p:bodyStyle>{_levels(pack, body, 'paper', False)}</p:bodyStyle>"
        f"<p:otherStyle>{_levels(pack, body, 'paper', False)}</p:otherStyle>"
        "</p:txStyles></p:sldMaster>"
    )


def _theme(pack: Pack) -> bytes:
    slots = "".join(
        f'<a:{s}><a:srgbClr val="{pack.hex(pack.theme[s])}"/></a:{s}>' for s in THEME_SLOTS
    )
    major = minor = pack.fonts[0]
    fonts = (
        f'<a:majorFont><a:latin typeface="{major}"/><a:ea typeface=""/><a:cs typeface=""/>'
        f'</a:majorFont><a:minorFont><a:latin typeface="{minor}"/><a:ea typeface=""/>'
        '<a:cs typeface=""/></a:minorFont>'
    )
    fill = '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    line = f'<a:ln w="6350">{fill}</a:ln>'
    effect = "<a:effectStyle><a:effectLst/></a:effectStyle>"
    return _xml(
        f'<a:theme xmlns:a="{A}" name="keyline {pack.name}"><a:themeElements>'
        f'<a:clrScheme name="{pack.name}">{slots}</a:clrScheme>'
        f'<a:fontScheme name="{pack.name}">{fonts}</a:fontScheme>'
        f'<a:fmtScheme name="{pack.name}"><a:fillStyleLst>{fill * 3}</a:fillStyleLst>'
        f"<a:lnStyleLst>{line * 3}</a:lnStyleLst><a:effectStyleLst>{effect * 3}"
        f"</a:effectStyleLst><a:bgFillStyleLst>{fill * 3}</a:bgFillStyleLst></a:fmtScheme>"
        "</a:themeElements><a:objectDefaults/><a:extraClrSchemeLst/></a:theme>"
    )


def _presentation(pack: Pack, mode: str) -> bytes:
    body = pack.styles[mode]["body"]
    return _xml(
        f'<p:presentation {NS} saveSubsetFonts="1"><p:sldMasterIdLst>'
        '<p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
        f'<p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}"/><p:notesSz cx="6858000" cy="9144000"/>'
        f"<p:defaultTextStyle>{_levels(pack, body, 'paper', False)}</p:defaultTextStyle>"
        "</p:presentation>"
    )


def _core(pack: Pack, mode: str) -> bytes:
    return _xml(
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/'
        'metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        f"<dc:title>keyline {pack.name} ({mode})</dc:title><dc:creator></dc:creator>"
        "<cp:lastModifiedBy></cp:lastModifiedBy><cp:revision>1</cp:revision>"
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{CREATED}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{CREATED}</dcterms:modified>'
        "</cp:coreProperties>"
    )


def build(pack: Pack, mode: str) -> bytes:
    """The template for one mode, as normalised zip bytes."""
    layouts = list(pack.regions)
    n = len(layouts)
    overrides = [
        ("/ppt/presentation.xml", f"{CT_P}.presentation.main+xml"),
        ("/ppt/slideMasters/slideMaster1.xml", f"{CT_P}.slideMaster+xml"),
        *(
            (f"/ppt/slideLayouts/slideLayout{i + 1}.xml", f"{CT_P}.slideLayout+xml")
            for i in range(n)
        ),
        ("/ppt/theme/theme1.xml", "application/vnd.openxmlformats-officedocument.theme+xml"),
        ("/ppt/presProps.xml", f"{CT_P}.presProps+xml"),
        ("/ppt/viewProps.xml", f"{CT_P}.viewProps+xml"),
        ("/ppt/tableStyles.xml", f"{CT_P}.tableStyles+xml"),
        ("/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"),
        (
            "/docProps/app.xml",
            "application/vnd.openxmlformats-officedocument.extended-properties+xml",
        ),
    ]
    content_types = _xml(
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
        'relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
        + "".join(f'<Override PartName="{p}" ContentType="{c}"/>' for p, c in overrides)
        + "</Types>"
    )
    entries = [
        ("[Content_Types].xml", content_types),
        (
            "_rels/.rels",
            _rels(
                [
                    ("rId1", "officeDocument", "ppt/presentation.xml"),
                    ("rId2", "pkg:metadata/core-properties", "docProps/core.xml"),
                    ("rId3", "extended-properties", "docProps/app.xml"),
                ]
            ),
        ),
        ("docProps/core.xml", _core(pack, mode)),
        (
            "docProps/app.xml",
            _xml(
                '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/'
                'extended-properties"><Application>keyline</Application>'
                "<PresentationFormat>Widescreen</PresentationFormat></Properties>"
            ),
        ),
        ("ppt/presentation.xml", _presentation(pack, mode)),
        (
            "ppt/_rels/presentation.xml.rels",
            _rels(
                [
                    ("rId1", "slideMaster", "slideMasters/slideMaster1.xml"),
                    ("rId2", "theme", "theme/theme1.xml"),
                    ("rId3", "presProps", "presProps.xml"),
                    ("rId4", "viewProps", "viewProps.xml"),
                    ("rId5", "tableStyles", "tableStyles.xml"),
                ]
            ),
        ),
        ("ppt/presProps.xml", _xml(f"<p:presentationPr {NS}/>")),
        (
            "ppt/viewProps.xml",
            _xml(
                f'<p:viewPr {NS}><p:gridSpacing cx="{pack.grid.row_emu}" '
                f'cy="{pack.grid.row_emu}"/></p:viewPr>'
            ),
        ),
        (
            "ppt/tableStyles.xml",
            _xml(f'<a:tblStyleLst xmlns:a="{A}" def="{{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}}"/>'),
        ),
        ("ppt/theme/theme1.xml", _theme(pack)),
        ("ppt/slideMasters/slideMaster1.xml", _master(pack, mode, n)),
        (
            "ppt/slideMasters/_rels/slideMaster1.xml.rels",
            _rels(
                [
                    (f"rId{i + 1}", "slideLayout", f"../slideLayouts/slideLayout{i + 1}.xml")
                    for i in range(n)
                ]
                + [(f"rId{n + 1}", "theme", "../theme/theme1.xml")]
            ),
        ),
    ]
    for i, layout in enumerate(layouts):
        entries.append((f"ppt/slideLayouts/slideLayout{i + 1}.xml", _layout(pack, mode, layout)))
        entries.append(
            (
                f"ppt/slideLayouts/_rels/slideLayout{i + 1}.xml.rels",
                _rels([("rId1", "slideMaster", "../slideMasters/slideMaster1.xml")]),
            )
        )
    return zipnorm.pack_bytes(entries)


def write_all(pack: Pack, out_dir: Path | None = None) -> list[Path]:
    """Write every mode's template (into the pack directory unless `out_dir` is given)."""
    out_dir = Path(out_dir) if out_dir is not None else pack.directory
    written = []
    for mode in pack.modes:
        path = out_dir / pack.templates[mode]
        path.write_bytes(build(pack, mode))
        written.append(path)
    return written
