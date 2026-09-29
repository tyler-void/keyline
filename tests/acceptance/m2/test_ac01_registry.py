"""Spec 002 AC-1 as amended by B-8.6: `keyline rules --json` lists 35 entries, each with
`requires`, and the M1 entries keep their ids, severities, categories and bases."""

import json

from tests.acceptance._cli import keyline

# (severity, category, basis) of the 13 spec 001 entries, as main (678c69a) lists them
M1 = {
    "adapter-unresolved": ("advisory", "quality", "structure"),
    "body-too-small": ("warning", "quality", "text"),
    "box-overlap": ("advisory", "quality", "geometry"),
    "dead-band": ("warning", "quality", "geometry"),
    "edge-margin": ("warning", "quality", "geometry"),
    "equal-card-row": ("warning", "slop", "geometry"),
    "font-count": ("warning", "quality", "text"),
    "notes-missing": ("warning", "quality", "structure"),
    "off-slide": ("error", "quality", "geometry"),
    "text-contrast": ("warning", "quality", "color"),
    "title-not-dominant": ("warning", "quality", "text"),
    "title-underline": ("warning", "slop", "geometry"),
    "unsupported-content": ("advisory", "quality", "structure"),
}
SECTION_3_4 = {
    "claude-look-palette": "none",
    "title-too-long": "none",
    "closing-cliche": "none",
    "off-palette-color": "pack",
    "off-scale-size": "pack",
    "off-pack-font": "pack",
    "accent-overuse": "pack",
}
SECTION_4 = {
    "brief-reads",
    "brief-mood",
    "brief-notes",
    "brief-headline-long",
    "brief-no-statement",
    "brief-slide-count",
    "brief-role",
    "brief-headline",
    "unsourced-number",
    "source-missing",
    "fiction-undisclosed",
}
VOICE = {"voice-contrast", "voice-claude-look", "voice-why"}  # B-8.5


def test_35_entries_each_with_requires():
    proc = keyline("rules", "--json")
    assert proc.returncode == 0
    rules = {r["id"]: r for r in json.loads(proc.stdout)}
    assert len(rules) == 35 == 13 + 1 + 7 + 11 + 3
    assert set(rules) == set(M1) | {"ooxml-invalid"} | set(SECTION_3_4) | SECTION_4 | VOICE
    assert all("requires" in r for r in rules.values())
    for rule_id, fields in M1.items():
        r = rules[rule_id]
        assert (r["severity"], r["category"], r["basis"]) == fields, rule_id
        assert (r["requires"], r["since"]) == ("none", "0.1.0")
    assert rules["ooxml-invalid"]["requires"] == "officecli"
    for rule_id, requires in SECTION_3_4.items():
        assert rules[rule_id]["requires"] == requires and rules[rule_id]["since"] == "0.2.0"
    for rule_id in SECTION_4 | VOICE:
        assert rules[rule_id]["requires"] == "brief" and rules[rule_id]["since"] == "0.2.0"
    for rule_id in VOICE:
        r = rules[rule_id]
        want = "structure" if rule_id == "voice-why" else "color"
        assert (r["category"], r["scope"], r["basis"]) == ("quality", "deck", want)
