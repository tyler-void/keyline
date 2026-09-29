"""Measure LibreOffice's line pitch and wrap behaviour against spec 002's fit constants
(amendments B-7 and B-21; tasks T-20 and its addendum).

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
- informational: the one-line threshold of three bold 14 pt labels, scanned 0.980× …
  1.010× in 0.0005 steps (T-20's first run).

The verdict is B-21's two criteria; the script exits 0 when both hold, else 2:
  (a) no stress case wraps at 1/0.99, the widest box the estimator accepts;
  (b) every measured pitch ≤ size × 1.2 × line spacing + 0.01 mm (LibreOffice's unit).
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


def _style(paragraph, family, size, bold, tracking=0.0, line_spacing=1.0):
    from pptx.util import Pt

    paragraph.line_spacing = line_spacing
    paragraph.space_before = paragraph.space_after = Pt(0)
    for run in paragraph.runs:
        run.font.name = family
        run.font.size = Pt(size)
        run.font.bold = bold
        if tracking:
            run.font._rPr.set("spc", str(round(tracking * size * 100)))


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


def convert(tmp: Path, name: str, deck_bytes: bytes, soffice: str):
    deck = tmp / f"{name}.pptx"
    deck.write_bytes(deck_bytes)
    work = tmp / name
    work.mkdir()
    return read_pages(convert_to_pdf(deck, soffice, work))


def main(argv: list[str]) -> int:
    families = load_config().portable_fonts
    soffice = find_soffice()
    if soffice is None:
        sys.exit("stop: soffice is not installed")
    version = libreoffice_version(soffice)
    out = [
        "# LibreOffice measurements for spec 002 amendments B-7 and B-21 (T-20, addendum)",
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
    with tempfile.TemporaryDirectory(prefix="keyline-measure-") as tmp:
        tmp_dir = Path(tmp)
        pitch_pages = convert(tmp_dir, "pitch", pitch_bytes, soffice)
        scan_pages = convert(tmp_dir, "scan", scan_bytes, soffice)
        stress_pages = convert(tmp_dir, "stress", stress_bytes, soffice)
    for probes, pages in ((pitch_probes, pitch_pages), (scan_probes, scan_pages)):
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

    # ---- verdict (B-21) ---------------------------------------------------------------
    a_ok, b_ok = not wrap_bad, not pitch_bad
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
    text = "\n".join(out) + "\n"
    print(text, end="")
    if len(argv) > 1:
        Path(argv[1]).write_text(text, encoding="utf-8")
    return 0 if a_ok and b_ok else 2


if __name__ == "__main__":
    if shutil.which("fc-match") is None:
        sys.exit("stop: fc-match is not installed")
    sys.exit(main(sys.argv))
