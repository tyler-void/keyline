"""Measure LibreOffice's line pitch and wrap behaviour against spec 002's fit constants
(amendments B-7, B-21 and B-22; T-20, its addendum, and the A2 fixes of audit 05).

    python tools/measure_lo.py [OUT_FILE]

Dev only (python-pptx, fontTools, pypdfium2). For each portable family (thresholds.toml
`portable_fonts`) the probes name the family itself, not its metric twin, so fontconfig
substitutes exactly as it does for a pen deck (audit 03 on Q-44). The script first prints
`fc-match` for every family and stops if one does not resolve to its twin. The probe
decks go through keyline's own render path (`render.convert_to_pdf`), and glyph origins
are read back from the PDF with pypdfium2.

What it measures:
- pitch: four lines at 13, 24, 48 and 60 pt, regular and bold, as line breaks and as
  paragraphs; and four lines at every (size, line spacing) the Swiss pack uses, regular;
- wrap, the stress set of audit 04: seven strings (narrow, wide caps, digits, Vietnamese,
  a sentence, two caps strings with +8 % tracking) at 9, 10, 12, 14 and 24 pt, regular
  and bold, in boxes 0.995×, 1.000×, 1.003×, 1.006× and 1/0.99× §6.4's estimate (the
  fontTools advance sum, upper-cased for caps, plus tracking × size per character; a
  character missing from the twin counts as its maximum advance);
- table-cell pitch (FX-18): a one-column table, cell margins 0 and rows 1 pt tall so
  LibreOffice grows each row to its text: four one-line rows, four two-line rows, and one
  cell of four lines (line breaks), at every (size, line spacing, weight) of the Swiss
  table styles and at 13, 24 and 48 pt with spacing 1.0;
- fallback advances (FX-19): ten CJK, emoji and Thai characters between two "H" (a run),
  and the same ten each between two "H" (mixed: LibreOffice adds space where Latin meets
  Asian text), per family, at 24 pt; a character's cost is the distance from the first
  to the last H origin, less the H advances, over ten; with the fonts LibreOffice used;
- informational: the one-line threshold of three bold 14 pt labels, scanned 0.980× …
  1.010× in 0.0005 steps (T-20's first run); and, per character of B-22 item 4, whether
  LibreOffice carries a full line's last word down with " <char> end" (bold Arial 48 pt),
  once with room on the line for the space after that word and once without.

The verdict is B-21's two criteria and B-22's two; the script exits 0 when all hold,
else 2:
  (a) no stress case wraps at 1/0.99, the widest box the estimator accepts;
  (b) every measured pitch ≤ size × 1.2 × line spacing + 0.01 mm (LibreOffice's unit);
  (c) in table cells, every line pitch ≤ size × max(1.2, the twin's hhea line height) ×
      line spacing + 0.01 mm (B-22 item 5), and every row ≤ its lines at that pitch plus
      0.01 mm (LibreOffice rounds each row up once more);
  (d) every fallback advance ≤ the estimate for a missing glyph, max(the twin's maximum
      advance, `missing_glyph_em` of thresholds.toml) (B-22 item 6).
Every number printed is tagged with the `soffice --version` that produced it.
"""

from __future__ import annotations

import ctypes
import datetime as dt
import io
import itertools
import platform
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from keyline import __version__  # noqa: E402
from keyline.config import load as load_config  # noqa: E402
from keyline.render import convert_to_pdf, find_soffice, libreoffice_version  # noqa: E402

