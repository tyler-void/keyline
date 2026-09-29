"""The validate step of `keyline check` (spec 002 §7, D-015): `officecli validate --json`,
each schema error as one `ooxml-invalid` finding. OfficeCLI is optional; without it the
step is skipped and says so. `lint` never runs this (requires = "officecli", plan Q-12).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from keyline.findings import Finding
from keyline.registry import RuleSpec, register

TIMEOUT_S = 120

OOXML_INVALID = register(
    RuleSpec(
        id="ooxml-invalid",
        category="quality",
        severity="warning",
        scope="slide",
        basis="structure",
        requires="officecli",
        since="0.2.0",
        summary="officecli validate reports a schema error in the package",
        rationale="L-014",
    )
)


def _run(cmd: list[str], timeout: float) -> subprocess.CompletedProcess:
    from keyline import _proc

    return _proc.run(cmd, timeout)


def available() -> bool:
    from keyline.officecli import status

    return status()[0]


def validate(deck: str | Path) -> list[Finding]:
    """Run `officecli validate DECK --json`; one finding per schema error, or one carrying
    the first line of output that cannot be read. Assumes `available()`."""
    from keyline.officecli import private_copy

    deck = Path(deck)
    with private_copy(deck) as copy:  # B-14: never the user's path (L-016)
        cmd = [shutil.which("officecli"), "validate", str(copy), "--json"]
        try:
            proc = _run(cmd, TIMEOUT_S)  # B-19: its own process group, killed whole
        except subprocess.TimeoutExpired:
            message = f"officecli validate timed out after {TIMEOUT_S} s"
            return [OOXML_INVALID.finding(0, None, message)]
        copy_name = copy.name
    errors = parse(proc.stdout)
    if errors is None:
        first = (proc.stdout or proc.stderr).strip().splitlines()
        line = first[0] if first else f"exit {proc.returncode}"
        return [OOXML_INVALID.finding(0, None, f"officecli validate output not understood: {line}")]
    order = _slide_order(deck)
    return [
        OOXML_INVALID.finding(
            order.get(part, 0),
            None,
            (f"{part} {path}: {text}" if part or path else text).replace(copy_name, deck.name),
        )
        for text, path, part in errors
    ]


def parse(stdout: str) -> list[tuple[str, str, str]] | None:
    """(message, path, part) per error, [] for a valid deck, None when unreadable.

    OfficeCLI 1.0.152 writes {"success": true, ...} for a valid deck, else {"success":
    false, "warnings": [...]}: a "Found N validation error(s):" header, then three entries
    per error: the message, "Path: …", "Part: …". A deck it cannot open gives the error
    envelope {"success": false, "error": {"error": "…", …}}: one error (B-15)."""
    try:
        data = json.loads(stdout)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("success"), bool):
        return None
    if data["success"]:
        return []
    envelope = data.get("error")
    if isinstance(envelope, dict) and isinstance(envelope.get("error"), str):
        return [(envelope["error"], "", "")]
    entries = data.get("warnings")
    if not isinstance(entries, list):
        return None
    errors: list[list[str]] = []
    for entry in entries:
        text = entry.get("message", "") if isinstance(entry, dict) else ""
        if not isinstance(text, str) or text.startswith("Found "):
            continue
        if text.startswith("Path: ") and errors:
            errors[-1][1] = text[len("Path: ") :]
        elif text.startswith("Part: ") and errors:
            errors[-1][2] = text[len("Part: ") :]
        elif text:
            errors.append([text, "", ""])
    return [tuple(e) for e in errors] or None


def _slide_order(deck: Path) -> dict[str, int]:
    """Part name ("/ppt/slides/slide3.xml") -> the slide's 1-based position in the deck,
    so a finding points at the same slide as lint's findings do."""
    from keyline.ooxml.ns import NS, q
    from keyline.ooxml.package import Package, ScanError

    try:
        with Package(deck) as pkg:
            rels = pkg.rels(pkg.main_part)
            ids = pkg.xml(pkg.main_part).findall("p:sldIdLst/p:sldId", NS)
            targets = [rels.get(sld.get(q("r:id")) or "") for sld in ids]
            return {f"/{r.target}": i for i, r in enumerate(targets, 1) if r is not None}
    except ScanError:
        return {}
