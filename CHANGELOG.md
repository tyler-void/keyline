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
- Spec 002, A2 fixes (audit 05):
  - One text normalization for the estimator and the writer; controls, stray line
    breaks and invisible characters refused at the verb; no line break before closing
    punctuation.
  - Table cells at max(1.2, the twin's hhea) plus 0.01 mm per row; a missing glyph at
    `missing_glyph_em` (1.49) at least; room kept for the twin's descent under a
    region's last line.
  - The pen: images read once (PNG, JPEG, GIF, BMP, TIFF), an atomic `save()` that
    raises only `PenError`, refused verbs that change nothing, captions-only styles
    below the body minimum, the footer for source and note lines only.
  - A vertical anchor per region: the cover, evidence and close titles sit on the rule
    or the lede.
  - AC-13(b) as amended by B-24, over all six portable families.
- Spec 002, A2 fixes round 2 (audit 06):
  - B-25's measured set: one definition for the fit's guarantees, and one warning per
    deck for what it does not cover.
  - The estimator counts positive kerning pairs and keeps opening punctuation with the
    next word. It takes measured table-cell data per LibreOffice version.
  - Complex scripts are set in the voice's family.
  - Chart series are checked at the verb, and text with no visible character is
    refused.
  - AC-13(b)'s top allowance for stacked capitals, with Vietnamese in the fit stress.
  - B-26's numeral set, derived from the twins and the pack: a figure's value refuses
    the characters that would reach past its region.
