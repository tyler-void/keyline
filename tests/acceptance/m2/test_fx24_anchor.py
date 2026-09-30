"""Audit 05 FX-24 (Tyler, audit 05 §4): a vertical anchor per region in pack.toml. The
cover, evidence and close titles are "b", so a one-line title sits on the lede or the
keyline rule; every other region is "t". A bottom-anchored text box gets a bottom inset of
its descent room, so the last line's descenders stay inside the region (A2 fixes)."""

import math
import re
import shutil
import zipfile

import pytest

from keyline.fit import Setting
from keyline.packs import PackError, load, resolve
from tests.acceptance.m2 import _lo

pytest.importorskip("pptx")

from keyline.pen import Deck

PACK = resolve("swiss")
BOTTOM = {"keyline:cover", "keyline:evidence", "keyline:evidence:figure", "keyline:close"}


def test_the_swiss_anchors():
    for layout, regions in PACK.regions.items():
        for name, region in regions.items():
            expected = "b" if name == "title" and layout in BOTTOM else "t"
            assert region.anchor == expected, (layout, name)


def test_an_anchor_is_t_or_b(tmp_path):
    shutil.copytree(PACK.directory, tmp_path / "swiss")
    toml = tmp_path / "swiss/pack.toml"
    text = toml.read_text(encoding="utf-8")
    toml.write_text(text.replace('rows = 4, anchor = "t" }', 'rows = 4, anchor = "middle" }'))
    with pytest.raises(PackError, match=r'regions\.keyline:section\.main\.anchor: must be "t"'):
        load(tmp_path / "swiss")
    toml.write_text(text.replace(', anchor = "t" }', " }"))  # absent: top
    assert all(
        r.anchor == ("b" if n == "title" and lay in BOTTOM else "t")
        for lay, rs in load(tmp_path / "swiss").regions.items()
        for n, r in rs.items()
    )


def body_prs(path):
    """Per slide, {text shape name: (anchor, bIns)}."""
    from lxml import etree

    a = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    p = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
    z = zipfile.ZipFile(path)
    names = sorted(
        (n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
        key=lambda n: int(re.search(r"\d+", n).group()),
    )
    out = []
    for n in names:
        shapes = {}
        for sp in etree.fromstring(z.read(n)).iter(f"{p}sp"):
            body = sp.find(f"{p}txBody/{a}bodyPr")
            if body is not None and body.get("bIns") is not None:
                name = sp.find(f".//{p}cNvPr").get("name")
                shapes[name] = (body.get("anchor"), int(body.get("bIns")))
        out.append(shapes)
    return out


def descent_inset(voice, style_name, mode):
    style = PACK.styles[mode][style_name]
    setting = Setting(PACK.voice(voice).font(style.font), style.weight, style.size_pt)
    return math.ceil(setting.descent_room * 12700)


@pytest.mark.parametrize("voice", ["neutral", "field"])
def test_the_pen_writes_each_regions_anchor(voice, tmp_path):
    d = Deck(pack="swiss", mode="presented", voice=voice)
    d.add("cover", "Toolshed").text("A tool library", style="lede")
    d.add("statement", "Every tool comes back").text("Mended", style="lede")
    d.add("evidence", "Most tools need a repair").text("Saws first")
    d.add("close", "Bring them back").text("This season", style="lede")
    d.save(str(tmp_path / "a.pptx"))
    cover, statement, evidence, close = body_prs(tmp_path / "a.pptx")
    assert cover["title"] == ("b", descent_inset(voice, "cover_title", "presented"))
    assert evidence["title"] == ("b", descent_inset(voice, "headline", "presented"))
    assert close["title"] == ("b", descent_inset(voice, "cover_title", "presented"))
    assert statement["title"] == ("t", 0)
    assert {cover["main"], statement["main"], evidence["main"], close["main"]} == {("t", 0)}
    if voice == "field":  # Gelasio reaches 0.094 em below LibreOffice's line box
        assert evidence["title"][1] > 0


def test_the_templates_carry_the_anchors():
    for mode in ("presented", "read"):
        z = zipfile.ZipFile(PACK.directory / f"swiss-neutral-{mode}.pptx")
        for n in (n for n in z.namelist() if n.startswith("ppt/slideLayouts/slideLayout")):
            xml = z.read(n).decode()
            if "<p:sldLayout" not in xml:
                continue
            layout = re.search(r'<p:cSld name="([^"]+)"', xml).group(1)
            anchors = re.findall(r'<p:cNvPr id="\d+" name="(\w+)"/>.*?anchor="(\w)"', xml, re.S)
            for name, anchor in anchors:
                region = PACK.regions[layout][name.lower()]
                assert anchor == region.anchor, (mode, layout, name)


@_lo.needs_lo("Arial", "Georgia")
@pytest.mark.parametrize("voice", ["neutral", "field"])
def test_a_one_line_title_sits_on_the_bottom_of_its_region(voice, tmp_path):
    title = _lo.region_pt(PACK, "keyline:evidence", "title")
    d = Deck(pack="swiss", mode="presented", voice=voice)
    d.add("evidence", "Most tools gyp")  # one line, with descenders
    d.save(str(tmp_path / "t.pptx"))
    (page,) = _lo.chars(tmp_path / "t.pptx", tmp_path / "lo")
    top, bottom = min(c[2] for c in page), max(c[4] for c in page)
    size = float(PACK.styles["presented"]["headline"].size_pt)
    assert bottom <= title[3] + 1.5  # the descenders stay inside (2 px at 1280 px)
    assert bottom >= title[3] - 0.15 * size  # and the line sits on the region's bottom
    assert top > (title[1] + title[3]) / 2  # a one-line title in the lower half
