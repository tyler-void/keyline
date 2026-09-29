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
- Spec 002, phase A2 (M2):
  - Fit tables for each portable font's metric twin, regular and bold, and the fit
    estimator (§6.4 with B-21): wrap at 0.99 × the width, 1.2 em line pitch plus
    0.01 mm per line, and a warning for characters a twin lacks.
  - The pen (`keyline.pen`): `Deck`, `Deck.from_brief`, and the verbs `text`,
    `bullets`, `figure`, `table`, `chart_bar`, `image`, `attribution`, `source`,
    `note` and `notes`. Tokens only; text that does not fit raises `DoesNotFit`;
    byte-identical output, charts included.
  - Swiss specimens in `neutral`, `night` and `field`, the AC-8 drift decks rebuilt
    with the pen, and `tools/measure_lo.py` and `tools/fit_stress.py` for the
    LibreOffice measurements.
