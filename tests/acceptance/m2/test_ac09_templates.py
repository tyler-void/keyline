"""Spec 002 AC-9 (template part): the §5.3 constraints on both Swiss templates, checked
through spec 001's own reader (not python-pptx), plus byte-identical rebuilds, a
python-pptx round trip, and `officecli validate` (skipped without OfficeCLI)."""

import subprocess

import pytest

from keyline.ooxml.color import DEFAULT_CLR_MAP, ColorContext
from keyline.ooxml.fill import background
from keyline.ooxml.ns import NS, q
from keyline.ooxml.package import Package
from keyline.ooxml.theme import parse_theme
from keyline.packs import resolve
from keyline.packs.templates import build
from keyline.roles import ROLES
from keyline.roles import parse as parse_role
from keyline.units import cm_to_emu

PACK = resolve("swiss")
MODES = ("presented", "read")
MARGIN = cm_to_emu("1.27")  # edge_margin_cm


def parts(mode):
    pkg = Package(PACK.template(mode))
    pres = pkg.xml(pkg.main_part)
    master_part = pkg.rel_targets(
        pkg.main_part,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster",
    )[0]
    layouts = pkg.rel_targets(
        master_part,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout",
    )
    theme = pkg.rel_targets(
        master_part, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme"
    )[0]
    return pkg, pres, pkg.xml(master_part), [pkg.xml(p) for p in layouts], pkg.xml(theme)


@pytest.mark.parametrize("mode", MODES)
def test_rebuild_is_byte_identical(mode):
    assert build(PACK, mode) == PACK.template(mode).read_bytes()


@pytest.mark.parametrize("mode", MODES)
def test_size_and_no_slides(mode):
    _, pres, *_ = parts(mode)
    size = pres.find("p:sldSz", NS)
    assert (size.get("cx"), size.get("cy")) == ("12192000", "6858000")
    assert pres.findall("p:sldIdLst/p:sldId", NS) == []


@pytest.mark.parametrize("mode", MODES)
def test_backgrounds(mode):
    _, _, master, layouts, theme = parts(mode)
    ctx = ColorContext(parse_theme(theme).colors, dict(DEFAULT_CLR_MAP))
    th = parse_theme(theme)
    assert background([master], th, ctx).fill == f"solid:#{PACK.hex('paper')}"
    for layout in layouts:
        name = layout.find("p:cSld", NS).get("name")
        want = "ink" if name == "keyline:section" else "paper"
        assert background([layout, master], th, ctx).fill == f"solid:#{PACK.hex(want)}", name


def _shapes(root):
    tree = root.find("p:cSld/p:spTree", NS)
    return [c for c in tree if c.tag not in (q("p:nvGrpSpPr"), q("p:grpSpPr"))]


@pytest.mark.parametrize("mode", MODES)
def test_master_and_layouts_hold_placeholders_only(mode):
    _, _, master, layouts, _ = parts(mode)
    for root in [master, *layouts]:
        for shape in _shapes(root):
            assert shape.tag == q("p:sp")
            assert shape.find("p:nvSpPr/p:nvPr/p:ph", NS) is not None


@pytest.mark.parametrize("mode", MODES)
def test_placeholders_keep_the_edge_margin(mode):
    _, _, master, layouts, _ = parts(mode)
    for root in [master, *layouts]:
        for shape in _shapes(root):
            off, ext = shape.find(".//a:off", NS), shape.find(".//a:ext", NS)
            x, y = int(off.get("x")), int(off.get("y"))
            w, h = int(ext.get("cx")), int(ext.get("cy"))
            assert min(x, y, 12192000 - x - w, 6858000 - y - h) >= MARGIN


@pytest.mark.parametrize("mode", MODES)
def test_theme_fonts_and_colours(mode):
    *_, theme = parts(mode)
    th = parse_theme(theme)
    assert (th.major_latin, th.minor_latin) == ("Arial", "Arial")
    assert len(th.colors) == 12
    assert set(th.colors.values()) <= set(PACK.palette.values())
    assert th.colors["dk1"] == PACK.hex("ink") and th.colors["lt1"] == PACK.hex("paper")
    assert th.colors["accent1"] == PACK.hex("accent") and th.colors["hlink"] == PACK.hex("ink")


