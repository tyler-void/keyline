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


# spec 002 §3.2 (T-04)


def test_spec_002_per_mode_keys():
    p, r = load("presented"), load("read")
    assert (p.as_int("title_words_max"), r.as_int("title_words_max")) == (10, 15)
    assert (p.source_min_pt, r.source_min_pt) == (12, 9)
    assert (p.as_int("reads_max"), r.as_int("reads_max")) == (3, 5)
    assert (p.as_int("bullets_max"), r.as_int("bullets_max")) == (4, 6)
    assert (p.as_int("numerals_max"), r.as_int("numerals_max")) == (1, 2)


def test_spec_002_common_numbers():
    c = load()
    assert c.neutral_chroma_max == Fraction(3, 2)
    assert (c.cream_lightness_min, c.cream_chroma_max) == (88, 20)
    assert (c.cream_hue_min, c.cream_hue_max, c.cream_slide_ratio) == (60, 115, Fraction(1, 2))
    assert (c.terracotta_hue_min, c.terracotta_hue_max) == (10, 25)
    assert (c.terracotta_sat_min, c.terracotta_sat_max) == (Fraction(7, 20), Fraction(9, 10))
    assert (c.terracotta_light_min, c.terracotta_light_max) == (Fraction(7, 20), Fraction(7, 10))
    assert c.as_int("statement_min_slides") == 6


def test_list_keys_are_nfc_casefolded_tuples():
    c = load()
    assert c.source_prefixes == ("source", "sources", "nguồn")
    assert c.note_prefixes == ("note", "notes", "ghi chú")
    assert "q&a" in c.closing_cliches and "cảm ơn đã lắng nghe" in c.closing_cliches
    assert len(c.closing_cliches) == 14 and len(c.mood_words) == 16
    cfg = parse(
        {"calibrated": False, "common": {**_minimal_common(), "note_prefixes": ["Ghi Chú"]}},
        "read",
    )
    assert cfg.note_prefixes == ("ghi chú",)


def test_list_and_number_types_are_enforced():
    with pytest.raises(ConfigError, match="list of non-empty strings"):
        parse({"calibrated": False, "common": {"mood_words": "clean"}}, "read")
    with pytest.raises(ConfigError, match="list of non-empty strings"):
        parse({"calibrated": False, "common": {"mood_words": ["clean", 3]}}, "read")
    with pytest.raises(ConfigError, match="must be a number"):
        parse({"calibrated": False, "read": {"reads_max": ["5"]}}, "read")


def test_portable_fonts_are_family_and_twin_pairs():
    """B-8.3: six families, each with its open metric-compatible twin (plan Q-38)."""
    assert load().portable_fonts == (
        ("Arial", "Liberation Sans"),
        ("Times New Roman", "Liberation Serif"),
        ("Courier New", "Liberation Mono"),
        ("Georgia", "Gelasio"),
        ("Calibri", "Carlito"),
        ("Cambria", "Caladea"),
    )
    for bad in (
        ["Arial"],
        [{"family": "Arial"}],
        [{"family": "Arial", "metric_twin": ""}],
        [{"family": "Arial", "metric_twin": "Arimo", "note": "x"}],
    ):
        with pytest.raises(ConfigError, match="family, metric_twin"):
            parse({"calibrated": False, "common": {"portable_fonts": bad}}, "read")
    twice = [{"family": f, "metric_twin": "Arimo"} for f in ("Arial", "arial")]
    with pytest.raises(ConfigError, match="lists a family twice"):
        parse({"calibrated": False, "common": {"portable_fonts": twice}}, "read")


def _minimal_common():
    """Every key of the shipped file, so a test can override one."""
    import tomllib
    from importlib import resources

    data = tomllib.loads(resources.files("keyline").joinpath("thresholds.toml").read_text())
    return {**data["common"], **data["read"]}