EXPECTED_VERSION = "26.8.0.3"
PITCH_SIZES = (13, 24, 48, 60)
WEIGHTS = ("regular", "bold")
LINE = "Hxgh Ápq"
PITCH_EM = 1.2
UNIT_PT = 0.01 * 72 / 25.4  # LibreOffice lays text out in 1/100 mm: 0.0283 pt
LABELS = ("ACTIVE KEEPERS BY MONTH", "median wait for a match", "Oldest tree on the waitlist")
SCAN = tuple(f"{0.980 + i * 0.0005:.4f}" for i in range(61))  # 0.9800 … 1.0100
MARGIN = 1 / 0.99  # §6.4: a line fits when its estimate ≤ 0.99 × the width
STRESS_FACTORS = (0.995, 1.000, 1.003, 1.006, MARGIN)
STRESS_SIZES = (9, 10, 12, 14, 24)
STRESS = {  # name: (text, caps, tracking), audit 04's evidence/audit04_stress_fit.py
    "narrow": ("illicit little lilies fill all tills", False, 0.0),
    "wide-caps": ("WOMBAT MEMO WAVE MW", False, 0.0),
    "digits": ("12,400 keepers; 3.2% swipe right; 0.4%", False, 0.0),
    "vietnamese": ("Cây bonsai già nhất trong danh sách chờ", False, 0.0),
    "sentence": ("Median wait for a first match is 41 days", False, 0.0),
    "label-caps-tracked": ("Active keepers by month", True, 0.08),
    "narrow-caps-tracked": ("fill all tills; lilies", True, 0.08),
}
FALLBACK = {  # name: one character the twins lack (as code points: the source stays ASCII)
    "cjk": chr(0x6F22),
    "emoji": chr(0x1F600),
    "thai": chr(0x0E2A),
}
FALLBACK_SIZE, FALLBACK_COUNT = 24, 10
LB13_FIRST = "plan build ship measure learn repeat"
LB13_SIZE = 48
PEN_LANG = "en-US"  # the run language the pen writes
SLIDE_W_IN, SLIDE_H_IN = 13.333, 7.5
EMU_PER_PT = 12700


def fc_match(pattern: str, fmt: str) -> str:
    out = subprocess.run(["fc-match", "-f", fmt, pattern], capture_output=True, text=True)
    return out.stdout.split(",")[0].strip()


def check_fonts(families) -> list[str]:
    lines, bad = [], []
    for family, twin in families:
        got = fc_match(family, "%{family}")
        ok = got.casefold() == twin.casefold()
        lines.append(f"  {family:<16} -> {got:<18} twin {twin:<18} {'ok' if ok else 'MISMATCH'}")
        if not ok:
            bad.append(family)
    if bad:
        print("\n".join(lines))
        sys.exit(f"stop: {', '.join(bad)} do not resolve to their metric twins (audit 03, Q-44)")
    return lines


_fonts: dict = {}


def _font(family: str, weight: str):
    """(cmap, hmtx, units per em, maximum advance) of the twin fontconfig picks."""
    from fontTools.ttLib import TTFont

    if (family, weight) not in _fonts:
        style = "Bold" if weight == "bold" else "Regular"
        font = TTFont(fc_match(f"{family}:style={style}", "%{file}"))
        hmtx = font["hmtx"]
        widest = max(advance for advance, _ in hmtx.metrics.values())
        _fonts[family, weight] = (font.getBestCmap(), hmtx, font["head"].unitsPerEm, widest)
    return _fonts[family, weight]


def hhea_em(family: str, weight: str) -> float:
    """The twin's hhea line height (ascender - descender + line gap) in em."""
    from fontTools.ttLib import TTFont

    style = "Bold" if weight == "bold" else "Regular"
    font = TTFont(fc_match(f"{family}:style={style}", "%{file}"))
    hhea = font["hhea"]
    return (hhea.ascent - hhea.descent + hhea.lineGap) / font["head"].unitsPerEm


def estimate(family, weight, text, size, caps=False, tracking=0.0):
    """§6.4's width estimate in pt, the text as set, and the characters the twin lacks."""
    cmap, hmtx, upm, widest = _font(family, weight)
    shown = unicodedata.normalize("NFC", text.upper() if caps else text)
    missing = sorted({ch for ch in shown if ord(ch) not in cmap})
    units = sum(hmtx[cmap[ord(ch)]][0] if ord(ch) in cmap else widest for ch in shown)
    return units * size / upm + tracking * size * len(shown), shown, missing


