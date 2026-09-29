"""Spec 002 AC-9 (pack part): pack.toml validates, and every §5.4 invariant holds for both
modes. Under B-8.7, invariants 1, 2, 3 and 7 are checked on the system, 4 (contrast) and 6
(fonts) per voice, and 5 (neutral paper, no terracotta) on the neutral voice only; every
other voice is covered by voice-claude-look. The template part is test_ac09_templates.py."""

import pytest

from keyline.colorspace import hsl, lab
from keyline.config import load as load_cfg
from keyline.packs import resolve
from keyline.packs.voices import claude_look, contrast_pairs, low_contrast
from keyline.rules.claude_look_palette import is_cream, is_terracotta
from keyline.rules.font_count import family
from keyline.rules.text_contrast import contrast

PACK = resolve("swiss")
VOICES = {name: PACK.voice(name) for name in PACK.voices()}
NOT_BODY = {"label", "numeral", "source"}  # the pen writes each as its own capped shape
MODES = ("presented", "read")

# B-8.10, normative values and the auditor's checks: contrast ratios, then the paper's
# CIELAB L*, C*, h and the accent's HSL hue.
STOCK = {
    "neutral": (
        ("Arial", "Arial"),
        ("F2F2F0", "111111", "5C5C5A", "B8B8B4", "CC3322", "E8422E"),
        (16.85, 5.98, 4.61, 16.85, 4.72),
        (95.4, 1.02, 110, 6),
    ),
    "night": (
        ("Arial", "Arial"),
        ("16181B", "ECECE8", "A3A7AC", "3D4148", "F0B429", "8A5A00"),
        (15.02, 7.35, 9.54, 15.02, 5.00),
        (8.2, 2.44, 267, 42),
    ),
    "field": (
        ("Georgia", "Georgia"),
        ("EEF2EE", "16251D", "4A5A51", "B6C2BA", "1D4FB8", "8DB2FF"),
        (14.11, 6.47, 6.49, 14.11, 7.55),
        (95.1, 2.51, 144, 221),
    ),
}
ROLES = ("paper", "ink", "muted", "hairline", "accent", "accent_on_ink")
PAIRS = (("ink", "paper"), ("muted", "paper"), ("accent", "paper"), ("paper", "ink"))
PAIRS += (("accent_on_ink", "ink"),)


def body_styles(mode):
    return {n: s for n, s in PACK.styles[mode].items() if n not in NOT_BODY}


def test_the_three_stock_voices_ship():
    assert sorted(VOICES) == sorted(STOCK)


@pytest.mark.parametrize("name", sorted(STOCK))
def test_stock_voice_values_and_checks(name):
    fonts, values, ratios, (paper_l, paper_c, paper_h, accent_h) = STOCK[name]
    v = VOICES[name]
    assert (v.display, v.text) == fonts
    assert tuple(v.hex(r) for r in ROLES) == values
    got = tuple(round(contrast(v.hex(a), v.hex(b)), 2) for a, b in PAIRS)
    assert got == ratios
    lightness, chroma, hue = lab(v.hex("paper"))
    assert (round(lightness, 1), round(chroma, 2), round(hue)) == (paper_l, paper_c, paper_h)
    assert round(hsl(v.hex("accent"))[0]) == accent_h


@pytest.mark.parametrize("mode", MODES)
def test_1_hierarchy(mode):
    cfg = load_cfg(mode)
    for role in PACK.roles.values():
        title = PACK.styles[mode][role.title]
        allowed = {s for styles in role.components[mode].values() for s in styles}
        for name in allowed - NOT_BODY:
            body = PACK.styles[mode][name]
            assert title.size_pt >= cfg.title_ratio_min * body.size_pt, (role.name, name)


@pytest.mark.parametrize("mode", MODES)
def test_2_body_floor(mode):
    cfg = load_cfg(mode)
    for name, style in body_styles(mode).items():
        assert style.size_pt >= cfg.body_min_pt, name


@pytest.mark.parametrize("mode", MODES)
def test_3_source_floor(mode):
    assert PACK.styles[mode]["source"].size_pt >= load_cfg(mode).source_min_pt


@pytest.mark.parametrize("name", sorted(STOCK))
@pytest.mark.parametrize("mode", MODES)
def test_4_contrast_normal_everywhere(mode, name):
    need = float(load_cfg(mode).contrast_normal)
    v = VOICES[name]
    for role in PACK.roles.values():
        surface = PACK.surfaces[role.surface]
        paper = v.hex(surface.background)
        used = {role.title} | {s for styles in role.components[mode].values() for s in styles}
        for style in used:
            text = v.hex(PACK.styles[mode][style].color[role.surface])
            assert contrast(text, paper) >= need, (role.name, style, text, paper)
        if "figure" in role.components[mode]:  # figure(accent=True) uses the surface accent
            assert contrast(v.hex(surface.accent), paper) >= need, role.name
    # the same pairs, as voice-contrast sees them (plan Q-28)
    assert len(contrast_pairs(PACK, v)) == 5 and low_contrast(PACK, v, load_cfg(mode)) == []


def test_5_neutral_paper_and_no_terracotta():
    cfg = load_cfg()
    v = VOICES["neutral"]
    assert lab(v.hex("paper"))[1] <= cfg.neutral_chroma_max
    for role, value in v.palette.items():
        assert not is_terracotta(value, cfg), role


@pytest.mark.parametrize("name", sorted(STOCK))
def test_5b_no_stock_voice_trips_voice_claude_look(name):
    look = claude_look(VOICES[name], load_cfg())
    assert not look.cream_paper and look.terracotta == ()


def test_night_ink_is_in_the_cream_band():
    """Plan Q-34: pinned, not a finding. voice-claude-look tests paper only."""
    assert is_cream(VOICES["night"].hex("ink"), load_cfg())


@pytest.mark.parametrize("name", sorted(STOCK))
def test_6_font_families(name):
    families = {family(f) for f in VOICES[name].fonts}
    assert len(families) <= load_cfg().as_int("font_family_max")


@pytest.mark.parametrize("mode", MODES)
def test_7_numerals_are_kpi_sized(mode):
    assert PACK.styles[mode]["numeral"].size_pt >= load_cfg(mode).kpi_numeral_min_pt


@pytest.mark.parametrize("mode", MODES)
def test_every_role_has_a_layout_and_title_style(mode):
    for role in PACK.roles.values():
        assert role.layouts and role.title in PACK.styles[mode]


def test_evidence_layouts_offer_an_8_column_figure_region():
    for layout in PACK.roles["evidence"].layouts:
        widest = max(r.span for n, r in PACK.regions[layout].items() if n != "title")
        assert widest >= 8, layout


def test_packs_command_lists_voices():
    """Plan Q-39."""
    import json

    from tests.acceptance._cli import keyline

    proc = keyline("packs", "--json")
    assert proc.returncode == 0
    (swiss,) = json.loads(proc.stdout)
    assert [(v["name"], v["display"], v["text"]) for v in swiss["voices"]] == [
        ("field", "Georgia", "Georgia"),
        ("neutral", "Arial", "Arial"),
        ("night", "Arial", "Arial"),
    ]
    human = keyline("packs").stdout.decode()
    assert human == "swiss  1.0.0  presented, read  voices: field, neutral, night\n"
