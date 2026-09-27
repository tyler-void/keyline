"""Capture or check the M1 baseline: lint output of every spec 001 rule fixture, foreign
deck and stress deck, in both modes (spec 002 plan §2.12, T-01; AC-2).

    python tools/m1_baseline.py --write    # capture (only on spec 001 code, before T-03)
    python tools/m1_baseline.py            # compare; exit 1 on any difference

Each deck and mode gets `<name>.<mode>.json`: exactly what `keyline lint --json` writes
to stdout (empty when the deck cannot be scanned). `manifest.json` records the exit code
and, for scan failures, the one-line reason.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "fixtures" / "expected" / "m1-baseline"
GROUPS = {
    "rules": sorted((ROOT / "fixtures" / "rules").glob("*.pptx")),
    "foreign": sorted((ROOT / "fixtures" / "foreign").glob("*.pptx")),
    "stress": sorted((ROOT / "fixtures" / "foreign" / "stress").glob("*.pptx")),
}
MODES = ("presented", "read")


def run(deck: Path, mode: str) -> tuple[str, int, str | None]:
    from keyline.findings import to_json
    from keyline.lint import lint_path
    from keyline.ooxml.package import ScanError

    try:
        result = lint_path(deck, mode)
    except ScanError as exc:
        return "", 1, str(exc)
    return to_json(result.findings), result.exit_code, None


def capture() -> dict:
    outputs, manifest = {}, {}
    for group, decks in GROUPS.items():
        for deck in decks:
            for mode in MODES:
                key = f"{group}/{deck.stem}.{mode}"
                stdout, code, reason = run(deck, mode)
                outputs[key] = stdout
                manifest[key] = (
                    {"exit": code} if reason is None else {"exit": code, "reason": reason}
                )
    return {"outputs": outputs, "manifest": manifest}


def write() -> None:
    data = capture()
    for key, stdout in data["outputs"].items():
        path = OUT / f"{key}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(stdout, encoding="utf-8")
    (OUT / "manifest.json").write_text(
        json.dumps(data["manifest"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(data['outputs'])} outputs to {OUT.relative_to(ROOT)}")


DIRS = {
    "rules": ROOT / "fixtures" / "rules",
    "foreign": ROOT / "fixtures" / "foreign",
    "stress": ROOT / "fixtures" / "foreign" / "stress",
}


def manifest() -> dict:
    return json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))


def diff() -> list[str]:
    """Compare the decks named in the manifest (the M1 set, frozen at capture), so decks
    added by spec 002 never count as differences."""
    changed = []
    for key, expected in sorted(manifest().items()):
        group, rest = key.split("/", 1)
        stem, mode = rest.rsplit(".", 1)
        deck = DIRS[group] / f"{stem}.pptx"
        if not deck.exists():
            changed.append(f"{key} (deck missing)")
            continue
        stdout, code, reason = run(deck, mode)
        got = {"exit": code} if reason is None else {"exit": code, "reason": reason}
        if stdout != (OUT / f"{key}.json").read_text(encoding="utf-8") or got != expected:
            changed.append(key)
    return changed


if __name__ == "__main__":
    if "--write" in sys.argv[1:]:
        write()
    else:
        changes = diff()
        print("\n".join(changes) if changes else "baseline: no differences")
        sys.exit(1 if changes else 0)