def _box(slide, x_pt, y_pt, w_pt, h_pt):
    from pptx.enum.text import MSO_AUTO_SIZE
    from pptx.util import Emu

    box = slide.shapes.add_textbox(
        Emu(round(x_pt * EMU_PER_PT)),
        Emu(round(y_pt * EMU_PER_PT)),
        Emu(round(w_pt * EMU_PER_PT)),
        Emu(round(h_pt * EMU_PER_PT)),
    )
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    return tf


def _style(paragraph, family, size, bold, tracking=0.0, line_spacing=1.0, lang=None):
    """`lang`: the run language, which chooses LibreOffice's line-break rules; the pen
    writes "en-US" (the B-21 probes leave it unset, as T-20 and audit 04 ran them)."""
    from pptx.util import Pt

    paragraph.line_spacing = line_spacing
    paragraph.space_before = paragraph.space_after = Pt(0)
    for run in paragraph.runs:
        run.font.name = family
        run.font.size = Pt(size)
        run.font.bold = bold
        if tracking:
            run.font._rPr.set("spc", str(round(tracking * size * 100)))
        if lang:
            run.font._rPr.set("lang", lang)


def _deck():
    from pptx import Presentation
    from pptx.util import Inches

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(SLIDE_W_IN), Inches(SLIDE_H_IN)
    return prs


def _bytes(prs) -> bytes:
    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


def pack_spacings() -> list[tuple[float, float]]:
    """Every (size, line spacing) of the Swiss pack, both modes."""
    from keyline.packs import resolve

    pack = resolve("swiss")
    pairs = {
        (float(st.size_pt), float(st.line_spacing))
        for styles in pack.styles.values()
        for st in styles.values()
    }
    return sorted(pairs)


def build_pitch(families):
    """Four-line probes: the T-20 set and the Swiss pack's (size, line spacing) set."""
    prs, probes, top = _deck(), [], 36.0
    for family, _twin in families:
        cases = [(w, s, 1.0, k) for w in WEIGHTS for s in PITCH_SIZES for k in ("br", "p")]
        cases += [("regular", s, ls, "br") for s, ls in pack_spacings()]
        for weight, size, ls, kind in cases:
            tf = _box(prs.slides.add_slide(prs.slide_layouts[6]), 72, top, 800, 480)
            if kind == "br":
                tf.paragraphs[0].text = "\v".join([LINE] * 4)  # \v is <a:br/>
            else:
                tf.text = "\n".join([LINE] * 4)
            for p in tf.paragraphs:
                _style(p, family, size, weight == "bold", line_spacing=ls)
            probes.append((family, weight, size, ls, kind, top))
    return _bytes(prs), probes


def build_scan(families):
    """The one-line threshold of three bold 14 pt labels (informational, T-20)."""
    prs, probes = _deck(), []
    for family, _twin in families:
        for label in LABELS:
            width, _shown, _missing = estimate(family, "bold", label, 14)
            for factor in SCAN:
                tf = _box(
                    prs.slides.add_slide(prs.slide_layouts[6]), 72, 36, width * float(factor), 200
                )
                tf.paragraphs[0].text = label
                _style(tf.paragraphs[0], family, 14, True)
                probes.append((family, label, factor))
    return _bytes(prs), probes


def build_stress(families):
    """Audit 04's stress set: every (family, weight, size, string) at five box widths."""
    prs, probes = _deck(), []
    for family, _twin in families:
        for weight in WEIGHTS:
            for size in STRESS_SIZES:
                for name, (text, caps, tracking) in STRESS.items():
                    width, shown, missing = estimate(family, weight, text, size, caps, tracking)
                    for factor in STRESS_FACTORS:
                        tf = _box(
                            prs.slides.add_slide(prs.slide_layouts[6]), 36, 36, width * factor, 120
                        )
                        tf.paragraphs[0].text = shown
                        _style(tf.paragraphs[0], family, size, weight == "bold", tracking)
                        probes.append((family, weight, size, name, factor, "".join(missing)))
    return _bytes(prs), probes


