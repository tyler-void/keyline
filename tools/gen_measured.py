"""Write the measured data the estimator reads, from committed tools/measure_lo.py outputs
(amendment B-27, items 3 and 5):

    python tools/gen_measured.py [OUT_DIR]

Dev only, but it needs neither LibreOffice nor fonts: it only reads the outputs listed in
SOURCES, one per LibreOffice version and environment measured.

`breaks.json` (item 3): the characters LibreOffice will not break before, after a space,
and the characters it will not break after, before a space. Each output with the full
probe ("line breaks at a space") gives its version's two sets, as measured. An output
that predates the full probe gives no entry (plan Q-60: 26.8.0.3 can no longer be
measured on Tyler's machine, and 26.8.1.1 supersedes it there). The estimator uses the
union over the versions.

`environments.json` (item 5): each environment measured (who ran it, the LibreOffice
version, the platform, the fallback fonts fontconfig picked there with their hhea line
heights, and the widest fallback advance, fallback cell line and cell-line excess it
measured), and the three thresholds that follow from them, each the largest value over
the environments, rounded up to 0.01:
- `missing_glyph_em`: the widest fallback advance;
- `missing_line_em`: the widest fallback cell line, or a fallback font's hhea line height
  where that is larger (24.2.7.2 sets a cell line at max(1.2, the hhea of its font));
- `cell_line_allowance_mm`: the largest excess per cell line (B-25 item 6).
thresholds.toml holds the same three values, and a test compares them.

Output is byte-stable: the same outputs give the same bytes.
"""

from __future__ import annotations

import json
import re
import sys
from decimal import ROUND_CEILING, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# not imported from keyline.fit: that package reads the data this tool writes
TABLES = ROOT / "src" / "keyline" / "fit" / "tables"
EVIDENCE = ROOT / "specs" / "002-skill-pack" / "evidence"
SOURCES = (  # who ran it, the measure_lo output
    ("Tyler", EVIDENCE / "lo-26.8.0.3-measurements.txt"),  # predates the full probe
    ("Tyler", EVIDENCE / "lo-26.8.1.1-measurements.txt"),
    ("the auditor", EVIDENCE / "lo-24.2.7.2-measurements.txt"),
)
BREAK_LINE = re.compile(r"^  no break (before|after) \((\d+)\):(.*)$", re.MULTILINE)
BREAKS, ENVIRONMENTS = "breaks.json", "environments.json"


def version_of(text: str) -> str:
    return re.search(r"^version: (.+)$", text, re.MULTILINE)[1]


def measured_breaks(text: str) -> dict[str, list[int]] | None:
    """The two sets of an output's full probe (B-27 item 3), or None for an output that
    predates it."""
    found = {}
    for side, count, rest in BREAK_LINE.findall(text):
        found[side] = sorted(int(cp[2:], 16) for cp in rest.split())
        if len(found[side]) != int(count):
            raise SystemExit(f"gen_measured: the no-break-{side} line does not hold {count}")
    if not found:
        return None
    if set(found) != {"before", "after"}:
        raise SystemExit("gen_measured: an output has only one of the two no-break lines")
    return found


def breaks() -> str:
    """breaks.json: the two sets of every version with the full probe, and their union."""
    versions = []
    for _who, path in SOURCES:
        text = path.read_text(encoding="utf-8")
        sets = measured_breaks(text)
        if sets is not None:
            versions.append(
                {
                    "version": version_of(text),
                    "source": path.relative_to(ROOT).as_posix(),
                    "no_break_before": sets["before"],
                    "no_break_after": sets["after"],
                }
            )
    if not versions:
        raise SystemExit("gen_measured: no output has the full probe of B-27 item 3")
    data = {
        "schema": 1,
        "rule": (
            "B-27 item 3: after a space, no line breaks before the characters of "
            "no_break_before; before a space, none breaks after those of no_break_after. "
            "Each is the union over the LibreOffice versions measured"
        ),
        "versions": versions,
        "no_break_before": sorted({cp for v in versions for cp in v["no_break_before"]}),
        "no_break_after": sorted({cp for v in versions for cp in v["no_break_after"]}),
    }
    return json.dumps(data, ensure_ascii=True, indent=1) + "\n"


def _one(pattern: str, text: str) -> re.Match:
    found = re.search(pattern, text, re.MULTILINE)
    if found is None:
        raise SystemExit(f"gen_measured: an output has no line matching {pattern!r}")
    return found


def environment(who: str, path: Path) -> dict:
    """What one measure_lo output says about its environment (B-27 item 5)."""
    text = path.read_text(encoding="utf-8")
    date, platform = _one(r"^date: (\S+)  keyline \S+  (\S+)$", text).groups()
    fonts = {}
    for item in _one(r"^  fallback fonts \(.*?\): (.+)$", text)[1].split(", "):
        script, file, em, _unit = item.split()
        fonts[script] = {"file": file, "hhea_line_em": em}
    return {
        "who": who,
        "source": path.relative_to(ROOT).as_posix(),
        "version": version_of(text),
        "date": date,
        "platform": platform,
        "fallback_fonts": fonts,
        "widest_fallback_advance_em": _one(r"^  widest fallback advance: (\S+) em$", text)[1],
        "widest_fallback_cell_line_em": _one(r"^  widest fallback cell line: (\S+) em$", text)[1],
        "cell_line_excess_mm": _one(r"^  largest excess per cell line: \S+ pt = (\S+) mm", text)[1],
    }


def _ceil(values) -> str:
    """The largest value, rounded up to 0.01."""
    return str(max(map(Decimal, values)).quantize(Decimal("0.01"), rounding=ROUND_CEILING))


def environments() -> str:
    """environments.json: every environment measured, and the thresholds they give."""
    found = [environment(who, path) for who, path in SOURCES]
    lines = [e["widest_fallback_cell_line_em"] for e in found]
    lines += [f["hhea_line_em"] for e in found for f in e["fallback_fonts"].values()]
    data = {
        "schema": 1,
        "rule": (
            "B-27 item 5: missing_glyph_em and missing_line_em take the largest value "
            "measured in any environment Tyler or the auditor has run; "
            "cell_line_allowance_mm likewise (B-25 item 6)"
        ),
        "environments": found,
        "missing_glyph_em": _ceil(e["widest_fallback_advance_em"] for e in found),
        "missing_line_em": _ceil(lines),
        "cell_line_allowance_mm": _ceil(e["cell_line_excess_mm"] for e in found),
    }
    return json.dumps(data, ensure_ascii=True, indent=1) + "\n"


def build(out_dir: Path = TABLES) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, text in ((BREAKS, breaks()), (ENVIRONMENTS, environments())):
        path = out_dir / name
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written


if __name__ == "__main__":
    for p in build(Path(sys.argv[1]) if len(sys.argv) > 1 else TABLES):
        print(p)
