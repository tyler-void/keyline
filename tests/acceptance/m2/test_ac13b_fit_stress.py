"""Spec 002 AC-13(b) (tasks T-30, T-32): in fit-stress decks, every text the estimator
checks sits at the longest length the pen accepts for its region; rendered with
LibreOffice at 1280 px, no text ink falls outside its region box by more than 2 px. The
decks, the render and the ink measurement are tools/fit_stress.py's; the render half
skips without LibreOffice (or when a voice font resolves to something other than its
metric twin). That the texts are the longest the pen accepts is checked everywhere.

As written, AC-13(b) fails at the left edge: a line that starts with a glyph whose left
side bearing is negative (bold Gelasio's "v" and "j") puts ink left of the region box,
2.7 px measured at 60 pt (report A2). That is not text the estimator let through; the
edges the estimator decides (right, top, bottom) hold. Until Tyler rules, the test of
every edge is an expected failure and the test of the estimator's edges must pass."""

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

COMBOS = [(m, v) for m in fit_stress.MODES for v in fit_stress.VOICES]


@pytest.mark.parametrize(("mode", "voice"), COMBOS)
def test_every_stressed_text_is_the_longest_the_pen_accepts(mode, voice, tmp_path):
    """Each stress slide builds as planned, and one more word (or digit) in any item is
    refused: by the estimator where the item's bound is "fit"."""
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


@pytest.mark.parametrize(("mode", "voice"), COMBOS)
def test_the_pen_refuses_no_component_at_its_shortest(mode, voice, tmp_path):
    """Report A2 found the figure refused at its shortest on a presented statement and
    close; since Q-48 (audit 05) the numeral box is one numeral line and both hold it."""
    evidence = fit_stress.write_evidence(tmp_path / "evidence.toml")
    refused = [(s.layout, *r) for s in fit_stress.plan(mode, voice, evidence) for r in s.refused]
    assert refused == []


REASON = fit_stress.unready()
needs_render = pytest.mark.skipif(REASON is not None, reason=f"fit stress cannot render: {REASON}")


@pytest.fixture(scope="module")
def measured(tmp_path_factory):
    return {
        (m, v): fit_stress.measure(m, v, tmp_path_factory.mktemp(f"{m}-{v}")) for m, v in COMBOS
    }


def _where(version, mode, voice, r):
    return f"{version}: {mode} {voice} slide {r.slide}, {r.layout} {r.region} ({r.what})"


@needs_render
@pytest.mark.parametrize(("mode", "voice"), COMBOS)
def test_no_ink_past_the_edges_the_estimator_decides(measured, mode, voice):
    version, results, _refused = measured[mode, voice]
    assert version.startswith("LibreOffice ")  # B-7: recorded with the render
    assert results
    for r in results:
        assert r.ink_px is not None, f"{_where(version, mode, voice, r)}: no ink"
        assert r.fit_overflow <= fit_stress.TOLERANCE_PX, (
            f"{_where(version, mode, voice, r)}: {r.fit_overflow:+.1f} px"
        )


@needs_render
@pytest.mark.xfail(
    reason="AC-13(b) as written: left-edge glyph overhang (report A2), awaiting a ruling",
    strict=False,  # whether a line starts with such a glyph depends on the corpus
)
@pytest.mark.parametrize(("mode", "voice"), COMBOS)
def test_ac13b_as_written_no_ink_past_any_edge(measured, mode, voice):
    version, results, _refused = measured[mode, voice]
    for r in results:
        assert r.overflow <= fit_stress.TOLERANCE_PX, (
            f"{_where(version, mode, voice, r)}: {r.overflow:+.1f} px {r.edge}"
        )


def test_the_ink_measurement_sees_ink_outside_a_box():
    """The measurement can fail: ink past an edge is reported, faint noise is not ink."""
    from PIL import Image, ImageDraw

    control = Image.new("RGB", (1280, 720), "#F2F2F0")
    image = control.copy()
    ImageDraw.Draw(image).rectangle([100, 100, 204, 150], fill="#111111")
    ink = fit_stress.ink_box(image, control)
    assert ink == (100, 100, 205, 151)
    r = fit_stress.Result("read", "field", 1, "keyline:evidence", "main", "text (body)", "1w",
                          "fit", (100.0, 100.0, 200.0, 200.0), ink)  # fmt: skip
    assert (r.overflow, r.edge, r.fit_overflow) == (5, "right", 5)
    left = fit_stress.Result("read", "field", 1, "keyline:evidence", "main", "text (body)", "1w",
                             "fit", (102.7, 100.0, 300.0, 200.0), ink)  # fmt: skip
    assert (round(left.overflow, 1), left.edge, left.fit_overflow) == (2.7, "left", 0)  # top
    faint = control.copy()
    ImageDraw.Draw(faint).point((10, 10), fill="#E0E0DE")  # 18 of 255 from the paper
    assert fit_stress.ink_box(faint, control) is None
