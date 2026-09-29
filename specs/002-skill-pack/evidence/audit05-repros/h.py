"""Harness: build with the pen, convert with LibreOffice, read word boxes from the PDF."""
import html
import re
import subprocess
from pathlib import Path

from keyline.packs import resolve

W = Path("/tmp/keyline-audit05")
PROFILE = "file:///tmp/keyline-audit05/lo-profile"


def to_pdf(pptx):
    pptx = Path(pptx)
    out = pptx.with_suffix(".pdf")
    subprocess.run(
        ["soffice", f"-env:UserInstallation={PROFILE}", "--headless", "--convert-to", "pdf",
         "--outdir", str(pptx.parent), str(pptx)],
        check=True, capture_output=True, timeout=240,
    )
    return out


def words(pdf):
    """[(page, xMin, yMin, xMax, yMax, text)] in pt"""
    xml = subprocess.run(["pdftotext", "-bbox", str(pdf), "-"], capture_output=True, text=True).stdout
    res = []
    page = 0
    for line in xml.splitlines():
        if "<page " in line:
            page += 1
        m = re.search(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*)</word>', line)
        if m:
            res.append((page, *map(float, m.groups()[:4]), html.unescape(m.group(5))))
    return res


def region_pt(layout, region, pack="swiss"):
    p = resolve(pack)
    b = p.region_box(layout, region)
    return (b.x / 12700, b.y / 12700, (b.x + b.w) / 12700, (b.y + b.h) / 12700)


def report(pdf, boxes, quiet=False):
    """boxes: {page: (x0,y0,x1,y1)}; print words outside their region."""
    ws = words(pdf)
    bad = 0
    for page, x0, y0, x1, y1, t in ws:
        if page in boxes:
            bx0, by0, bx1, by1 = boxes[page]
            flags = []
            if x1 > bx1 + 1:
                flags.append(f"right+{x1 - bx1:.1f}")
            if y1 > by1 + 1:
                flags.append(f"bottom+{y1 - by1:.1f}")
            if flags:
                bad += 1
                if not quiet:
                    print(f"  p{page} OUTSIDE {flags} word={t[:40]!r} "
                          f"box=({x0:.1f},{y0:.1f},{x1:.1f},{y1:.1f}) "
                          f"region=({bx0:.1f},{by0:.1f},{bx1:.1f},{by1:.1f})")
    return ws, bad