@pytest.mark.parametrize("mode", MODES)
def test_layout_names_and_every_role(mode):
    *_, layouts, _ = parts(mode)
    names = [layout.find("p:cSld", NS).get("name") for layout in layouts]
    assert names == list(PACK.regions)
    assert {parse_role(n)[0] for n in names} == set(ROLES)


def _sz(ppr):
    return int(ppr.find("a:defRPr", NS).get("sz"))


def _colour(ppr):
    return ppr.find("a:defRPr/a:solidFill/a:srgbClr", NS).get("val")


@pytest.mark.parametrize("mode", MODES)
def test_placeholder_styles_carry_the_pack_scale(mode):
    *_, layouts, _ = parts(mode)
    styles = PACK.styles[mode]
    for layout in layouts:
        name = layout.find("p:cSld", NS).get("name")
        role = PACK.layout_role(name)
        for shape in _shapes(layout):
            ph = shape.find("p:nvSpPr/p:nvPr/p:ph", NS)
            ppr = shape.find("p:txBody/a:lstStyle/a:lvl1pPr", NS)
            if ph.get("type") == "title":
                style = styles[role.title]
            else:
                region = {v: k for k, v in PACK.placeholder_idx.items()}[int(ph.get("idx"))]
                style = styles[PACK.placeholder_styles[name][region]]
            assert _sz(ppr) == style.size_hundredths, (name, style.name)
            assert _colour(ppr) == PACK.hex(style.color[role.surface]), (name, style.name)


@pytest.mark.parametrize("mode", MODES)
def test_section_placeholders_are_paper_and_accent_on_ink(mode):
    *_, layouts, _ = parts(mode)
    (section,) = [x for x in layouts if x.find("p:cSld", NS).get("name") == "keyline:section"]
    colours = {_colour(s.find("p:txBody/a:lstStyle/a:lvl1pPr", NS)) for s in _shapes(section)}
    assert colours == {PACK.hex("paper"), PACK.hex("accent_on_ink")}


@pytest.mark.parametrize("mode", MODES)
def test_txstyles_and_default_text_style_carry_the_mode_sizes(mode):
    _, pres, master, _, _ = parts(mode)
    styles = PACK.styles[mode]
    tx = master.find("p:txStyles", NS)
    assert _sz(tx.find("p:titleStyle/a:lvl1pPr", NS)) == styles["headline"].size_hundredths
    for path in ("p:bodyStyle/a:lvl1pPr", "p:otherStyle/a:lvl1pPr"):
        assert _sz(tx.find(path, NS)) == styles["body"].size_hundredths
    assert _sz(pres.find("p:defaultTextStyle/a:lvl1pPr", NS)) == styles["body"].size_hundredths
    for level in range(1, 10):  # every level resolves, so no adapter-unresolved
        assert tx.find(f"p:bodyStyle/a:lvl{level}pPr/a:defRPr", NS) is not None


@pytest.mark.parametrize("mode", MODES)
def test_python_pptx_round_trip_lints_on_scale(mode, tmp_path):
    pptx = pytest.importorskip("pptx")
    from keyline.ooxml.adapter import load_deck

    prs = pptx.Presentation(str(PACK.template(mode)))
    for layout in prs.slide_layouts:
        slide = prs.slides.add_slide(layout)
        for ph in slide.placeholders:
            ph.text_frame.text = "Keepers wait a season"
    out = tmp_path / f"{mode}.pptx"
    prs.save(out)
    deck, diags = load_deck(out)
    assert diags == []
    sizes = {r.size for s in deck.slides for sh in s.shapes for r in sh.runs if r.has_ink}
    assert sizes <= PACK.scale(mode)
    fonts = {r.font for s in deck.slides for sh in s.shapes for r in sh.runs if r.has_ink}
    assert fonts == {"Arial"}
    assert [s.role for s in deck.slides] == [parse_role(n)[0] for n in PACK.regions]


@pytest.mark.officecli
@pytest.mark.parametrize("mode", MODES)
def test_officecli_validate(mode):
    proc = subprocess.run(
        ["officecli", "validate", str(PACK.template(mode))], capture_output=True, text=True
    )
    assert proc.returncode == 0 and "Validation passed" in proc.stdout, proc.stdout


def test_templates_are_package_data_next_to_pack_toml():
    for mode in MODES:
        assert PACK.template(mode).parent == PACK.directory
