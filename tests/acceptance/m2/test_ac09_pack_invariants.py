"""Spec 002 AC-9 (pack part): pack.toml validates, and every §5.4 invariant holds for both
modes. The template part is test_ac09_templates.py (T-09)."""

import pytest

from keyline.colorspace import lab
from keyline.config import load as load_cfg
from keyline.packs import resolve
from keyline.rules.claude_look_palette import is_terracotta
from keyline.rules.font_count import family
from keyline.rules.text_contrast import contrast

PACK = resolve("swiss")
NOT_BODY = {"label", "numeral", "source"}  # the pen writes each as its own capped shape
MODES = ("presented", "read")


def body_styles(mode):
    return {n: s for n, s in PACK.styles[mode].items() if n not in NOT_BODY}


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


@pytest.mark.parametrize("mode", MODES)
def test_4_contrast_normal_everywhere(mode):
    need = float(load_cfg(mode).contrast_normal)
    for role in PACK.roles.values():
        surface = PACK.surfaces[role.surface]
        paper = PACK.hex(surface.background)
        used = {role.title} | {s for styles in role.components[mode].values() for s in styles}
        for name in used:
            text = PACK.hex(PACK.styles[mode][name].color[role.surface])
            assert contrast(text, paper) >= need, (role.name, name, text, paper)
        if "figure" in role.components[mode]:  # figure(accent=True) uses the surface accent
            assert contrast(PACK.hex(surface.accent), paper) >= need, role.name


def test_5_neutral_paper_and_no_terracotta():
    cfg = load_cfg()
    assert lab(PACK.hex("paper"))[1] <= cfg.neutral_chroma_max
    for name, value in PACK.palette.items():
        assert not is_terracotta(value, cfg), name


def test_6_font_families():
    assert len({family(f) for f in PACK.fonts}) <= load_cfg().as_int("font_family_max")


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
