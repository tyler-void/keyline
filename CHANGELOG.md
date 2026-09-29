# Changelog

All notable changes are recorded here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Bootstrap: constitution, vision, decisions, lessons learned, research notes (2026-09).
- Spec 001 (lint core) with acceptance criteria.
- Golden fixtures `kpi-recipe.pptx` and `editorial.pptx`, with their build scripts.
- Research prototype `prototype/deck_lint_v0.py` (reference only).
- Python package skeleton (`keyline` console script, Python >= 3.11) and CI on 3.11 and 3.13.
- Spec 001, lint core (M1): 11 rules and 2 adapter ids, `lint`, `rules`, `render` and
  `check`, golden and rule fixtures.
- Spec 002, phase A1 (M2):
  - Slide roles from `keyline:<role>` layout names; source and note lines (§3.1).
  - Rules `claude-look-palette`, `title-too-long` and `closing-cliche`, and the pack
    rules `off-palette-color`, `off-scale-size`, `off-pack-font` and `accent-overuse`.
  - Packs as one system plus voices (amendment B-8, D-020): the Swiss system, the
    `neutral`, `night` and `field` voices, templates built per voice and mode, and
    `keyline packs`.
  - Briefs and evidence (`keyline brief`), with the brief's voice and its checks
    (`voice-contrast`, `voice-claude-look`, `voice-why`); deck-vs-brief rules with
    `--brief`; `--pack` and `--voice`.
  - Numeric tokens (§4.4) and table text.
  - A LibreOffice render engine (`--engine auto|libreoffice|officecli`), the
    `officecli validate` step in `check` (`ooxml-invalid`), and `keyline doctor`.
