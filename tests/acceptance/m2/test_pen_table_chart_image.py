"""Spec 002 §6.1, §6.4 and §6.6 (task T-26): table, chart_bar and image."""

import shutil
import subprocess
import zipfile

import pytest

pytest.importorskip("pptx")

from lxml import etree
from PIL import Image

from keyline.ooxml.adapter import load_deck
from keyline.packs import resolve
from keyline.pen import Deck, DoesNotFit, PenError
from tests.conftest import FIXTURES

EVIDENCE = [str(FIXTURES / "briefs/evidence.toml"), str(FIXTURES / "briefs/extra-evidence.toml")]
PACK = resolve("swiss")
MAIN = PACK.region_box("keyline:evidence", "main")
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
C = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"


def evidence_slide(mode="presented"):
    d = Deck(pack="swiss", mode=mode, voice="neutral", evidence=EVIDENCE)
    return d, d.add("evidence", "What members borrow most", notes="n")


def _part(path, prefix):
    with zipfile.ZipFile(path) as z:
        (name,) = [n for n in z.namelist() if n.startswith(prefix) and n.endswith(".xml")]
        return etree.fromstring(z.read(name))


def test_a_table_has_hairlines_no_fills_and_the_region_box(tmp_path):
    d, s = evidence_slide()
    s.table([["Tool", "Loans"], ["Saw", "120"], ["Clamp", "96"]])
    out = tmp_path / "t.pptx"
    d.save(str(out))
    model, _ = load_deck(out)
    (frame,) = [x for x in model.slides[0].shapes if x.kind == "graphicFrame:table"]
    assert (frame.x, frame.y, frame.w, frame.h) == (MAIN.x, MAIN.y, MAIN.w, MAIN.h)
    assert frame.table_text == "Tool\tLoans\nSaw\t120\nClamp\t96"
    slide = _part(out, "ppt/slides/slide")
    widths = [int(g.get("w")) for g in slide.iter(f"{A}gridCol")]
    assert sum(widths) == MAIN.w
    for tc in slide.iter(f"{A}tc"):
        tc_pr = tc.find(f"{A}tcPr")
        assert tc_pr.find(f"{A}noFill") is not None
        assert tc_pr.find(f"{A}lnB/{A}solidFill/{A}srgbClr").get("val") == "B8B8B4"
        assert tc_pr.find(f"{A}lnL/{A}noFill") is not None
    header = next(slide.iter(f"{A}tc")).find(f".//{A}rPr")
    assert (header.get("sz"), header.get("cap")) == ("1400", "all")  # the label style


@pytest.mark.parametrize(
    ("rows", "error", "message"),
    [
        ([["a", "b"], ["c"]], PenError, "equally long lists"),
        ([["Tool used for the spring repairs", "b"], ["c", "d"]], PenError, "header cell has 6"),
        ([["Tool", "Note"]] + [["Saw", "a long note " * 3]] * 12, DoesNotFit, "table needs"),
    ],
)
def test_table_errors(rows, error, message):
    _d, s = evidence_slide()
    with pytest.raises(error, match=message):
        s.table(rows)


def test_a_chart_with_one_highlight(tmp_path):
    d, s = evidence_slide()
    s.chart_bar("members_by_quarter", highlight="Q3").source()
    out = tmp_path / "c.pptx"
    d.save(str(out))
    chart = _part(out, "ppt/charts/chart")
    assert chart.find(f".//{C}legend") is None
    ids = [int(x.get("val")) for x in chart.iter(f"{C}axId")]
    crosses = [int(x.get("val")) for x in chart.iter(f"{C}crossAx")]
    assert all(0 < i < 2**32 for i in ids + crosses)  # §6.6: positive UInt32
    assert set(crosses) <= set(ids)
    fills = [x.get("val") for x in chart.iter(f"{A}srgbClr")]
    assert "5C5C5A" in fills and "CC3322" in fills  # muted bars, the accent highlight
    assert {x.get("typeface") for x in chart.iter(f"{A}latin")} == {"Arial"}
    assert s._accents == 1


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda s: s.chart_bar("returns_repaired"), "has a value, not a series"),
        (lambda s: s.chart_bar("members_by_quarter", highlight="Q9"), "is not a category"),
    ],
)
def test_chart_errors(call, message):
    _d, s = evidence_slide()
    with pytest.raises(PenError, match=message):
        call(s)


def test_a_highlight_counts_against_the_accent_budget():
    d = Deck(pack="swiss", mode="read", voice="neutral", evidence=EVIDENCE)
    s = d.add("evidence", "Growth", notes="n", variant="figure").figure(
        "returns_repaired", accent=True
    )
    with pytest.raises(PenError, match="would be accent 2"):
        s.chart_bar("members_by_quarter", region="side", highlight="Q3")


@pytest.mark.officecli
def test_a_chart_deck_validates(tmp_path):
    d, s = evidence_slide()
    s.chart_bar("members_by_quarter").source()
    out = tmp_path / "v.pptx"
    d.save(str(out))
    proc = subprocess.run(
        [shutil.which("officecli"), "validate", str(out)], capture_output=True, text=True
    )
    assert "Validation passed" in proc.stdout, proc.stdout


def test_an_image_fits_without_distortion(tmp_path):
    png = tmp_path / "wide.png"
    Image.new("RGB", (800, 200), (120, 140, 120)).save(png)
    d, s = evidence_slide()
    s.image(str(png), alt="The repair bench")
    out = tmp_path / "i.pptx"
    d.save(str(out))
    model, _ = load_deck(out)
    (pic,) = [x for x in model.slides[0].shapes if x.kind == "pic"]
    assert (pic.x, pic.y, pic.w) == (MAIN.x, MAIN.y, MAIN.w) and pic.h <= MAIN.h
    assert abs(pic.w / pic.h - 4) < 0.001  # the aspect ratio kept
    slide = _part(out, "ppt/slides/slide")
    descr = [x.get("descr") for x in slide.iter("{*}cNvPr") if x.get("descr")]
    assert descr == ["The repair bench"]


def test_image_needs_alt_and_a_readable_file(tmp_path):
    _d, s = evidence_slide()
    with pytest.raises(TypeError):
        s.image(str(tmp_path / "x.png"))
    with pytest.raises(PenError, match="cannot be read"):
        s.image(str(tmp_path / "missing.png"), alt="x")
