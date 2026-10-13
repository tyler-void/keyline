"""Write the measured data the estimator reads, from committed tools/measure_lo.py outputs
(amendment B-27 item 3):

    python tools/gen_measured.py [OUT_DIR]

Dev only, but it needs neither LibreOffice nor fonts: it only reads the outputs listed in
SOURCES, one per LibreOffice version and environment measured.

`breaks.json` (item 3): the characters LibreOffice will not break before, after a space,
and the characters it will not break after, before a space. Per version:
- an output with the full probe ("line breaks at a space") gives its two sets as measured;
- an output that predates the full probe gives B-22 item 4's and B-25 item 5's lists, as
  they stood on that version (LISTED), plus what an audit found there (REPORTED). It
  stays so until the full probe has run on that version.
The estimator uses the union over the versions.

Output is byte-stable: the same outputs give the same bytes.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# not imported from keyline.fit: that package reads the data this tool writes
TABLES = ROOT / "src" / "keyline" / "fit" / "tables"
EVIDENCE = ROOT / "specs" / "002-skill-pack" / "evidence"
SOURCES = (  # who ran it, the measure_lo output
    ("Tyler", EVIDENCE / "lo-26.8.0.3-measurements.txt"),
    ("Tyler", EVIDENCE / "lo-26.8.1.1-measurements.txt"),
    ("the auditor", EVIDENCE / "audit07-repros" / "measure_lo-on-24.2.7.2.txt"),
)
# B-22 item 4 (no break before) and B-25 item 5 (no break after an opening punctuation
# mark: category Ps, and the inverted ! and ?), inside the measured set, as listed before
# B-27. Before: ) ] } , . : ; ! ? / % and U+2030, U+00BB, U+201D, U+2019. After: ( [ {
# and U+201A, U+201E, U+2045, U+00A1, U+00BF.
LISTED = {
    "before": [
        *(0x29, 0x5D, 0x7D, 0x2C, 0x2E, 0x3A, 0x3B, 0x21, 0x3F, 0x2F, 0x25),
        *(0x2030, 0xBB, 0x201D, 0x2019),
    ],
    "after": [0x28, 0x5B, 0x7B, 0x201A, 0x201E, 0x2045, 0xA1, 0xBF],
}
# What an audit found on a version whose output predates the full probe.
REPORTED = {
    "LibreOffice 24.2.7.2 420(Build:2)": {
        "before": [0x5C, 0x2044],  # audit 07 FX-33: f2_backslash.py, probe_b.py
        "after": [],
        "note": "audit 07 FX-33 found no break before U+005C and U+2044 there",
    },
}
BREAK_LINE = re.compile(r"^  no break (before|after) \((\d+)\):(.*)$", re.MULTILINE)
BREAKS = "breaks.json"


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
    """breaks.json: the sets per version, and their union."""
    versions = []
    for _who, path in SOURCES:
        text = path.read_text(encoding="utf-8")
        version = version_of(text)
        sets = measured_breaks(text)
        entry = {"version": version, "source": path.relative_to(ROOT).as_posix()}
        if sets is not None:
            entry["probe"] = "full"
        else:
            reported = REPORTED.get(version, {"before": [], "after": [], "note": ""})
            sets = {side: sorted({*LISTED[side], *reported[side]}) for side in ("before", "after")}
            entry["probe"] = (
                "listed: this output predates the full probe, so these are B-22 item 4's and "
                "B-25 item 5's lists" + (f"; {reported['note']}" if reported["note"] else "")
            )
        entry["no_break_before"], entry["no_break_after"] = sets["before"], sets["after"]
        versions.append(entry)
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


def build(out_dir: Path = TABLES) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, text in ((BREAKS, breaks()),):
        path = out_dir / name
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written


if __name__ == "__main__":
    for p in build(Path(sys.argv[1]) if len(sys.argv) > 1 else TABLES):
        print(p)
