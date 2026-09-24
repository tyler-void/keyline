from fractions import Fraction

from keyline.geom import Box, contains, overlap, rotated_aabb, slide_coverage


def test_box_edges():
    b = Box(10, 20, 30, 40)
    assert (b.left, b.top, b.right, b.bottom, b.area) == (10, 20, 40, 60, 1200)


def test_overlap_and_gap():
    assert overlap(Box(0, 0, 10, 10), Box(5, 5, 10, 10)) == (5, 5)
    assert overlap(Box(0, 0, 10, 10), Box(15, 0, 10, 10)) == (-5, 10)


def test_contains_is_edge_inclusive():
    card = Box(540000, 1800000, 3520800, 2520000)
    label = Box(540000, 3240000, 3520800, 324000)  # kpi slide 2: shares both side edges
    assert contains(card, label)
    assert not contains(label, card)


def test_slide_coverage_clips():
    assert slide_coverage(Box(0, 0, 100, 100), 100, 100) == 1
    assert slide_coverage(Box(-50, 0, 100, 100), 100, 100) == Fraction(1, 2)
    assert slide_coverage(Box(200, 0, 10, 10), 100, 100) == 0


def test_rotated_aabb_quarter_turns_exact():
    assert rotated_aabb(0, 0, 100, 40, 0) == Box(0, 0, 100, 40)
    assert rotated_aabb(0, 0, 100, 40, 90 * 60000) == Box(30, -30, 40, 100)
    assert rotated_aabb(0, 0, 100, 40, 180 * 60000) == Box(0, 0, 100, 40)
    assert rotated_aabb(0, 0, 100, 40, -90 * 60000) == Box(30, -30, 40, 100)


def test_rotated_aabb_45():
    b = rotated_aabb(0, 0, 100, 100, 45 * 60000)
    # edges are rounded, not the size: 50 ∓ 70.71 -> -21 and 121
    assert (b.left, b.top, b.right, b.bottom) == (-21, -21, 121, 121)
