"""Audit 05 FX-18 (amendment B-22 item 5): a table cell's line pitch is size × max(1.2,
the twin's hhea line height) × line spacing + 0.01 mm, and each row one more 0.01 mm
(LibreOffice 26.8.0.3 rounds every row up once more; tools/measure_lo.py). The fit tables
store the hhea value. Repro: evidence/audit05-repros/attack_table2.py (on 24.2.7.2 the
longest `field` table the pen accepted ended 4.9 pt below its region)."""

import re
import zipfile
from fractions import Fraction

import pytest

from keyline.config import load as load_config
from keyline.fit import (
    LINE_ALLOWANCE_PT,
    ROW_ALLOWANCE_PT,
    WEIGHTS,
    Setting,
    cell_data,
    load_table,
)
from keyline.packs import resolve
from tests.acceptance.m2 import _lo

pytest.importorskip("pptx")

from keyline.pen import Deck, DoesNotFit

FAMILIES = [f for f, _twin in load_config().portable_fonts]
HHEA = {  # (ascender - descender + line gap) / units per em, of the installed twins
    "Arial": Fraction(1854 + 434 + 67, 2048),
    "Times New Roman": Fraction(1825 + 443 + 87, 2048),
    "Courier New": Fraction(1705 + 615, 2048),
    "Georgia": Fraction(1900 + 700, 2048),
    "Calibri": Fraction(1950 + 550, 2048),
    "Cambria": Fraction(900 + 250, 1000),
}


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("weight", WEIGHTS)
def test_the_tables_store_the_hhea_line_height(family, weight):
    assert load_table(family, weight).hhea_line_em == HHEA[family]


def test_cell_pitch():
    georgia = Setting("Georgia", "regular", Fraction(24), line_spacing=Fraction(11, 10))
    allowance = cell_data()[0]  # B-25 item 6: 0.05 mm, the largest excess measured (FX-31)
    assert georgia.cell_pitch == 24 * HHEA["Georgia"] * Fraction(11, 10) + allowance
    assert georgia.cell_pitch > georgia.pitch
    arial = Setting("Arial", "regular", Fraction(24), line_spacing=Fraction(11, 10))
    assert arial.cell_pitch == arial.pitch - LINE_ALLOWANCE_PT + allowance  # hhea 1.1499 < 1.2
    assert ROW_ALLOWANCE_PT == LINE_ALLOWANCE_PT


def test_the_pen_writes_rows_at_the_cell_pitch(tmp_path):
    d = Deck(pack="swiss", mode="presented", voice="field")
    d.add("evidence", "A table").table([["Style", "Used for"], ["Body", "Text"], ["Lede", "Lines"]])
    d.save(str(tmp_path / "t.pptx"))
    xml = zipfile.ZipFile(tmp_path / "t.pptx").read("ppt/slides/slide1.xml").decode()
    heights = [int(h) for h in re.findall(r'<a:tr h="(\d+)"', xml)]
    styles = resolve("swiss").styles["presented"]
    margins = Fraction(45720 * 2, 12700)
    expected = []
    for name in ("label", "body", "body"):
        st = styles[name]
        s = Setting("Georgia", st.weight, st.size_pt, line_spacing=st.line_spacing)
        expected.append(int(-(-(s.cell_pitch + ROW_ALLOWANCE_PT + margins) * 12700 // 1)))
    assert heights == expected


def longest_table(deck):
    best = None
    for n in range(1, 60):
        rows = [["Style", "Used for"]] + [[f"Row {i}", "Text"] for i in range(n)]
        trial = deck.add("evidence", "Scratch")
        try:
            trial.table(rows)
        except DoesNotFit:
            deck._slides.pop()
            return best
        deck._slides.pop()
        best = rows
    raise AssertionError("no table was refused")


@_lo.needs_lo(*FAMILIES)
@pytest.mark.parametrize("mode", ["presented", "read"])
def test_the_longest_table_stays_in_its_region(mode, tmp_path):
    """attack_table2.py, for every portable family through a test-only voice."""
    main = _lo.region_pt(resolve("swiss"), "keyline:evidence", "main")
    decks = []
    for family in FAMILIES:
        d = Deck(pack="swiss", mode=mode, voice=_lo.voice_file(tmp_path, family))
        d.add("evidence", "A table").table(longest_table(d))
        path = tmp_path / f"{family}.pptx"
        d.save(str(path))
        decks.append((family, path))
    for family, path in decks:
        (page,) = _lo.chars(path, tmp_path / f"lo-{family}")
        body = [c for c in page if c[2] >= main[1] - 1.5]
        assert max(c[4] for c in body) <= main[3] + 1.5, family  # 2 px at 1280 px
