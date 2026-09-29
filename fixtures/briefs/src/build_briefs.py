"""Write the brief fixtures: python fixtures/briefs/src/build_briefs.py

Each variant is valid.brief.toml (or an evidence file) with exactly one change, so each
fixture isolates one schema error or one finding (spec 002 AC-7, amendment B-8.4/B-8.5).
A change is (old, new) text that must occur exactly once. Also writes the one-mode pack
used by the B-4 fixture: the Swiss system with modes = ["presented"].
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SWISS = HERE.parents[1] / "src" / "keyline" / "packs" / "swiss" / "pack.toml"

EV = 'evidence = ["evidence.toml", "extra-evidence.toml"]'
VOICE_START = "[voice.fonts]"
VOICE_END = "[[slides]]"
OWN = (
    'own_world = ["chisels", "the lending shelf", "sawdust", "clean workbench", "membership cards"]'
)
LONG = 'headline = "Most returned tools need a repair before the next loan"'
CREAM = 'paper = "EEF0F2"'


def _voice_block(text: str) -> str:
    return text[text.index(VOICE_START) : text.index(VOICE_END)]


# name -> list of (old, new); "VOICE" as old means the whole inline voice block
BRIEFS: dict[str, list[tuple[str, str]]] = {
    # schema errors (exit 1): §4.3, B-4, B-8.4, B-8.5
    "bad-schema": [("schema = 1", "schema = 2")],
    "missing-key": [('thesis = "Repairs, not new tools, are what keep members coming back"\n', "")],
    "mistyped-key": [('reads = ["what the library is"]', 'reads = "what the library is"')],
    "unknown-role": [('role = "quote"', 'role = "interlude"')],
    "unknown-evidence-id": [('evidence = ["returns_repaired"]', 'evidence = ["returns_fixed"]')],
    "evidence-missing": [(EV, 'evidence = ["evidence.toml", "missing.toml"]')],
    "evidence-invalid": [(EV, 'evidence = ["evidence-no-product.toml"]')],
    "evidence-duplicate-id": [(EV, 'evidence = ["evidence.toml", "evidence-duplicate.toml"]')],
    "evidence-label-long": [(EV, 'evidence = ["evidence-long-label.toml"]')],
    "evidence-value-and-series": [(EV, 'evidence = ["evidence-value-and-series.toml"]')],
    "first-not-cover": [('role = "cover"', 'role = "statement"')],
    "two-covers": [('role = "close"', 'role = "cover"')],
    "own-world-short": [(OWN, 'own_world = ["chisels", "sawdust"]')],
    "own-world-long": [(OWN, OWN.replace('"membership cards"', '"cards", "a", "b", "c"'))],
    "evidence-on-section": [
        (
            'reads = ["the part of the talk that follows"]',
            'reads = ["the part of the talk that follows"]\nevidence = ["bench_hours"]',
        ),
    ],
    "evidence-on-quote": [
        (
            'reads = ["a member\'s words"]',
            'reads = ["a member\'s words"]\nevidence = ["bench_hours"]',
        ),
    ],
    "unknown-pack": [('pack = "swiss"', 'pack = "nordic"')],
    "mode-not-in-pack": [
        ('pack = "swiss"', 'pack = "packs/presented-only"'),
        ('mode = "presented"', 'mode = "read"'),
    ],
    "voice-missing": [("VOICE", "")],
    "voice-both": [('pack = "swiss"\n', 'pack = "swiss"\nvoice = "neutral"\n')],
    "voice-unknown-name": [("VOICE", ""), ('pack = "swiss"\n', 'pack = "swiss"\nvoice = "dusk"\n')],
    "voice-missing-role": [('hairline = "BFC5CC"\n', "")],
    "voice-extra-role": [('hairline = "BFC5CC"\n', 'hairline = "BFC5CC"\ngold = "D4A017"\n')],
    "voice-bad-hex": [('accent = "1F6F5C"', 'accent = "#1F6F5C"')],
    "voice-font-not-portable": [('display = "Cambria"', 'display = "Verdana"')],
    # findings (§4.3, B-8.5): positives and the negatives the valid brief does not cover
    "brief-reads--pos": [
        (
            'reads = ["the claim", "why it matters", "what we ask"]',
            'reads = ["the claim", "why it matters", "what we ask", "what happens next"]',
        ),
    ],
    "brief-mood--pos": [('"clean workbench"', '"Clean, modern!"')],
    "brief-notes--pos": [('notes = "Point at the number, not the chart."\n', "")],
    "brief-notes--neg-read": [
        ('mode = "presented"', 'mode = "read"'),
        ('notes = "Point at the number, not the chart."\n', ""),
    ],
    "brief-headline-long--pos": [(LONG, LONG.replace("a repair", "a small repair"))],
    "brief-no-statement--pos": [('role = "statement"', 'role = "evidence"')],
    "brief-no-statement--neg-read": [
        ('mode = "presented"', 'mode = "read"'),
        ('role = "statement"', 'role = "evidence"'),
    ],
    "voice-contrast--pos": [('muted = "4F5761"', 'muted = "9A9A98"')],
    "voice-claude-look--pos": [
        (CREAM, 'paper = "F4F3EE"'),
        ('accent = "1F6F5C"', 'accent = "A8502F"'),
    ],
    "voice-claude-look--cream-only": [(CREAM, 'paper = "F4F3EE"')],
    "voice-claude-look--accepted": [
        (CREAM, 'paper = "F4F3EE"'),
        ('accent = "1F6F5C"', 'accent = "A8502F"'),
        (
            VOICE_START,
            '[voice]\naccepted = [{ rule = "voice-claude-look", reason = "a pottery '
            "studio's own clay and kiln colours\" }]\n\n" + VOICE_START,
        ),
    ],
    "voice-why--pos": [('hairline = "a chalk line snapped across a board"\n', "")],
    "named-voice": [("VOICE", ""), ('pack = "swiss"\n', 'pack = "swiss"\nvoice = "night"\n')],
}

EVIDENCE: dict[str, list[tuple[str, str]]] = {
    "evidence-no-product": [
        ('[product]\nname = "Toolshed Commons"\nfictional = true\n', ""),
        (
            'disclosure = "Note: Toolshed Commons is fictional, and so is every number in this '
            'deck."\none_liner = "A neighbourhood tool library"   # unknown keys are ignored '
            "(§4.1)\n",
            "",
        ),
    ],
    "evidence-long-label": [
        ('label = "returns needing a repair"', 'label = "returns that needed a small repair"'),
    ],
    "evidence-value-and-series": [
        ('value = "62%"', 'value = "62%"\nseries = [["Q1", 1]]'),
    ],
}


def _apply(text: str, changes: list[tuple[str, str]]) -> str:
    for old, new in changes:
        if old == "VOICE":
            old = _voice_block(text)
        if text.count(old) != 1:
            raise SystemExit(f"change not unique: {old[:60]!r}")
        text = text.replace(old, new)
    return text


def build() -> list[Path]:
    written = []
    brief = (HERE / "valid.brief.toml").read_text(encoding="utf-8")
    header = brief.split("schema = 1", 1)[0]
    for name, changes in BRIEFS.items():
        body = _apply(brief, changes).replace(header, "", 1)
        path = HERE / f"{name}.brief.toml"
        path.write_text(f"# valid.brief.toml with one change: {name}\n" + body, encoding="utf-8")
        written.append(path)
    evidence = (HERE / "evidence.toml").read_text(encoding="utf-8")
    for name, changes in EVIDENCE.items():
        path = HERE / f"{name}.toml"
        path.write_text(_apply(evidence, changes), encoding="utf-8")
        written.append(path)
    extra = (HERE / "extra-evidence.toml").read_text(encoding="utf-8")
    dup = _apply(extra, [('id = "bench_hours"', 'id = "returns_repaired"')])
    (HERE / "evidence-duplicate.toml").write_text(dup, encoding="utf-8")
    written.append(HERE / "evidence-duplicate.toml")
    pack_dir = HERE / "packs" / "presented-only"
    pack_dir.mkdir(parents=True, exist_ok=True)
    system = SWISS.read_text(encoding="utf-8")
    one_mode = _apply(system, [('modes = ["presented", "read"]', 'modes = ["presented"]')])
    (pack_dir / "pack.toml").write_text(one_mode, encoding="utf-8")
    written.append(pack_dir / "pack.toml")
    return written


if __name__ == "__main__":
    for p in build():
        print(p.relative_to(HERE))
    sys.exit(0)
