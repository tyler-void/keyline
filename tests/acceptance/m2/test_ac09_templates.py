"""Spec 002 AC-9 (template part): the §5.3 constraints on the Swiss templates, checked
through spec 001's own reader (not python-pptx), for every stock voice and mode (B-8.9).
Templates are built in memory; only the neutral pair is committed, and it must rebuild
byte-identically. Plus a python-pptx round trip and `officecli validate` (skipped
without OfficeCLI)."""

import subprocess
import sys

import pytest

from keyline.ooxml.color import DEFAULT_CLR_MAP, ColorContext
from keyline.ooxml.fill import background
from keyline.ooxml.ns import NS, q
from keyline.ooxml.package import Package
from keyline.ooxml.theme import parse_theme
from keyline.packs import THEME_SLOTS, resolve
from keyline.packs.templates import build, committed, filename
from keyline.roles import ROLES
from keyline.roles import parse as parse_role
from keyline.units import cm_to_emu
from tests.conftest import ROOT

PACK = resolve("swiss")
MODES = ("presented", "read")
VOICES = tuple(PACK.voices())
CASES = [(v, m) for v in VOICES for m in MODES]
MARGIN = cm_to_emu("1.27")  # edge_margin_cm
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """Every (voice, mode) template, built in memory and written once for the reader."""
    out = tmp_path_factory.mktemp("templates")
    paths = {}
    for voice_name, mode in CASES:
        voice = PACK.voice(voice_name)
        path = out / filename(PACK, voice, mode)
        path.write_bytes(build(PACK, voice, mode))
        paths[voice_name, mode] = path
    return paths


def parts(path):
    pkg = Package(path)
    pres = pkg.xml(pkg.main_part)
    master_part = pkg.rel_targets(pkg.main_part, REL + "slideMaster")[0]
    layouts = pkg.rel_targets(master_part, REL + "slideLayout")
    theme = pkg.rel_targets(master_part, REL + "theme")[0]
    return pkg, pres, pkg.xml(master_part), [pkg.xml(p) for p in layouts], pkg.xml(theme)


def _shapes(root):
    tree = root.find("p:cSld/p:spTree", NS)
    return [c for c in tree if c.tag not in (q("p:nvGrpSpPr"), q("p:grpSpPr"))]


def _name(layout):
    return layout.find("p:cSld", NS).get("name")


def _ppr(shape):
    return shape.find("p:txBody/a:lstStyle/a:lvl1pPr", NS)


def _sz(ppr):
    return int(ppr.find("a:defRPr", NS).get("sz"))


def _colour(ppr):
    return ppr.find("a:defRPr/a:solidFill/a:srgbClr", NS).get("val")


def _typeface(ppr):
    return ppr.find("a:defRPr/a:latin", NS).get("typeface")


@pytest.mark.parametrize("mode", MODES)
def test_committed_neutral_rebuilds_byte_identically(mode):
    assert build(PACK, PACK.voice("neutral"), mode) == committed(PACK, mode).read_bytes()


def test_the_build_script_rebuilds_them_into_a_new_directory(tmp_path):
    out = tmp_path / "new" / "dir"
    script = ROOT / "src/keyline/packs/swiss/src/build_templates.py"
    subprocess.run([sys.executable, script, out], check=True, capture_output=True)
    for mode in MODES:
        built = (out / f"swiss-neutral-{mode}.pptx").read_bytes()
        assert built == committed(PACK, mode).read_bytes()


def test_only_the_neutral_templates_are_committed():
    assert sorted(p.name for p in PACK.directory.glob("*.pptx")) == [
        "swiss-neutral-presented.pptx",
        "swiss-neutral-read.pptx",
    ]


@pytest.mark.parametrize(("voice", "mode"), CASES)
def test_builds_are_byte_stable(voice, mode, built):
    assert build(PACK, PACK.voice(voice), mode) == built[voice, mode].read_bytes()


@pytest.mark.parametrize(("voice", "mode"), CASES)
def test_size_and_no_slides(voice, mode, built):
    _, pres, *_ = parts(built[voice, mode])
    size = pres.find("p:sldSz", NS)
    assert (size.get("cx"), size.get("cy")) == ("12192000", "6858000")
    assert pres.findall("p:sldIdLst/p:sldId", NS) == []


@pytest.mark.parametrize(("voice", "mode"), CASES)
def test_backgrounds(voice, mode, built):
    v = PACK.voice(voice)
    _, _, master, layouts, theme = parts(built[voice, mode])
    th = parse_theme(theme)
    ctx = ColorContext(th.colors, dict(DEFAULT_CLR_MAP))
    assert background([master], th, ctx).fill == f"solid:#{v.hex('paper')}"
    for layout in layouts:
        want = "ink" if _name(layout) == "keyline:section" else "paper"
        assert background([layout, master], th, ctx).fill == f"solid:#{v.hex(want)}"


@pytest.mark.parametrize(("voice", "mode"), CASES)
def test_master_and_layouts_hold_placeholders_only(voice, mode, built):
    _, _, master, layouts, _ = parts(built[voice, mode])
    for root in [master, *layouts]:
        for shape in _shapes(root):
            assert shape.tag == q("p:sp")
            assert shape.find("p:nvSpPr/p:nvPr/p:ph", NS) is not None


