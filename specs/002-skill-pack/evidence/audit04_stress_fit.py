"""Auditor's stress test of spec 002 §6.4's fit constants against LibreOffice.

Part A (wrap): for each portable family x weight x size x string, a one-line text box whose
width is factor x the §6.4 estimate (fontTools advance sum, no kerning, caps upper-cased,
plus tracking x size per character). The decisive factor is 1/0.99 = 1.0101: the widest
box in which the estimator would still accept one line. Any string that LibreOffice wraps
at 1.0101 is a text the pen would accept and LibreOffice would break.

Part B (pitch): four lines at every (size, line_spacing) the Swiss pack uses, per family,
regular; measured pitch vs size x 1.2 x line_spacing, and the first baseline vs the box top.
"""

from __future__ import annotations

import io
import itertools
import sys
import tempfile
import tomllib
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # run from tools/ in a keyline checkout
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from measure_lo import _box, fc_match, read_pages  # noqa: E402
from keyline.config import load as load_config  # noqa: E402
from keyline.render import convert_to_pdf, find_soffice, libreoffice_version  # noqa: E402

FACTORS = (0.995, 1.000, 1.003, 1.006, 1 / 0.99)
STRINGS = {
    "narrow": ("illicit little lilies fill all tills", False, 0.0),
    "wide-caps": ("WOMBAT MEMO WAVE MW", False, 0.0),
    "digits": ("12,400 keepers; 3.2% swipe right; 0.4%", False, 0.0),
    "vietnamese": ("Cây bonsai già nhất trong danh sách chờ", False, 0.0),
    "sentence": ("Median wait for a first match is 41 days", False, 0.0),
    "label-caps-tracked": ("Active keepers by month", True, 0.08),
    "narrow-caps-tracked": ("fill all tills; lilies", True, 0.08),
}
SIZES = (9, 10, 12, 14, 24)
WEIGHTS = ("regular", "bold")
EMU_PER_PT = 12700


def font_path(family, weight):
    return fc_match(f"{family}:style=Bold" if weight == "bold" else f"{family}:style=Regular", "%{file}")


_fonts = {}


def estimate(family, weight, text, size, caps, tracking):
    from fontTools.ttLib import TTFont

    key = (family, weight)
    if key not in _fonts:
        f = TTFont(font_path(family, weight))
        _fonts[key] = (f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm, max(a for a, _ in f["hmtx"].metrics.values()))
    cmap, hmtx, upm, maxadv = _fonts[key]
    s = unicodedata.normalize("NFC", text.upper() if caps else text)
    missing = [ch for ch in s if ord(ch) not in cmap]
    total = sum(hmtx[cmap[ord(ch)]][0] if ord(ch) in cmap else maxadv for ch in s)
    return total * size / upm + tracking * size * len(s), s, missing


def style_run(p, family, size, bold, tracking):
    from pptx.util import Pt

    p.line_spacing = 1.0
    p.space_before = p.space_after = Pt(0)
    for r in p.runs:
        r.font.name = family
        r.font.size = Pt(size)
        r.font.bold = bold
        if tracking:
            r.font._rPr.set("spc", str(round(tracking * size * 100)))


def build_wrap(families):
    from pptx import Presentation
    from pptx.util import Inches

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    probes = []
    for family, _twin in families:
        for weight in WEIGHTS:
            for size in SIZES:
                for name, (text, caps, tracking) in STRINGS.items():
                    est, shown, missing = estimate(family, weight, text, size, caps, tracking)
                    for factor in FACTORS:
                        slide = prs.slides.add_slide(prs.slide_layouts[6])
                        tf = _box(slide, 36, 36, est * factor, 120)
                        tf.paragraphs[0].text = shown
                        style_run(tf.paragraphs[0], family, size, weight == "bold", tracking)
                        probes.append((family, weight, size, name, factor, bool(missing)))
    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue(), probes


def pack_sizes():
    data = tomllib.loads((ROOT / "src/keyline/packs/swiss/pack.toml").read_text())
    out = set()
    for mode, styles in data["styles"].items():
        for name, st in styles.items():
            out.add((float(st["size_pt"]), float(st.get("line_spacing", 1))))
    return sorted(out)


def build_pitch(families):
    from pptx import Presentation
    from pptx.util import Inches, Pt

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    probes = []
    for family, _twin in families:
        for size, ls in pack_sizes():
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            tf = _box(slide, 36, 36, 880, 500)
            tf.paragraphs[0].text = "\v".join(["Hxgh Ápq"] * 4)
            p = tf.paragraphs[0]
            for r in p.runs:
                r.font.name, r.font.size = family, Pt(size)
            p.line_spacing = ls
            p.space_before = p.space_after = Pt(0)
            probes.append((family, size, ls))
    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue(), probes


