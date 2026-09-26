from fractions import Fraction

import pytest

from keyline.config import KEYS, ConfigError, load, parse


def test_spec_table_values():
    p = load("presented")
    r = load("read")
    assert p.calibrated is False
    assert (p.body_min_pt, r.body_min_pt) == (18, 11)
    assert (p.title_ratio_min, r.title_ratio_min) == (2, Fraction(8, 5))
    for c in (p, r):
        assert c.caption_exempt_words == 5
        assert c.edge_margin_cm == Fraction(127, 100)
        assert c.edge_margin_tolerance_cm == Fraction(1, 20)
        assert c.dead_band_ratio == Fraction(1, 4)
        assert (c.contrast_normal, c.contrast_large) == (Fraction(9, 2), 3)
        assert (c.large_text_pt, c.large_text_bold_pt) == (18, 14)
        assert c.as_int("font_family_max") == 2


def test_every_key_present_in_both_modes():
    for mode in ("presented", "read"):
        assert set(load(mode).values) == set(KEYS)


def test_default_is_presented():
    assert load().mode == "presented"


def test_rejects_unknown_mode_and_keys():
    with pytest.raises(ConfigError):
        load("slides")
    with pytest.raises(ConfigError, match="unknown key"):
        parse({"calibrated": False, "common": {"nope": 1}}, "read")
    with pytest.raises(ConfigError, match="missing keys"):
        parse({"calibrated": False, "read": {"body_min_pt": 11}}, "read")
    with pytest.raises(ConfigError, match="must be a number"):
        parse({"calibrated": False, "common": {"body_min_pt": "11"}}, "read")