def table_cases() -> list[tuple[float, float, str]]:
    """(size, line spacing, weight): every Swiss table style (body and label, both modes),
    and 13, 24 and 48 pt at spacing 1.0 in both weights."""
    from keyline.packs import resolve

    cases = {
        (float(st.size_pt), float(st.line_spacing), st.weight)
        for styles in resolve("swiss").styles.values()
        for st in (styles["body"], styles["label"])
    }
    cases |= {(size, 1.0, weight) for size in (13.0, 24.0, 48.0) for weight in WEIGHTS}
    return sorted(cases)


def build_table(families):
    """Table-cell pitch probes (FX-18): four one-line rows, and one cell of four lines."""
    from pptx.util import Emu

    prs, probes = _deck(), []
    for family, _twin in families:
        for size, ls, weight in table_cases():
            for kind in ("rows", "rows2", "br"):
                n = 1 if kind == "br" else 4
                slide = prs.slides.add_slide(prs.slide_layouts[6])
                frame = slide.shapes.add_table(
                    n, 1, Emu(72 * EMU_PER_PT), Emu(36 * EMU_PER_PT), Emu(800 * EMU_PER_PT),
                    Emu(n * EMU_PER_PT),
                )  # fmt: skip
                for r in range(n):
                    frame.table.rows[r].height = Emu(EMU_PER_PT)  # grown to the text
                    cell = frame.table.cell(r, 0)
                    cell.margin_left = cell.margin_right = 0
                    cell.margin_top = cell.margin_bottom = 0
                    lines = {"rows": 1, "rows2": 2, "br": 4}[kind]
                    cell.text_frame.text = "\v".join([LINE] * lines)
                    _style(
                        cell.text_frame.paragraphs[0],
                        family,
                        size,
                        weight == "bold",
                        0,
                        ls,
                        PEN_LANG,
                    )
                probes.append((family, weight, size, ls, kind))
    return _bytes(prs), probes


def build_fallback(families):
    """Ten characters of each fallback script in a row, per family (FX-19)."""
    prs, probes = _deck(), []
    for family, _twin in families:
        for name, ch in FALLBACK.items():
            for kind in ("run", "mixed"):
                tf = _box(prs.slides.add_slide(prs.slide_layouts[6]), 36, 36, 1200, 200)
                body = ch * FALLBACK_COUNT if kind == "run" else "H".join([ch] * FALLBACK_COUNT)
                tf.paragraphs[0].text = f"H{body}H"
                _style(tf.paragraphs[0], family, FALLBACK_SIZE, False, lang=PEN_LANG)
                probes.append((family, name, kind))
    return _bytes(prs), probes


def build_lb13():
    """Per character of B-22 item 4: a first line that fits the box at the estimator's
    0.99 margin, then " <char> end", which cannot fit on that line even at LibreOffice's
    widest threshold (1.003x, B-21)."""
    sys.path.insert(0, str(ROOT / "src"))
    from keyline.fit.text import NO_BREAK_BEFORE

    prs, probes = _deck(), []
    first_w, _shown, _missing = estimate("Arial", "bold", LB13_FIRST, LB13_SIZE)
    space_w, _shown, _missing = estimate("Arial", "bold", LB13_FIRST + " ", LB13_SIZE)
    for ch in NO_BREAK_BEFORE:
        with_ch, _s, _m = estimate("Arial", "bold", f"{LB13_FIRST} {ch}", LB13_SIZE)
        for room, box_w in (
            ("space fits", (space_w + with_ch) / 2 / 1.003),
            ("space does not fit", first_w * 1.001),
        ):
            assert with_ch > box_w * 1.003, (ch, room)
            tf = _box(prs.slides.add_slide(prs.slide_layouts[6]), 36, 36, box_w, 300)
            tf.paragraphs[0].text = f"{LB13_FIRST} {ch} end"
            _style(tf.paragraphs[0], "Arial", LB13_SIZE, True, lang=PEN_LANG)
            probes.append((ch, room))
    return _bytes(prs), probes


