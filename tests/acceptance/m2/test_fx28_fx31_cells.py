"""Audit 06 FX-28 and FX-31 (amendment B-25 item 6, B-22 item 7): in a table cell, each
line's pitch is size × max(1.2, the twin's hhea) × line spacing + `cell_line_allowance_mm`,
the largest excess measured on any LibreOffice version (0.05 mm, 24.2.7.2); a cell with a
glyph the twin lacks sets its lines at `missing_line_em` at least (24.2.7.2 uses the
fallback font's hhea: CJK about 1.42 em in the audit's repro). Repro:
evidence/audit06-repros/t_table.py; the measurements are tools/measure_lo.py's."""

import math
import re
import zipfile
from fractions import Fraction as F

import pytest

from keyline.config import load as load_config
from keyline.fit import ROW_ALLOWANCE_PT, Setting, cell_data, load_table
from keyline.packs import resolve
from tests.acceptance.m2 import _lo
from tests.conftest import ROOT

pytest.importorskip("pptx")

from keyline.pen import Deck, DoesNotFit

MM = F(72, 254) * 10  # pt per mm
EVIDENCE = ROOT / "specs/002-skill-pack/evidence"
MEASUREMENTS = {
    "24.2.7.2": EVIDENCE / "audit06-repros/measure_lo-on-24.2.7.2.txt",
    "26.8.0.3": EVIDENCE / "lo-26.8.0.3-measurements.txt",
}
ROW = re.compile(
    r"^\s+(?P<family>[A-Z][\w ]+?)\s+(?P<weight>regular|bold)\s+(?P<size>[\d.]+)\s+"
    r"(?P<ls>[\d.]+)\s+(?P<kind>rows2|rows|br)\s+(?P<hhea>[\d.]+)\s+(?P<pitch>[\d.]+)\s"
)
CJK = chr(0x6F22) + chr(0x5B57)
THAI = "".join(map(chr, (0x0E15, 0x0E25, 0x0E32, 0x0E14)))


def excesses(path):
    """Per table probe of a measure_lo output, the excess per cell line over size × em ×
    line spacing, in mm (a row's own unit counted in, as audit 06 measured it)."""
    out, lines_ = [], path.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines_) if line.startswith("table cells"))
    end = next(i for i in range(start, len(lines_)) if not lines_[i].strip())
    for line in lines_[start:end]:
        m = ROW.match(line)
        if m:
            size, ls, pitch = (float(m[k]) for k in ("size", "ls", "pitch"))
            hhea = float(load_table(m["family"], m["weight"]).hhea_line_em)  # exact, not printed
            lines = {"rows": 1, "rows2": 2, "br": 1}[m["kind"]]
            out.append((pitch - lines * size * max(1.2, hhea) * ls) / lines / float(MM))
    return out


@pytest.mark.parametrize("version", list(MEASUREMENTS))
def test_the_cell_allowance_covers_every_measured_version(version):
    found = excesses(MEASUREMENTS[version])
    assert len(found) == 180, len(found)  # 6 families x 30 table probes
    allowance = float(load_config().cell_line_allowance_mm)
    assert math.ceil(round(max(found), 6) * 100) / 100 <= allowance
    if version == "24.2.7.2":
        assert math.ceil(round(max(found), 6) * 100) / 100 == allowance  # audit 06: 0.05 mm


def test_the_cell_data():
    allowance, line_em = cell_data()
    config = load_config()
    assert allowance == config.cell_line_allowance_mm * MM and line_em == config.missing_line_em
    georgia = Setting("Georgia", "bold", F(14))
    hhea = F(1900 + 700, 2048)
    assert georgia.cell_pitch == 14 * hhea + allowance
    assert georgia.cell_line_pitch(True) == 14 * line_em + allowance  # 1.52 > 1.2695


def test_missing_line_em_covers_the_installed_fallback_fonts():
    """24.2.7.2 sets a cell line at max(1.2, the hhea of the font that sets it)."""
    fonttools = pytest.importorskip("fontTools.ttLib")
    import shutil
    import subprocess

    if shutil.which("fc-match") is None:
        pytest.skip("fc-match is not installed")
    for ch in (CJK[0], chr(0x1F600), THAI[0]):
        path = subprocess.run(
            ["fc-match", "-f", "%{file}", f"Arial:charset={ord(ch):x}"],
            capture_output=True,
            text=True,
        ).stdout
        font = fonttools.TTFont(path, fontNumber=0)
        h = font["hhea"]
        assert (h.ascent - h.descent + h.lineGap) / font["head"].unitsPerEm <= float(
            load_config().missing_line_em
        ), path


def test_a_row_with_a_fallback_glyph_takes_missing_line_em(tmp_path):
    d = Deck(pack="swiss", mode="presented", voice="neutral")
    d.add("evidence", "A table").table([["Item", "Value"], [f"Q3 {CJK}", "12"], ["Q4", "13"]])
    d.save(str(tmp_path / "t.pptx"))
    xml = zipfile.ZipFile(tmp_path / "t.pptx").read("ppt/slides/slide1.xml").decode()
    heights = [int(h) for h in re.findall(r'<a:tr h="(\d+)"', xml)]
    body = resolve("swiss").styles["presented"]["body"]
    s = Setting("Arial", body.weight, body.size_pt, line_spacing=body.line_spacing)
    margins = F(45720 * 2, 12700)
    fallback = math.ceil((s.cell_line_pitch(True) + ROW_ALLOWANCE_PT + margins) * 12700)
    plain = math.ceil((s.cell_pitch + ROW_ALLOWANCE_PT + margins) * 12700)
    assert heights[1:] == [fallback, plain]


def most_rows(mode, voice, cell):
    best = None
    for n in range(1, 60):
        rows = [["Item", "Value"]] + [[cell, cell] for _ in range(n)]
        try:
            Deck(pack="swiss", mode=mode, voice=voice).add("evidence", "x").table(rows)
        except DoesNotFit:
            return best
        best = rows
    raise AssertionError("no table was refused")


@_lo.needs_lo("Arial", "Georgia", "Calibri")
@pytest.mark.parametrize("mode", ["presented", "read"])
def test_the_longest_fallback_tables_stay_in_their_region(mode, tmp_path):
    """attack: t_table.py, for CJK, Thai and a mixed cell, in three families."""
    main = _lo.region_pt(resolve("swiss"), "keyline:evidence", "main")
    for family in ("Arial", "Georgia", "Calibri"):
        voice = _lo.voice_file(tmp_path, family)
        for name, cell in (("cjk", CJK), ("thai", THAI), ("mixed", f"Q3 {CJK}")):
            d = Deck(pack="swiss", mode=mode, voice=voice)
            d.add("evidence", "x").table(most_rows(mode, voice, cell))
            path = tmp_path / f"{family}-{name}.pptx"
            d.save(str(path))
            (page,) = _lo.chars(path, tmp_path / f"lo-{family}-{name}")
            body = [c for c in page if c[2] >= main[1] - 1.5]
            assert body and max(c[4] for c in body) <= main[3] + 1.5, (family, name)