def main():
    families = load_config().portable_fonts
    soffice = find_soffice()
    version = libreoffice_version(soffice)
    print(f"# auditor stress, {version}")
    with tempfile.TemporaryDirectory(prefix="audit-stress-") as tmp:
        wrap_bytes, wrap_probes = build_wrap(families)
        (Path(tmp) / "wrap.pptx").write_bytes(wrap_bytes)
        (Path(tmp) / "w").mkdir()
        wpages = read_pages(convert_to_pdf(Path(tmp) / "wrap.pptx", soffice, Path(tmp) / "w"))
        pitch_bytes, pitch_probes = build_pitch(families)
        (Path(tmp) / "pitch.pptx").write_bytes(pitch_bytes)
        (Path(tmp) / "p").mkdir()
        ppages = read_pages(convert_to_pdf(Path(tmp) / "pitch.pptx", soffice, Path(tmp) / "p"))
    assert len(wpages) == len(wrap_probes) and len(ppages) == len(pitch_probes)

    # Part A
    by = {}
    for probe, (ys, _f, _h) in zip(wrap_probes, wpages, strict=True):
        family, weight, size, name, factor, missing = probe
        by.setdefault((family, weight, size, name, missing), []).append((factor, len(ys)))
    fails, thresholds = [], []
    for key, seq in by.items():
        fits = [f for f, n in seq if n == 1]
        thr = min(fits) if fits else None
        thresholds.append((thr if thr is not None else 9.9, key))
        at_margin = dict(seq)[1 / 0.99]
        if at_margin != 1:
            fails.append((key, at_margin, seq))
    print(f"\nA. wrap: {len(by)} (family, weight, size, string) cases, factors {', '.join(f'{f:.4f}' for f in FACTORS)}")
    print(f"   cases that WRAP at 1/0.99 = 1.0101 (estimator would accept, LibreOffice breaks): {len(fails)}")
    for key, n, seq in fails:
        print("   FAIL", key, "lines at 1.0101:", n, "seq:", [(round(f, 4), c) for f, c in seq])
    hist = {}
    for thr, key in thresholds:
        label = "<=0.995" if thr <= 0.995 else (">1.0101" if thr > 1.0102 else f"{thr:.4f}")
        hist[label] = hist.get(label, 0) + 1
    print("   smallest fitting factor, histogram:", dict(sorted(hist.items())))
    worst = sorted(thresholds, key=lambda t: -t[0])[:12]
    print("   worst cases (smallest fitting factor, largest first):")
    for thr, key in worst:
        print(f"     {thr:.4f}  {key}")
    by_str = {}
    for thr, key in thresholds:
        by_str.setdefault(key[3], []).append(thr)
    print("   per string, worst smallest-fitting factor:", {k: round(max(v), 4) for k, v in by_str.items()})
    by_size = {}
    for thr, key in thresholds:
        by_size.setdefault(key[2], []).append(thr)
    print("   per size, worst:", {k: round(max(v), 4) for k, v in sorted(by_size.items())})
    miss = sorted({(k[0], k[3]) for _t, k in thresholds if k[4]})
    print("   strings with glyphs missing from the twin (max advance used):", miss or "none")

    # Part B
    print("\nB. pitch at every Swiss (size, line_spacing), regular; ratio = measured / (size x 1.2 x ls)")
    worst_ratio, rows = 0.0, []
    firsts = []
    for (family, size, ls), (ys, _f, h) in zip(pitch_probes, ppages, strict=True):
        steps = [a - b for a, b in itertools.pairwise(ys)]
        pitch = sum(steps) / len(steps) if len(ys) == 4 else float("nan")
        ratio = pitch / (size * 1.2 * ls)
        first = (h - 36 - ys[0]) / size
        rows.append((family, size, ls, pitch, ratio, first, len(ys)))
        worst_ratio = max(worst_ratio, ratio)
        firsts.append(first)
    for fam in dict.fromkeys(r[0] for r in rows):
        rs = [r for r in rows if r[0] == fam]
        print(f"   {fam:<16} ratio {min(r[4] for r in rs):.4f} … {max(r[4] for r in rs):.4f}; first baseline {min(r[5] for r in rs):.3f} … {max(r[5] for r in rs):.3f} em; lines {set(r[6] for r in rs)}")
    print(f"   worst ratio overall: {worst_ratio:.4f}")
    for r in rows:
        if r[0] == "Arial":
            print(f"     Arial {r[1]:>5.0f} pt ls {r[2]:.1f}: pitch {r[3]:.3f} pt, ratio {r[4]:.4f}, first baseline {r[5]:.3f} em")


if __name__ == "__main__":
    main()