def read_origins(pdf: Path):
    """Per page: (glyph origins as (char, x, y) in reading order, font names)."""
    import pypdfium2 as pdfium
    import pypdfium2.raw as raw

    doc = pdfium.PdfDocument(str(pdf))
    pages = []
    try:
        for page in doc:
            tp = page.get_textpage()
            glyphs, fonts = [], set()
            x, y = ctypes.c_double(), ctypes.c_double()
            buf = ctypes.create_string_buffer(256)
            flags = ctypes.c_int()
            for i in range(tp.count_chars()):
                text = tp.get_text_range(i, 1)
                if not text.strip():
                    continue
                raw.FPDFText_GetCharOrigin(tp.raw, i, ctypes.byref(x), ctypes.byref(y))
                glyphs.append((text, x.value, y.value))
                n = raw.FPDFText_GetFontInfo(tp.raw, i, buf, 256, ctypes.byref(flags))
                fonts.add(buf.raw[: max(n - 1, 0)].decode("utf-8", "replace"))
            pages.append((glyphs, sorted(fonts)))
            tp.close()
    finally:
        doc.close()
    return pages


def read_pages(pdf: Path):
    """Per page: (baselines top to bottom, font names, page height), from glyph origins.
    Glyphs are grouped into lines by their origin rounded to 0.01 pt, and each baseline is
    the mean of its glyphs' raw origins, so a pitch is not blurred by rounding."""
    import pypdfium2 as pdfium
    import pypdfium2.raw as raw

    doc = pdfium.PdfDocument(str(pdf))
    pages = []
    try:
        for page in doc:
            height = page.get_height()
            tp = page.get_textpage()
            lines: dict[float, list[float]] = {}
            fonts = set()
            x, y = ctypes.c_double(), ctypes.c_double()
            buf = ctypes.create_string_buffer(256)
            flags = ctypes.c_int()
            for i in range(tp.count_chars()):
                if not tp.get_text_range(i, 1).strip():
                    continue
                raw.FPDFText_GetCharOrigin(tp.raw, i, ctypes.byref(x), ctypes.byref(y))
                lines.setdefault(round(y.value, 2), []).append(y.value)
                n = raw.FPDFText_GetFontInfo(tp.raw, i, buf, 256, ctypes.byref(flags))
                fonts.add(buf.raw[: max(n - 1, 0)].decode("utf-8", "replace"))
            ys = sorted((sum(v) / len(v) for v in lines.values()), reverse=True)
            pages.append((ys, sorted(fonts), height))
            tp.close()
    finally:
        doc.close()
    return pages


def convert(tmp: Path, name: str, deck_bytes: bytes, soffice: str, origins: bool = False):
    deck = tmp / f"{name}.pptx"
    deck.write_bytes(deck_bytes)
    work = tmp / name
    work.mkdir()
    pdf = convert_to_pdf(deck, soffice, work)
    return read_origins(pdf) if origins else read_pages(pdf)


