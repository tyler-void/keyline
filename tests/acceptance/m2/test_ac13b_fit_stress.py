"""Spec 002 AC-13(b) as amended by B-24 (tasks T-30, T-32, the A2 fixes): in fit-stress
decks for each of the six portable families (test-only voices) in both modes, every text
the estimator checks sits at the longest length the pen accepts for its region; rendered
with LibreOffice at 1280 px, no text ink falls outside its region box by more than 2 px on
the right, top or bottom, nor on the left by more than 2 px plus its left allowance (the
most negative left side bearing among its characters × size, from the twin, fontTools).
The decks, the render and the measurement are tools/fit_stress.py's; the render half
skips without LibreOffice (or when a family resolves to something other than its metric
twin). That the texts are the longest the pen accepts is checked everywhere."""

import importlib.util
import sys

import pytest

from tests.conftest import ROOT

pytest.importorskip("pptx")

_spec = importlib.util.spec_from_file_location("fit_stress", ROOT / "tools" / "fit_stress.py")
fit_stress = importlib.util.module_from_spec(_spec)
sys.modules["fit_stress"] = fit_stress  # its dataclasses look their module up
_spec.loader.exec_module(fit_stress)

from keyline.pen import Deck  # noqa: E402

COMBOS = [(m, f) for m in fit_stress.MODES for f in fit_stress.FAMILIES]


@pytest.mark.parametrize(("mode", "family"), COMBOS)
def test_every_stressed_text_is_the_longest_the_pen_accepts(mode, family, tmp_path):
    """Each stress slide builds as planned, and one more word (or digit) in any item is
    refused: by the estimator where the item's bound is "fit"."""
    voice = fit_stress.voice_file(tmp_path, family)
    evidence = fit_stress.write_evidence(tmp_path / "evidence.toml")
    scratch = Deck(fit_stress.PACK, mode, voice, evidence=str(evidence))
    for s in fit_stress.plan(mode, voice, evidence):
        built = scratch.add(s.role, s.headline.texts[0], variant=s.variant)
        for region, fill in s.fills.items():
            fit_stress.apply(built, region, fill)
        for region, fill in [("title", s.headline), *s.fills.items()]:
            assert len(fill.bounds) == len(fill.counts)
            for i, bound in enumerate(fill.bounds):
                why = fit_stress.refusal(scratch, s, region, fill.longer(i))
                assert why is not None and why.split(":")[0] == bound, (s.layout, region, i)


@pytest.mark.parametrize(("mode", "family"), COMBOS)
def test_the_pen_refuses_no_component_at_its_shortest(mode, family, tmp_path):
    """Report A2 found the figure refused at its shortest on a presented statement and
    close; since Q-48 (audit 05) the numeral box is one numeral line and both hold it."""
    voice = fit_stress.voice_file(tmp_path, family)
    evidence = fit_stress.write_evidence(tmp_path / "evidence.toml")
    refused = [(s.layout, *r) for s in fit_stress.plan(mode, voice, evidence) for r in s.refused]
    assert refused == []


@pytest.mark.skipif(
    fit_stress.fc_family("Georgia") != "Gelasio", reason="Georgia does not resolve to Gelasio"
)
def test_the_left_allowance():
    """Bold Gelasio's "v" (left side bearing -49/2048 em) at 60 pt: 1.9 px at 1280 px."""
    pack = fit_stress.resolve(fit_stress.PACK)
    field = pack.voice("field")
    stress = fit_stress.Stress("statement", "keyline:statement", None)
    fill = fit_stress.Fill("headline", (1,), 0)
    words = dict(zip(fit_stress.WORDS, range(len(fit_stress.WORDS)), strict=False))
    visitors = fit_stress.replace(fill, start=words["visitors"])
    assert visitors.texts == ["visitors"]
    bearings, upm = fit_stress.left_bearings("Georgia", "bold")
    expected = -min(bearings[ord(c)] for c in "visitors") / upm * 60 * 1280 / 960
    assert fit_stress.left_allowance(pack, "presented", field, stress, visitors) == expected
    assert round(expected, 1) == 1.9


REASON = fit_stress.unready()
needs_render = pytest.mark.skipif(REASON is not None, reason=f"fit stress cannot render: {REASON}")


@pytest.fixture(scope="module")
def measured(tmp_path_factory):
    work = tmp_path_factory.mktemp("stress")
    return {(m, f): fit_stress.measure(m, f, work) for m, f in COMBOS}


@needs_render
@pytest.mark.parametrize(("mode", "family"), COMBOS)
def test_no_ink_past_its_limits(measured, mode, family):
    version, results, refused = measured[mode, family]
    assert version.startswith("LibreOffice ")  # B-7: recorded with the render
    assert results and refused == []
    for r in results:
        where = f"{version}: {mode} {family} slide {r.slide}, {r.layout} {r.region} ({r.what})"
        assert r.ink_px is not None, f"{where}: no ink"
        assert r.excess <= 0, f"{where}: {r.excess:+.1f} px past the {r.excess_edge} limit"


def test_the_ink_measurement_sees_ink_outside_a_box():
    """The measurement can fail: ink past an edge is reported, faint noise is not ink, and
    the left edge's limit moves by the left allowance only."""
    from PIL import Image, ImageDraw

    control = Image.new("RGB", (1280, 720), "#F2F2F0")
    image = control.copy()
    ImageDraw.Draw(image).rectangle([100, 100, 204, 150], fill="#111111")
    ink = fit_stress.ink_box(image, control)
    assert ink == (100, 100, 205, 151)
    r = fit_stress.Result("read", "Georgia", 1, "keyline:evidence", "main", "text (body)", "1w",
                          "fit", (100.0, 100.0, 200.0, 200.0), ink)  # fmt: skip
    assert (r.overflow, r.edge, r.excess, r.excess_edge) == (5, "right", 3, "right")
    left = fit_stress.Result("read", "Georgia", 1, "keyline:evidence", "main", "text (body)",
                             "1w", "fit", (104.0, 100.0, 300.0, 200.0), ink, 1.5)  # fmt: skip
    assert (left.edges["left"], left.excess, left.excess_edge) == (4.0, 0.5, "left")
    faint = control.copy()
    ImageDraw.Draw(faint).point((10, 10), fill="#E0E0DE")  # 18 of 255 from the paper
    assert fit_stress.ink_box(faint, control) is None
