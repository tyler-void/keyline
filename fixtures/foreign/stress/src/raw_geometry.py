# Adapted from audit 02's stress-corpus/src/raw_geometry.py: output paths, test photo and the Tyler author only (see _stress.py).
"""D17: geometry and visibility cases PowerPoint writes, built with python-pptx + raw XML.

Slide size 33.867 x 19.05 cm (16:9).
1 cover
2 rotation: R1 is 16x2 cm centred at (7, 9.525) with rot=90deg. Unrotated it would run
  1 cm off the left edge; its rotated box is x 6..8, y 1.525..17.525 (inside).
  R2 is 20x2 cm centred at (20, 9.525) with rot=90deg: unrotated inside, rotated box
  y -0.475..19.525 (0.475 cm off the top and bottom).
3 rotated group: group box x 10..30, y 7.525..11.525, rot=90deg about (20, 9.525).
  Child A (group-left 4x4 cm) lands at x 18..22, y -0.475..3.525 (off the top);
  child B (group-right) lands at y 15.525..19.525 (off the bottom).
4 hidden shapes (cNvPr hidden="1"): a parked note 5 cm left of the slide, white text on
  white, and a big hidden box filling the lower half (the lower half is visually empty).
5 mc:AlternateContent equation text box (PowerPoint's a14:m markup) at x = 0.3 cm,
  filling the lower 2/3 of the slide.
6 normAutofit fontScale=55%: 20 pt body text renders at 11 pt.
7 full-width header band (touches left/top/right) with the title inside it, and a
  full-bleed photo on the right half (touches top/right/bottom).
8 full-slide background photo with a title at the top (backgrounds are not content).
"""
import sys

import _stress  # noqa: E402  (fixtures/foreign/stress/src)
from pptx import Presentation
from pptx.oxml import parse_xml
from pptx.oxml.ns import qn
from pptx.util import Cm, Emu, Inches, Pt

out = _stress.out_path("d17_raw_geometry.pptx")
NSDECL = ('xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
          'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')
prs = Presentation()
prs.slide_width, prs.slide_height = Cm(33.867), Cm(19.05)
blank = prs.slide_layouts[6]
PHOTO = _stress.photo()
_id = [100]


def nid():
    _id[0] += 1
    return _id[0]


def cm(v):
    return int(round(v * 360000))


def sp_xml(name, x, y, w, h, text, size=24, color="1A1A1A", rot=0, hidden=False, fill=None,
           bodypr_extra="", ns=True):
    hid = ' hidden="1"' if hidden else ""
    r = f' rot="{rot}"' if rot else ""
    fillx = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else "<a:noFill/>"
    decl = " " + NSDECL if ns else ""
    return (f'<p:sp{decl}><p:nvSpPr><p:cNvPr id="{nid()}" name="{name}"{hid}/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm{r}><a:off x="{cm(x)}" y="{cm(y)}"/><a:ext cx="{cm(w)}" cy="{cm(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>{fillx}</p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square">{bodypr_extra}</a:bodyPr><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="{size*100}" dirty="0">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:rPr><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp>')


def add(slide, xml):
    tree = slide.shapes._spTree
    tree.append(parse_xml(xml))


def title(slide, text, x=2.0, y=1.5, w=29.867, h=2.2, color="111111"):
    add(slide, sp_xml("Title", x, y, w, h, text, 40, color))


def notes(slide):
    slide.notes_slide.notes_text_frame.text = "notes"


# 1 cover
s = prs.slides.add_slide(blank); title(s, "Geometry and visibility", 2, 8, 29.867, 3); notes(s)

# 2 rotated single shapes
s = prs.slides.add_slide(blank); title(s, "Rotated text boxes"); notes(s)
add(s, sp_xml("R1 rotated inside", 7 - 8, 9.525 - 1, 16, 2, "Rotated label inside the slide", 20, rot=5400000))
add(s, sp_xml("R2 rotated outside", 20 - 10, 9.525 - 1, 20, 2, "Rotated label that runs off the top and bottom", 20, rot=5400000))

# 3 rotated group
s = prs.slides.add_slide(blank); title(s, "Rotated group", 2, 1.5, 12, 2.2); notes(s)
grp = (f'<p:grpSp {NSDECL}><p:nvGrpSpPr><p:cNvPr id="{nid()}" name="Rotated group"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
       f'<p:grpSpPr><a:xfrm rot="5400000"><a:off x="{cm(10)}" y="{cm(7.525)}"/><a:ext cx="{cm(20)}" cy="{cm(4)}"/>'
       f'<a:chOff x="0" y="0"/><a:chExt cx="{cm(20)}" cy="{cm(4)}"/></a:xfrm></p:grpSpPr>'
       + sp_xml("Child A", 0, 0, 4, 4, "Alpha step", 20, ns=False)
       + sp_xml("Child B", 16, 0, 4, 4, "Omega step", 20, ns=False)
       + '</p:grpSp>')
