"""The fit estimator (spec 002 §6.4 as amended by B-21; task T-22)."""

from fractions import Fraction as F

import pytest

from keyline.fit import (
    BELOW_BASELINE_EM,
    LINE_ALLOWANCE_PT,
    WRAP_MARGIN,
    DoesNotFit,
    Setting,
    coverage_warning,
    fit,
    load_table,
    missing,
    unmeasured,
    width,
    wrap,
)

ARIAL = Setting("Arial", "regular", F(24))


def test_width_is_the_advance_sum_plus_tracking():
    t = load_table("Arial", "regular")
    assert width(ARIAL, "HH") == F(2 * t.advance("H"), t.units_per_em) * 24
    caps = Setting("Arial", "bold", F(14), caps=True, tracking=F(8, 100))
    tb = load_table("Arial", "bold")
    shown = "ACTIVE"
    expected = F(sum(tb.advance(c) for c in shown), tb.units_per_em) * 14 + F(8, 100) * 14 * 6
    assert width(caps, "active") == expected
    assert width(ARIAL, "\U0010fffd") == t.missing_advance / t.units_per_em * 24


def test_wrap_uses_the_099_margin_exactly():
    text = "Keepers wait a season"
    w = width(ARIAL, text)
    assert wrap(ARIAL, text, w / WRAP_MARGIN) == [text]  # exactly at the margin: fits
    assert len(wrap(ARIAL, text, w / WRAP_MARGIN - F(1, 1000))) == 2


def test_indent_comes_off_the_width():
    text = "Keepers wait a season"
    w = width(ARIAL, text) / WRAP_MARGIN
    indented = Setting("Arial", "regular", F(24), indent=F(27))
    assert len(wrap(indented, text, w)) == 2 and wrap(indented, text, w + 27) == [text]


def test_a_word_wider_than_the_region_does_not_fit():
    with pytest.raises(DoesNotFit, match="the word 'Bonsaihubkeepers' is wider"):
        wrap(ARIAL, "a Bonsaihubkeepers b", F(100))


def test_height_adds_the_allowance_per_line():
    pitch = F(24) * F(6, 5) + LINE_ALLOWANCE_PT
    assert ARIAL.pitch == pitch
    assert F(72, 2540) == LINE_ALLOWANCE_PT
    lines = ["one", "two", "three"]
    held = 3 * pitch + ARIAL.descent_room  # the lines, and room for the last one's descent
    assert fit(ARIAL, lines, F(500), held) == [["one"], ["two"], ["three"]]
    with pytest.raises(DoesNotFit, match=r"^headline needs 3 lines, region holds 2: shorten"):
        fit(ARIAL, lines, F(500), held - F(1, 1000), "headline")


def test_room_for_the_descent_under_the_last_line():
    """LibreOffice's baseline sits 0.2 em above a line's bottom (B-21); a twin's deepest
    descent below that is kept free under a region's last line (A2 fixes, with FX-24)."""
    t = load_table("Arial", "regular")
    assert t.descent_em == F(455, 2048)  # Liberation Sans, over the measured set (Q-51)
    assert ARIAL.descent_room == 24 * (t.descent_em - BELOW_BASELINE_EM)
    gelasio = Setting("Georgia", "bold", F(48))
    assert gelasio.descent_room == 48 * (load_table("Georgia", "bold").descent_em - F(1, 5))
    carlito = Setting("Calibri", "regular", F(24))  # 0.258 em over the measured set (Q-51)
    assert carlito.descent_room == 24 * (load_table("Calibri", "regular").descent_em - F(1, 5))
    lowest = Setting("Calibri", "regular", F(24), caps=True)
    assert lowest.descent_room == carlito.descent_room  # one room per font, whatever the text


def test_paragraph_spacing_counts():
    spaced = Setting("Arial", "regular", F(24), space_after=F(6))
    pitch, room = spaced.pitch, spaced.descent_room
    assert fit(spaced, ["a", "b"], F(500), 2 * pitch + 12 + room)
    with pytest.raises(DoesNotFit, match="needs 2 lines, region holds 1"):
        fit(spaced, ["a", "b"], F(500), 2 * pitch + 11 + room)
    assert fit(spaced, ["a", "b"], F(500), 2 * pitch + 12, descent=False)  # a numeral box


def test_missing_characters_and_the_warning():
    cambria = Setting("Cambria", "regular", F(24))
    assert missing(cambria, "Cây già nhất chờ đợi") == "ấờợ"
    assert missing(Setting("Arial", "regular", F(24)), "Cây già nhất chờ đợi") == ""
    cjk = chr(0x6F22)
    assert unmeasured(f"Cây {cjk} già") == cjk and unmeasured("Cây già nhất") == ""
    assert coverage_warning({"Cambria": "ấờợ"}, cjk) == (
        f"the fit does not cover some characters (B-25): Caladea (for Cambria) lacks: ấờợ; "
        f"outside the measured set: {cjk}; the pen estimated them conservatively but "
        "promises nothing for them, and the check render may set them in another font"
    )
    assert coverage_warning({"Cambria": ""}, "") is None


def test_a_long_fit_reads_the_config_once(monkeypatch):
    """load_table answers from its cache before it reads the config (T-30: the stress
    planner spent most of its time re-parsing thresholds.toml once per width)."""
    import keyline.config as config_mod
    import keyline.fit as fit_mod

    monkeypatch.setattr(fit_mod, "_cache", {})
    calls = []
    real = config_mod.load
    monkeypatch.setattr(config_mod, "load", lambda *a, **k: calls.append(1) or real(*a, **k))
    fit(ARIAL, ["keepers wait a season " * 40], F(800), F(1000), "text")
    assert len(calls) == 1
    with pytest.raises(Exception, match="not a portable font"):
        load_table("Comic Sans MS", "regular")
