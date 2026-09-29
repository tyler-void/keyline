"""Spec 002 AC-13(b) (task T-30): in fit-stress decks, every text sits at the longest
length the pen accepts for its region; rendered with LibreOffice at 1280 px, no text ink
falls outside its region box by more than 2 px. The decks, the render and the ink
measurement are tools/fit_stress.py's; the render half skips without LibreOffice (or when
a voice font resolves to something other than its metric twin). That the texts are the
longest the pen accepts is checked everywhere."""

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
def test_every_stressed_text_is_the_longest_the_pen_accepts(mode, voice):
    """Each stress slide builds as planned, and one more word of the corpus in any item
    (a headline, a text, a bullet, the source or the note line) raises DoesNotFit."""
    scratch = Deck(fit_stress.PACK, mode, voice)
    for s in fit_stress.plan(mode, voice):
        built = scratch.add(s.role, s.headline.texts[0], variant=s.variant)
        for region, fill in s.fills.items():
            fit_stress.apply(built, region, fill)
        for region, fill in [("title", s.headline), *s.fills.items()]:
            for i in range(len(fill.counts)):
                longer = fill.longer(i)
                assert not fit_stress.fits(scratch, s, region, longer), (s.layout, region, i)


REASON = fit_stress.unready()


@pytest.fixture(scope="module")
def measured(tmp_path_factory):
    return {
        (m, v): fit_stress.measure(m, v, tmp_path_factory.mktemp(f"{m}-{v}")) for m, v in COMBOS
    }


@pytest.mark.skipif(REASON is not None, reason=f"fit stress cannot render: {REASON}")
@pytest.mark.parametrize(("mode", "voice"), COMBOS)
def test_no_text_ink_falls_outside_its_region(measured, mode, voice):
    version, results = measured[mode, voice]
    assert version.startswith("LibreOffice ")  # B-7: recorded with the render
    assert results
    for r in results:
        where = f"{version}: {mode} {voice} slide {r.slide}, {r.layout} {r.region} ({r.what})"
        assert r.ink_px is not None, f"{where}: no ink"
        assert r.overflow <= fit_stress.TOLERANCE_PX, f"{where}: {r.overflow:+.1f} px {r.edge}"


def test_the_ink_measurement_sees_ink_outside_a_box():
    """The measurement can fail: ink past an edge is reported, faint noise is not ink."""
    from PIL import Image, ImageDraw

    control = Image.new("RGB", (1280, 720), "#F2F2F0")
    image = control.copy()
    ImageDraw.Draw(image).rectangle([100, 100, 204, 150], fill="#111111")
    ink = fit_stress.ink_box(image, control)
    assert ink == (100, 100, 205, 151)
    r = fit_stress.Result("read", "field", 1, "keyline:evidence", "main", "text (body)", 1,
                          (100.0, 100.0, 200.0, 200.0), ink)  # fmt: skip
    assert (r.overflow, r.edge) == (5, "right")
    faint = control.copy()
    ImageDraw.Draw(faint).point((10, 10), fill="#E0E0DE")  # 18 of 255 from the paper
    assert fit_stress.ink_box(faint, control) is None
