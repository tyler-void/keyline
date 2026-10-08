"""Harness: build slides with the pen, keep one region per slide plus a control slide,
convert with LibreOffice 24.2 (private profile), rasterize at 1280 px, and measure each
text's ink box against its region box (B-24 edges)."""
import html
import itertools
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

from lxml import etree
from PIL import Image, ImageChops

from keyline.packs import resolve
from keyline.pen import Deck, DoesNotFit, PenError

W = Path("/tmp/keyline-audit06")
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
SHAPES = {f"{{{P}}}{t}" for t in ("sp", "graphicFrame", "pic", "cxnSp", "grpSp")}
SLIDE_W, SLIDE_H = 12192000, 6858000
_count = itertools.count(1)
VOICES = W / "voices"


def voice(family):
    """A test-only voice: Swiss neutral with `family` (name = file stem)."""
    VOICES.mkdir(parents=True, exist_ok=True)
    src = Path("./src/keyline/packs/swiss/voices/neutral.toml").read_text()
    name = "t-" + family.lower().replace(" ", "-")
    path = VOICES / f"{name}.toml"
    path.write_text(src.replace('name = "neutral"', f'name = "{name}"').replace('"Arial"', f'"{family}"'))
    return str(path)


def keep_only(xml, keep):
    root = etree.fromstring(xml)
    tree = root.find(f"{{{P}}}cSld/{{{P}}}spTree")
    for child in list(tree):
        if child.tag in SHAPES:
            name = child.find(f".//{{{P}}}cNvPr").get("name")
            if not keep or (name != keep and not name.startswith(f"{keep}-")):
                tree.remove(child)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def build(deck, cases, path):
    """cases: [(label, fn(deck) -> builder, keep_region)]; each is built twice (content,
    control). Returns [(label, layout, keep)]"""
    order = []
    for label, fn, keep in cases:
        b = fn(deck)
        order.append((label, b._layout, keep))
        fn(deck)
    raw = Path(path).with_suffix(".full.pptx")
    deck.save(str(raw))
    src = zipfile.ZipFile(raw)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as out:
        for info in src.infolist():
            data = src.read(info.filename)
            name = info.filename
            m = re.fullmatch(r"ppt/slides/slide(\d+)\.xml", name)
            if m:
                k = int(m.group(1)) - 1
                data = keep_only(data, order[k // 2][2] if k % 2 == 0 else "")
            out.writestr(info, data)
    return order


def render(pptx):
    pptx = Path(pptx)
    n = next(_count)
    prof = f"file:///tmp/keyline-audit06/profile-{os.getpid()}-{n}"
    subprocess.run(
        ["soffice", f"-env:UserInstallation={prof}", "--headless", "--convert-to", "pdf",
         "--outdir", str(pptx.parent), str(pptx)],
        check=True, capture_output=True, timeout=600,
    )
    pdf = pptx.with_suffix(".pdf")
    prefix = pptx.with_suffix("")
    for old in pptx.parent.glob(prefix.name + "-*.png"):
        old.unlink()
    subprocess.run(["pdftoppm", "-png", "-scale-to-x", "1280", "-scale-to-y", "-1", str(pdf), str(prefix)],
                   check=True)
    pngs = sorted(pptx.parent.glob(prefix.name + "-*.png"), key=lambda p: int(p.stem.rsplit("-", 1)[1]))
    return pdf, [Image.open(p).convert("RGB") for p in pngs]


def ink_box(img, ctl):
    diff = ImageChops.difference(img, ctl)
    r, g, b = diff.split()
    s = ImageChops.lighter(ImageChops.lighter(r, g), b)
    return s.point(lambda v: 255 if v > 26 else 0).getbbox()


def measure(order, images, pack="swiss", allow=None):
    p = resolve(pack)
    out = []
    for i, (label, layout, keep) in enumerate(order):
        img, ctl = images[2 * i], images[2 * i + 1]
        sx, sy = img.width / SLIDE_W, img.height / SLIDE_H
        b = p.region_box(layout, keep)
        reg = (b.x * sx, b.y * sy, (b.x + b.w) * sx, (b.y + b.h) * sy)
        ink = ink_box(img, ctl)
        if ink is None:
            out.append((label, None))
            print(f"{label}: NO INK")
            continue
        e = {"left": reg[0] - ink[0], "top": reg[1] - ink[1], "right": ink[2] - reg[2],
             "bottom": ink[3] - reg[3]}
        out.append((label, e))
        worst = max(("top", "right", "bottom"), key=e.get)
        flag = "  <-- PAST 2px" if e[worst] > 2 else ""
        print(f"{label}: region={tuple(round(v,1) for v in reg)} ink={ink} "
              + " ".join(f"{k}{v:+.1f}" for k, v in e.items()) + flag)
    return out


def words(pdf):
    xml = subprocess.run(["pdftotext", "-bbox", str(pdf), "-"], capture_output=True, text=True).stdout
    res, page = [], 0
    for line in xml.splitlines():
        if "<page " in line:
            page += 1
        m = re.search(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*)</word>', line)
        if m:
            res.append((page, *map(float, m.groups()[:4]), html.unescape(m.group(5))))
    return res


def lines_on(pdf, page):
    """distinct word baselines (yMax rounded) on a page"""
    ys = sorted({round(w[4], 0) for w in words(pdf) if w[0] == page})
    return ys