add(s, grp)

# 4 hidden shapes
s = prs.slides.add_slide(blank); title(s, "Hidden shapes"); notes(s)
add(s, sp_xml("Visible body", 2, 4.5, 29.867, 3.5, "Only this paragraph and the title are visible on the slide", 24))
add(s, sp_xml("Parked note", -9, 5, 7, 3, "Parked note kept off the slide and hidden", 24, hidden=True))
add(s, sp_xml("Hidden white", 2, 8.5, 29.867, 2, "Hidden white text on the white slide background", 24, "FFFFFF", hidden=True))
add(s, sp_xml("Hidden filler", 2, 11, 29.867, 6.5, "A hidden box that fills the lower part of the slide", 24, hidden=True))

# 5 mc:AlternateContent equation box
s = prs.slides.add_slide(blank); title(s, "An equation"); notes(s)
eq_id = nid()
ac = (f'<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" {NSDECL}>'
      f'<mc:Choice xmlns:a14="http://schemas.microsoft.com/office/drawing/2010/main" Requires="a14">'
      f'<p:sp><p:nvSpPr><p:cNvPr id="{eq_id}" name="TextBox {eq_id}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
      f'<p:spPr><a:xfrm><a:off x="{cm(0.3)}" y="{cm(5)}"/><a:ext cx="{cm(31)}" cy="{cm(12)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
      f'<p:txBody><a:bodyPr wrap="square"><a:spAutoFit/></a:bodyPr><a:lstStyle/>'
      f'<a:p><a14:m><m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><m:oMathParaPr><m:jc m:val="centerGroup"/></m:oMathParaPr>'
      f'<m:oMath><m:r><a:rPr lang="en-US" sz="4000" i="1"><a:latin typeface="Cambria Math"/></a:rPr><m:t>E=m</m:t></m:r></m:oMath></m:oMathPara></a14:m>'
      f'<a:endParaRPr lang="en-US" sz="4000"/></a:p>'
      f'<a:p><a:r><a:rPr lang="en-US" sz="2400"><a:solidFill><a:srgbClr val="1A1A1A"/></a:solidFill></a:rPr><a:t>The equation above relates energy and mass in one short line of symbols</a:t></a:r></a:p>'
      f'</p:txBody></p:sp></mc:Choice>'
      f'<mc:Fallback><p:sp><p:nvSpPr><p:cNvPr id="{eq_id}" name="TextBox {eq_id}"/><p:cNvSpPr txBox="1"><a:spLocks noRot="1" noChangeAspect="1" noMove="1" noResize="1" noTextEdit="1"/></p:cNvSpPr><p:nvPr/></p:nvSpPr>'
      f'<p:spPr><a:xfrm><a:off x="{cm(0.3)}" y="{cm(5)}"/><a:ext cx="{cm(31)}" cy="{cm(12)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="F2F2F2"/></a:solidFill></p:spPr>'
      f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US"><a:noFill/></a:rPr><a:t> </a:t></a:r></a:p></p:txBody></p:sp></mc:Fallback>'
      f'</mc:AlternateContent>')
add(s, ac)

# 6 normAutofit fontScale 55%
s = prs.slides.add_slide(blank); title(s, "Shrunk body text"); notes(s)
add(s, sp_xml("Autofit body", 2, 4.5, 29.867, 12.5,
              "This twenty point paragraph was shrunk by autofit and now renders at about eleven points on the slide", 20,
              bodypr_extra='<a:normAutofit fontScale="55000" lnSpcReduction="20000"/>'))

# 7 full-width header band + full-bleed half photo
s = prs.slides.add_slide(blank); notes(s)
add(s, sp_xml("Header band", 0, 0, 33.867, 3.6, "Title inside a full-width band", 36, "FFFFFF", fill="14213D"))
pic = s.shapes.add_picture(PHOTO, Cm(16.933), Cm(3.6), Cm(16.934), Cm(15.45))
add(s, sp_xml("Left body", 2, 5, 13, 12, "Body text on the left half next to a photo that bleeds off the right side", 24))

# 8 full-slide background photo with a title
s = prs.slides.add_slide(blank); notes(s)
s.shapes.add_picture(PHOTO, 0, 0, prs.slide_width, prs.slide_height)
add(s, sp_xml("Photo title", 2, 1.5, 29.867, 2.2, "A full-bleed photo slide", 40, "FFFFFF"))

_stress.tyler(prs)
prs.save(out)
print("wrote", out)