def main(argv: list[str]) -> int:
    families = load_config().portable_fonts
    soffice = find_soffice()
    if soffice is None:
        sys.exit("stop: soffice is not installed")
    version = libreoffice_version(soffice)
    out = [
        "# LibreOffice measurements for spec 002 amendments B-7, B-21 and B-22 (T-20; A2 fixes)",
        f"version: {version}",
        f"date: {dt.date.today().isoformat()}  keyline {__version__}  {platform.platform()}",
    ]
    if EXPECTED_VERSION not in version:
        out.append(f"note: expected LibreOffice {EXPECTED_VERSION}; this run used {version}")
    out += ["", "fc-match (probes name the portable family; fontconfig picks the twin):"]
    out += check_fonts(families)

    pitch_bytes, pitch_probes = build_pitch(families)
    scan_bytes, scan_probes = build_scan(families)
    stress_bytes, stress_probes = build_stress(families)
    table_bytes, table_probes = build_table(families)
    fallback_bytes, fallback_probes = build_fallback(families)
    lb13_bytes, lb13_probes = build_lb13()
    with tempfile.TemporaryDirectory(prefix="keyline-measure-") as tmp:
        tmp_dir = Path(tmp)
        pitch_pages = convert(tmp_dir, "pitch", pitch_bytes, soffice)
        scan_pages = convert(tmp_dir, "scan", scan_bytes, soffice)
        stress_pages = convert(tmp_dir, "stress", stress_bytes, soffice)
        table_pages = convert(tmp_dir, "table", table_bytes, soffice)
        fallback_pages = convert(tmp_dir, "fallback", fallback_bytes, soffice, origins=True)
        lb13_pages = convert(tmp_dir, "lb13", lb13_bytes, soffice, origins=True)
    for probes, pages in (
        (pitch_probes, pitch_pages),
        (scan_probes, scan_pages),
        (table_probes, table_pages),
        (fallback_probes, fallback_pages),
        (lb13_probes, lb13_pages),
    ):
        if len(pages) != len(probes):
            sys.exit(f"stop: {len(pages)} PDF pages for {len(probes)} probes")
    if len(stress_pages) != len(stress_probes):
        sys.exit(f"stop: {len(stress_pages)} PDF pages for {len(stress_probes)} probes")

    # ---- pitch -----------------------------------------------------------------------
    out += ["", f"pitch: four lines; bound = size x 1.2 x line spacing + 0.01 mm, {version}"]
    out.append(
        f"  {'family':<16} {'weight':<7} {'size':>5} {'ls':>4} {'kind':<4}"
        f" {'pitch pt':>9} {'em':>7} {'bound pt':>9} {'slack pt':>9} {'1st bl em':>9}  font"
    )
    worst_slack, pitch_bad = None, []
    for probe, (ys, fonts, height) in zip(pitch_probes, pitch_pages, strict=True):
        family, weight, size, ls, kind, top = probe
        if len(ys) != 4:
            pitch_bad.append((probe, f"{len(ys)} lines"))
            continue
        pitch = sum(a - b for a, b in itertools.pairwise(ys)) / 3
        bound = size * PITCH_EM * ls + UNIT_PT
        slack = bound - pitch
        first = (height - top - ys[0]) / size
        worst_slack = slack if worst_slack is None else min(worst_slack, slack)
        if slack < 0:
            pitch_bad.append((probe, f"pitch {pitch:.4f} > bound {bound:.4f}"))
        out.append(
            f"  {family:<16} {weight:<7} {size:>5g} {ls:>4.1f} {kind:<4} {pitch:>9.4f}"
            f" {pitch / size:>7.4f} {bound:>9.4f} {slack:>9.4f} {first:>9.4f}  {', '.join(fonts)}"
        )

    # ---- wrap: the stress set --------------------------------------------------------
    cases: dict = {}
    for probe, (ys, _fonts, _h) in zip(stress_probes, stress_pages, strict=True):
        family, weight, size, name, factor, missing = probe
        cases.setdefault((family, weight, size, name, missing), {})[factor] = len(ys)
    out += ["", f"wrap, audit 04's stress set: lines at each box / estimate factor, {version}"]
    out.append(
        f"  {'family':<16} {'weight':<7} {'size':>4} {'string':<20} "
        + " ".join(f"{f:>6.4f}" for f in STRESS_FACTORS)
        + "  twin lacks"
    )
    wrap_bad, smallest = [], {}
    for (family, weight, size, name, missing), counts in cases.items():
        row = " ".join(f"{counts[f]:>6}" for f in STRESS_FACTORS)
        out.append(f"  {family:<16} {weight:<7} {size:>4} {name:<20} {row}  {missing}")
        if counts[MARGIN] != 1:
            wrap_bad.append((family, weight, size, name, counts[MARGIN]))
        fits = [f for f in STRESS_FACTORS if counts[f] == 1]
        smallest[family, weight, size, name] = min(fits) if fits else None
    histogram: dict[str, int] = {}
    for value in smallest.values():
        key = "none" if value is None else ("<=0.9950" if value <= 0.995 else f"{value:.4f}")
        histogram[key] = histogram.get(key, 0) + 1
    out.append(f"  smallest fitting factor, histogram: {dict(sorted(histogram.items()))}")

    # ---- informational: the label threshold scan --------------------------------------
    out += ["", f"one-line threshold of bold 14 pt labels (informational), {version}:"]
    seqs: dict = {}
    for (family, label, factor), (ys, _f, _h) in zip(scan_probes, scan_pages, strict=True):
        seqs.setdefault((family, label), []).append((float(factor), len(ys)))
    for (family, label), seq in seqs.items():
        one = [f for f, n in seq if n == 1]
        where = f">= {min(one):.4f}" if one else f"> {float(SCAN[-1]):.4f}"
        out.append(f"  {family:<16} {label:<28} one line at {where}")

    # ---- table-cell pitch (B-22 item 5) -------------------------------------------------
    out += [
        "",
        "table cells: line bound = size x max(1.2, hhea) x line spacing + 0.01 mm; a row of n"
        f" lines = n x line bound + 0.01 mm; rows = 1 line a row, rows2 = 2, br = 4 in one cell,"
        f" {version}",
    ]
    out.append(
        f"  {'family':<16} {'weight':<7} {'size':>5} {'ls':>4} {'kind':<5} {'hhea em':>7}"
        f" {'pitch pt':>9} {'em/line':>7} {'bound pt':>9} {'slack pt':>9}"
    )
    table_bad, table_slack = [], None
    for probe, (ys, _fonts, _h) in zip(table_probes, table_pages, strict=True):
        family, weight, size, ls, kind = probe
        per_row = {"rows": 1, "rows2": 2, "br": 4}[kind]
        if len(ys) != (4 if kind == "br" else 4 * per_row):
            table_bad.append((probe, f"{len(ys)} lines"))
            continue
        hhea = hhea_em(family, weight)
        line_bound = size * max(PITCH_EM, hhea) * ls + UNIT_PT
        if kind == "br":  # line pitch inside one cell
            pitch = sum(a - b for a, b in itertools.pairwise(ys)) / 3
            bound = line_bound
        else:  # row pitch: the first baselines of consecutive rows
            firsts = ys[::per_row]
            pitch = sum(a - b for a, b in itertools.pairwise(firsts)) / 3
            bound = per_row * line_bound + UNIT_PT
        slack = bound - pitch
        table_slack = slack if table_slack is None else min(table_slack, slack)
        if slack < 0:
            table_bad.append((probe, f"pitch {pitch:.4f} > bound {bound:.4f}"))
        out.append(
            f"  {family:<16} {weight:<7} {size:>5g} {ls:>4.2f} {kind:<5} {hhea:>7.4f}"
            f" {pitch:>9.4f} {pitch / size / ls / (1 if kind == 'br' else per_row):>7.4f}"
            f" {bound:>9.4f} {slack:>9.4f}"
        )

    # ---- fallback advances (B-22 item 6) ------------------------------------------------
    missing_em = load_config().values.get("missing_glyph_em")
    out += [
        "",
        f"fallback advances: {FALLBACK_COUNT} characters at {FALLBACK_SIZE} pt; estimate = "
        f"max(twin's maximum advance, missing_glyph_em = "
        f"{'not set' if missing_em is None else f'{float(missing_em):.2f}'}), {version}",
    ]
    fallback_bad, widest = [], 0.0
    for (family, name, kind), (glyphs, fonts) in zip(fallback_probes, fallback_pages, strict=True):
        hs = [x for t, x, _y in glyphs if t == "H"]
        cmap, hmtx, upm, max_adv = _font(family, "regular")
        in_twin = ord(FALLBACK[name]) in cmap
        n_h = 2 if kind == "run" else FALLBACK_COUNT + 1
        if len(hs) != n_h:
            fallback_bad.append((family, name, kind, f"{len(hs)} H origins"))
            continue
        h_pt = hmtx[cmap[ord("H")]][0] * FALLBACK_SIZE / upm
        em = (hs[-1] - hs[0] - (n_h - 1) * h_pt) / FALLBACK_COUNT / FALLBACK_SIZE
        estimate_em = max(max_adv / upm, float(missing_em or 0))
        if not in_twin:
            widest = max(widest, em)
            if em > estimate_em:
                fallback_bad.append((family, name, kind, f"{em:.4f} em > {estimate_em:.4f} em"))
        note = "in the twin" if in_twin else f"estimate {estimate_em:.4f} em"
        out.append(
            f"  {family:<16} {name:<6} {kind:<6} {em:>7.4f} em  {note:<22} {', '.join(fonts)}"
        )
    out.append(f"  widest fallback advance: {widest:.4f} em")

    # ---- informational: line breaks before closing punctuation (B-22 item 4) -----------
    out += [
        "",
        f"line breaks before closing punctuation, bold Arial {LB13_SIZE} pt (informational),"
        f" {version}:",
    ]
    rows: dict[str, list[str]] = {}
    for (ch, room), (glyphs, _fonts) in zip(lb13_probes, lb13_pages, strict=True):
        at = max(i for i, g in enumerate(glyphs) if g[0] == ch)
        kept = abs(glyphs[at - 1][2] - glyphs[at][2]) < LB13_SIZE / 2
        rows.setdefault(ch, []).append(f"{room}: {'kept with the word' if kept else 'breaks'}")
    for ch, cells in rows.items():
        out.append(f"  U+{ord(ch):04X} {ch}  " + "  |  ".join(f"{c:<32}" for c in cells).rstrip())

    # ---- verdict (B-21, B-22) -----------------------------------------------------------
    a_ok, b_ok = not wrap_bad, not pitch_bad
    c_ok, d_ok = not table_bad, not fallback_bad
    out += ["", "verdict (amendment B-21):"]
    out.append(
        f"  (a) no stress case wraps at 1/0.99 = {MARGIN:.4f}: {len(cases)} cases, "
        f"{len(wrap_bad)} wrap: {'HOLDS' if a_ok else 'FAILS'}"
    )
    for bad in wrap_bad:
        out.append(f"      wraps: {bad}")
    out.append(
        f"  (b) every pitch <= size x 1.2 x line spacing + 0.01 mm ({UNIT_PT:.4f} pt): "
        f"{len(pitch_probes)} probes, smallest slack {worst_slack:.4f} pt: "
        f"{'HOLDS' if b_ok else 'FAILS'}"
    )
    for bad in pitch_bad:
        out.append(f"      over: {bad}")
    out += ["", "verdict (amendment B-22):"]
    out.append(
        f"  (c) every table line <= size x max(1.2, hhea) x line spacing + 0.01 mm, every row"
        f" <= its lines + 0.01 mm: "
        f"{len(table_probes)} probes, smallest slack {table_slack:.4f} pt: "
        f"{'HOLDS' if c_ok else 'FAILS'}"
    )
    for bad in table_bad:
        out.append(f"      over: {bad}")
    out.append(
        f"  (d) every fallback advance <= max(maximum advance, missing_glyph_em): "
        f"{len(fallback_probes)} probes, widest {widest:.4f} em: {'HOLDS' if d_ok else 'FAILS'}"
    )
    for bad in fallback_bad:
        out.append(f"      over: {bad}")
    text = "\n".join(out) + "\n"
    print(text, end="")
    if len(argv) > 1:
        Path(argv[1]).write_text(text, encoding="utf-8")
    return 0 if a_ok and b_ok and c_ok and d_ok else 2


if __name__ == "__main__":
    if shutil.which("fc-match") is None:
        sys.exit("stop: fc-match is not installed")
    sys.exit(main(sys.argv))