@pytest.mark.parametrize(("voice", "mode"), CASES)
def test_placeholders_keep_the_edge_margin(voice, mode, built):
    _, _, master, layouts, _ = parts(built[voice, mode])
    for root in [master, *layouts]:
        for shape in _shapes(root):
            off, ext = shape.find(".//a:off", NS), shape.find(".//a:ext", NS)
            x, y = int(off.get("x")), int(off.get("y"))
            w, h = int(ext.get("cx")), int(ext.get("cy"))
            assert min(x, y, 12192000 - x - w, 6858000 - y - h) >= MARGIN


@pytest.mark.parametrize(("voice", "mode"), CASES)
def test_theme_fonts_and_colours_come_from_the_voice(voice, mode, built):
    v = PACK.voice(voice)
    *_, theme = parts(built[voice, mode])
    th = parse_theme(theme)
    assert (th.major_latin, th.minor_latin) == (v.display, v.text)
    assert {s: th.colors[s] for s in THEME_SLOTS} == {
        s: v.hex(PACK.theme[s]) for s in THEME_SLOTS
    }  # the plan's role mapping, dk1 = ink even when ink is light (Q-33)
    assert th.colors["hlink"] == v.hex("ink")


@pytest.mark.parametrize(("voice", "mode"), CASES)
def test_layout_names_and_every_role(voice, mode, built):
    *_, layouts, _ = parts(built[voice, mode])
    names = [_name(layout) for layout in layouts]
    assert names == list(PACK.regions)
    assert {parse_role(n)[0] for n in names} == set(ROLES)


@pytest.mark.parametrize(("voice", "mode"), CASES)
def test_placeholder_styles_carry_the_pack_scale_and_voice(voice, mode, built):
    v = PACK.voice(voice)
    *_, layouts, _ = parts(built[voice, mode])
    styles = PACK.styles[mode]
    region_of = {idx: region for region, idx in PACK.placeholder_idx.items()}
    for layout in layouts:
        name = _name(layout)
        role = PACK.layout_role(name)
        for shape in _shapes(layout):
            ph = shape.find("p:nvSpPr/p:nvPr/p:ph", NS)
            if ph.get("type") == "title":
                style = styles[role.title]
            else:
                style = styles[PACK.placeholder_styles[name][region_of[int(ph.get("idx"))]]]
            ppr = _ppr(shape)
            assert _sz(ppr) == style.size_hundredths, (name, style.name)
            assert _colour(ppr) == v.hex(style.color[role.surface]), (name, style.name)
            want = "+mj-lt" if style.font == "display" else "+mn-lt"  # Q-27
            assert _typeface(ppr) == want, (name, style.name)


@pytest.mark.parametrize(("voice", "mode"), CASES)
def test_section_placeholders_are_paper_and_accent_on_ink(voice, mode, built):
    v = PACK.voice(voice)
    *_, layouts, _ = parts(built[voice, mode])
    (section,) = [x for x in layouts if _name(x) == "keyline:section"]
    colours = {_colour(_ppr(s)) for s in _shapes(section)}
    assert colours == {v.hex("paper"), v.hex("accent_on_ink")}


@pytest.mark.parametrize(("voice", "mode"), CASES)
def test_txstyles_and_default_text_style_carry_the_mode_sizes(voice, mode, built):
    _, pres, master, _, _ = parts(built[voice, mode])
    styles = PACK.styles[mode]
    tx = master.find("p:txStyles", NS)
    title = tx.find("p:titleStyle/a:lvl1pPr", NS)
    assert _sz(title) == styles["headline"].size_hundredths and _typeface(title) == "+mj-lt"
    for path in ("p:bodyStyle/a:lvl1pPr", "p:otherStyle/a:lvl1pPr"):
        assert _sz(tx.find(path, NS)) == styles["body"].size_hundredths
        assert _typeface(tx.find(path, NS)) == "+mn-lt"
    assert _sz(pres.find("p:defaultTextStyle/a:lvl1pPr", NS)) == styles["body"].size_hundredths
    for level in range(1, 10):  # every level resolves, so no adapter-unresolved
        assert tx.find(f"p:bodyStyle/a:lvl{level}pPr/a:defRPr", NS) is not None


@pytest.mark.parametrize(("voice", "mode"), CASES)
def test_python_pptx_round_trip_lints_on_scale_and_voice(voice, mode, built, tmp_path):
    pptx = pytest.importorskip("pptx")
    from keyline.ooxml.adapter import load_deck

    v = PACK.voice(voice)
    prs = pptx.Presentation(str(built[voice, mode]))
    for layout in prs.slide_layouts:
        slide = prs.slides.add_slide(layout)
        for ph in slide.placeholders:
            ph.text_frame.text = "Keepers wait a season"
    out = tmp_path / f"{voice}-{mode}.pptx"
    prs.save(out)
    deck, diags = load_deck(out)
    assert diags == []
    runs = [r for s in deck.slides for sh in s.shapes for r in sh.runs if r.has_ink]
    assert {r.size for r in runs} <= PACK.scale(mode)
    assert {r.font for r in runs} == set(v.fonts)
    assert {r.color for r in runs} <= set(v.palette.values())
    assert {s.background_rgb for s in deck.slides} == {v.hex("paper"), v.hex("ink")}
    assert [s.role for s in deck.slides] == [parse_role(n)[0] for n in PACK.regions]


@pytest.mark.officecli
@pytest.mark.parametrize(("voice", "mode"), CASES)
def test_officecli_validate(voice, mode, built):
    path = built[voice, mode]
    proc = subprocess.run(["officecli", "validate", str(path)], capture_output=True, text=True)
    assert proc.returncode == 0 and "Validation passed" in proc.stdout, proc.stdout
