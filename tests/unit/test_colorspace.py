"""Spec 002 §3.3 test anchors (auditor's computation; within ±0.02)."""

import pytest

from keyline.colorspace import hsl, lab

LAB = {
    "F2F2F0": (95.44, 1.02, 110.10),
    "f4f3ee": (95.79, 2.58, 102.06),
    "FAF9F5": (97.90, 2.06, 100.17),
    "F5F5DC": (95.95, 12.76, 109.19),
    "EFF1F5": (95.10, 2.16, 271.43),
}
HUE = {"F2F2F0": 60.00, "CC3322": 6.00, "c96442": 15.11, "D20F39": 347.08}


@pytest.mark.parametrize(("colour", "expected"), LAB.items())
def test_cielab_anchors(colour, expected):
    for got, want in zip(lab(colour), expected, strict=True):
        assert abs(got - want) <= 0.02, (colour, lab(colour))


@pytest.mark.parametrize(("colour", "expected"), HUE.items())
def test_hsl_hue_anchors(colour, expected):
    assert abs(hsl(colour)[0] - expected) <= 0.02


def test_hsl_saturation_cannot_judge_paper():
    # L-011: keyline paper has S = 7.1 % in HSL although it is neutral (C* 1.02)
    assert abs(hsl("F2F2F0")[1] - 0.071) < 0.001


def test_bad_input():
    with pytest.raises(ValueError):
        lab("FFF")
