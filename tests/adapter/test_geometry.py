from fractions import Fraction

import pytest
from lxml import etree

from keyline.geom import Box
from keyline.ooxml.geometry import Placement, Xfrm, apply_group, parse_xfrm
from keyline.ooxml.placeholders import Ph, match_layout, match_master, ph_of

A = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
P = 'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'


def test_parse_xfrm():
    el = etree.fromstring(
        f'<a:xfrm {A} rot="5400000" flipH="1"><a:off x="1" y="2"/><a:ext cx="3" cy="4"/>'
        '<a:chOff x="5" y="6"/><a:chExt cx="7" cy="8"/></a:xfrm>'
    )
    assert parse_xfrm(el) == Xfrm(1, 2, 3, 4, 5400000, True, False, 5, 6, 7, 8)
    assert parse_xfrm(etree.fromstring(f'<a:xfrm {A}><a:off x="1" y="2"/></a:xfrm>')) is None
    assert parse_xfrm(None) is None


def leaf(x, y, w, h, rot=0):
    return Placement.from_xfrm(Xfrm(x, y, w, h, rot))


def test_group_scale_and_offset():
    g = Xfrm(1000, 1000, 500, 500, ch_x=0, ch_y=0, ch_cx=1000, ch_cy=1000)
    p = apply_group(leaf(200, 400, 100, 200), g)
    assert p.rect() == (1100, 1200, 50, 100)


def test_nested_groups_compose_inner_first():
    outer = Xfrm(360000, 360000, 3600000, 1800000, ch_x=0, ch_y=0, ch_cx=7200000, ch_cy=3600000)
    inner = Xfrm(720000, 720000, 1440000, 720000, ch_x=100, ch_y=100, ch_cx=720000, ch_cy=360000)
    p = apply_group(apply_group(leaf(100, 100, 360000, 180000), inner), outer)
    # inner: scale 2, child (100,100) -> (720000, 720000); outer: scale 0.5 then +360000
    assert p.rect() == (720000, 720000, 360000, 180000)


def test_zero_child_extent_means_scale_one():
    p = apply_group(leaf(10, 10, 5, 5), Xfrm(100, 100, 50, 50))
    assert p.rect() == (110, 110, 5, 5)


def test_group_rotation_90_moves_center_and_adds_rotation():
    g = Xfrm(0, 0, 400, 200, rot=90 * 60000, ch_cx=400, ch_cy=200)
    p = apply_group(leaf(0, 0, 100, 50), g)  # child center (50, 25); group center (200, 100)
    # rotate (-150, -75) clockwise by 90° in y-down space -> (75, -150)
    assert (p.cx, p.cy) == (Fraction(275), Fraction(-50))
    assert p.rot == 90 * 60000
    assert p.box() == Box(250, -100, 50, 100)


def test_group_flip_mirrors_center():
    g = Xfrm(0, 0, 400, 200, flip_h=True, ch_cx=400, ch_cy=200)
    p = apply_group(leaf(0, 0, 100, 50, rot=30 * 60000), g)
    assert (p.cx, p.cy) == (Fraction(350), Fraction(25))
    assert p.rot == 330 * 60000


def ph_sp(sid, name, ph_attrs):
    return (
        f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvSpPr/>'
        f"<p:nvPr><p:ph {ph_attrs}/></p:nvPr></p:nvSpPr></p:sp>"
    )


def part(tag, *shapes):
    body = "".join(shapes)
    return etree.fromstring(
        f"<p:{tag} {P} {A}><p:cSld><p:spTree>{body}</p:spTree></p:cSld></p:{tag}>"
    )


LAYOUT = part(
    "sldLayout",
    ph_sp(2, "Title", 'type="title"'),
    ph_sp(3, "Content", 'idx="1"'),
    ph_sp(4, "Date", 'type="dt" sz="half" idx="10"'),
)
MASTER = part(
    "sldMaster",
    ph_sp(2, "MTitle", 'type="title"'),
    ph_sp(3, "MBody", 'type="body" idx="1"'),
)


def name(el):
    return el.find(".//{*}cNvPr").get("name")


@pytest.mark.parametrize(
    ("ph", "expected"),
    [
        (Ph("title", 0), "Title"),  # idx 0 matches the title
        (Ph("obj", 1), "Content"),  # idx match
        (Ph("body", 1), "Content"),  # idx match wins over type
        (Ph("dt", 99), "Date"),  # no idx match -> same type
    ],
)
def test_match_layout_idx_first_then_type(ph, expected):
    assert name(match_layout(ph, LAYOUT)) == expected


def test_match_layout_none():
    assert match_layout(Ph("pic", 42), LAYOUT) is None


def test_match_master_by_mapped_type():
    assert name(match_master(Ph("ctrTitle", 0), MASTER)) == "MTitle"
    assert name(match_master(Ph("obj", 1), MASTER)) == "MBody"
    assert name(match_master(Ph("subTitle", 1), MASTER)) == "MBody"
    assert match_master(Ph("sldNum", 12), MASTER) is None


def test_ph_defaults():
    sp = etree.fromstring(
        f'<p:sp {P}><p:nvSpPr><p:cNvPr id="1" name="x"/><p:cNvSpPr/><p:nvPr><p:ph/></p:nvPr>'
        "</p:nvSpPr></p:sp>"
    )
    assert ph_of(sp) == Ph("obj", 0)
