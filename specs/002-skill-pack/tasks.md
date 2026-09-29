# Tasks 002: skill, brief and the Swiss pack

Order is the build order. Each task lands as its own commit(s), with its tests, on
`002-skill-pack`, and is pushed. "Done when" names the check an auditor can re-run.
Tasks marked ⚑ depend on an open question in [`plan.md`](plan.md) §9 and follow its
proposal unless Tyler rules otherwise. ruff fixes and formatting run only on
`src tests fixtures tools`. Spec 002's acceptance tests live in `tests/acceptance/m2/`,
because spec 001's `test_acNN_*.py` files keep their names and spec 002 restarts at
AC-1.

**Amendment B-8** (systems and voices, 2026-09-29) arrived after T-01 … T-09 part 2 had
landed (`b35ff05`). T-08 and T-09 get a rework commit each; T-10, T-12, T-17 and T-18
are adjusted below; the new questions are plan Q-26 … Q-41.

## Phase A1: lint and data

### Groundwork

| id | task | done when |
|---|---|---|
| T-01 | ⚑ **Baseline.** Before any lint code changes, capture the lint JSON of every M1 rule fixture, foreign deck and stress deck in both modes under `fixtures/expected/m1-baseline/`, with a test that compares current output to it (golden/rule/foreign: byte-identical; stress: identical or listed) (Q-5) | `tests/acceptance/test_m1_baseline.py` passes on the unchanged code |
| T-02 | **Dependencies and CI.** Extras `pen`, `render`; `dev` gains `pypdfium2`, `fontTools`; package data for packs and fit tables; CI installs `fonts-liberation` | CI green on 3.11 and 3.13; `pip install -e .[dev]` works |
| T-03 | ⚑ **Registry and context.** `requires` field (M1 entries `none`), `LintContext`, `check(deck, cfg, ctx)` with the two-argument adapter, runner skips unmet `requires`, `rules` listing shows `requires` (Q-12) | `tests/unit/test_registry.py`; spec 001's AC-14 injection test passes unchanged |
| T-04 | **Config schema.** Typed keys (numbers, lists of strings), the §3.2 per-mode and common keys in `thresholds.toml`, loud failures on unknown keys or wrong types | `tests/unit/test_config.py` extended; every M1 config test unchanged |

### Lint 0.2

| id | task | done when |
|---|---|---|
| T-05 | ⚑ **Roles (§2).** `roles.py`, `Slide.role`/`variant` from the layout name, role-aware `is_content_slide`, `dead-band` and `notes-missing` changes; AC-5 deck (Q-8, Q-9) | `test_ac05_roles.py` |
| T-06 | ⚑ **Source and note lines (§3.1)** in `body-too-small`; AC-6 decks (Q-7) | `test_ac06_source_lines.py` |
| T-07 | ⚑ **Colour spaces and pack-free rules (§3.3, §3.4).** `colorspace.py` with the eight anchors; `claude-look-palette`, `title-too-long`, `closing-cliche` with `--pos`/`--neg` fixtures; AC-4's four anchor decks (Q-25) | `tests/unit/test_colorspace.py`, rule-fixture cases, `test_ac04_claude_look.py` |

### Pack

| id | task | done when |
|---|---|---|
| T-08 | ⚑ **Pack format and Swiss data (§5.1, §5.2, §5.4).** `packs/__init__.py` (load by name or directory, validate, list), `packs/swiss/pack.toml` (palette, surfaces, grid, styles, roles, regions) and `README.md`, `keyline packs [--json]`; the seven §5.4 invariants as tests for both modes (Q-10, Q-20). *Landed at `ea659b7`.* | `tests/unit/test_packs.py`, `test_ac09_pack_invariants.py` |
| T-08r | ⚑ **B-8 rework: system and voices.** Move `[palette]` and `fonts` from `pack.toml` into `voices/neutral.toml`; add `palette_roles` and a `font` per style (Q-27); drop `templates` (Q-26); add `voices/night.toml` and `voices/field.toml` with B-8.10's values; `portable_fonts` in `thresholds.toml` (Q-38); `packs/voices.py` loads and validates a voice (the B-8.5 schema errors, Q-30, Q-32) and computes the three checks (Q-28); `keyline packs` lists voices (Q-39); README (Q-37); invariants 4 and 6 per voice, 5 on `neutral` only, 1, 2, 3, 7 on the system; every B-8.10 check number asserted | `tests/unit/test_packs.py`, `tests/unit/test_voices.py`, `test_ac09_pack_invariants.py` |
| T-09 | ⚑ **Templates (§5.3).** `zipnorm.py`; `packs/swiss/src/build_templates.py` (raw OOXML); `swiss-presented.pptx`, `swiss-read.pptx`; constraint tests via the M1 adapter; rebuild byte-identical (Q-17, Q-21). *Landed at `4da8304` and `b35ff05`.* | `test_ac09_templates.py`; `officecli validate` 0 errors on both templates (skips without OfficeCLI) |
| T-09r | ⚑ **B-8 rework: templates per voice.** `templates.build(pack, voice, mode)`; theme colours from the voice, major = display, minor = text, `lstStyle` fonts by style (Q-27, Q-33); commit only `swiss-neutral-{presented,read}.pptx` (Q-26); the constraint tests run on the committed neutral pair and on in-memory builds of every stock voice | `test_ac09_templates.py` (neutral rebuilt byte-identically; every voice × mode meets §5.3); `officecli validate` 0 errors on every build (skips without OfficeCLI) |
| T-10 | ⚑ **Pack rules (§3.4, B-8.8).** `off-palette-color`, `off-scale-size`, `off-pack-font`, `accent-overuse`, resolving the voice's palette, fonts and accent values; `--pack NAME\|DIR` and `--voice NAME\|FILE` (Q-35); `--pack` without a voice is exit 1; `accepted` downgrade from pack and voice (Q-24, Q-31); `--pos`/`--neg` fixtures from the Swiss template with `pack = "swiss"` and `voice` in `expect.toml` (Q-36), including one case in a non-neutral voice | AC-3 cases pass; the fixture harness passes `pack`/`voice`/`brief` to lint |

### Brief and evidence

| id | task | done when |
|---|---|---|
| T-11 | ⚑ **Numeric tokens (§4.4).** `numtokens.py` (Q-19); `Shape.table_text` in the adapter; equality with the auditor's oracle on the anchors, `product.toml` strings and a seeded 5,000-string corpus; the Q-6 limits pinned as tests | `tests/unit/test_numtokens.py` |
| T-12 | ⚑ **Evidence and brief schema, `keyline brief` (§4.1–§4.3, B-8.4, B-8.5).** `brief.py`, the five §4.3 findings as registry entries (Q-2, Q-3, Q-14, Q-23); the brief's voice (`voice = NAME` or inline `[voice]`, exactly one), the voice schema errors, and `voice-contrast`, `voice-claude-look`, `voice-why` as registry entries (Q-29 … Q-32); `fixtures/briefs/` with one file per schema error and `--pos`/`--neg` per finding, voice ids included | `test_ac07_brief.py`, `test_ac07_voice.py` |
| T-13 | ⚑ **Deck vs brief (§4.5) and CLI resolution (§3.5).** `briefcheck.py`, the six §4.5 registry entries, `--brief` on `lint`/`check`, `--mode` default `None`, conflict errors (Q-13) | `tests/unit/test_briefcheck.py`, `tests/acceptance/test_cli_resolution.py` |
| T-14 | ⚑ **AC-8 drift decks.** `fixtures/briefs/src/build_drift.py` builds the base deck from the Swiss template (pen-like output) and the six drifted copies (Q-4) | `test_ac08_drift.py`: base exits 0; each drift gives exactly its one finding |

### Render, validate, doctor

| id | task | done when |
|---|---|---|
| T-15 | ⚑ **Render engines (§7).** `libreoffice` (private profile, `--outdir`, 120 s, pypdfium2 or pdftoppm, 1280 px), `auto`, `--engine`, known limits per engine; the no-engine message keeps the M1 substrings (Q-11, Q-18); `--engine officecli` on the M1 `officecli` tests (AC-2's allowed change) | `test_ac14_render_engines.py` (skips without LibreOffice); M1 `test_ac10_render.py` passes |
| T-16 | **Validate step (§7).** `officecli validate --json` parsing, `ooxml-invalid`, `--no-validate`, the skipped message; `fixtures/validate/editorial-bogus.pptx` built by a committed script | `test_ac14b_validate.py` (skips without OfficeCLI) |
| T-17 | ⚑ **doctor (§7, B-8.12).** All nine checks and tokens, install hints, exit rule, `--json`; the font check per `portable_fonts` family (`FONT_OK` on the family or its twin, else `FONT_SUBSTITUTED`); the `NO_PPTX` path tested in a venv without python-pptx (Q-22, Q-40, Q-41); CI installs `fonts-crosextra-carlito` and `fonts-crosextra-caladea` | `test_ac16_doctor.py` |

### Acceptance and report

| id | task | done when |
|---|---|---|
| T-18 | ⚑ **A1 acceptance sweep.** AC-1 (**35** entries: 32 + 3 voice ids, B-8.6), AC-2 (baseline identity; the stress re-lint table; the list of M1 test changes; `test_rules_listing` accepts the same 35), an import-boundary test (lint never imports `pptx`, `pypdfium2`, `keyline.pen`, `keyline.render`); README, `docs/adapter.md` (roles, table text), CHANGELOG | every A1 AC test green locally; CI green |
| T-19 | **Report A1** in `report.md`: each A1 AC (AC-1 … AC-9, AC-14, AC-14b, AC-16) with command, output excerpt and PASS/FAIL; for B-8: the three stock voices' checks with the computed numbers, the neutral templates rebuilt byte-identically, the 35 registry entries, and which fit-table twins are present here; Deviations; Open questions. Then **stop** for the A1 audit (Q-15) | review by Tyler; audit by the external session |

## Phase A2: pen

Written after audit 02 (FIX, then A2), from plan §3 and the audit's "Carry into A2". The
metric twins of all six portable families are installed on Tyler's machine (Q-41;
`report.md`, A1 fixes). Audit 03 ruled Q-42 … Q-46 and adjusted T-20 … T-28; a second fix round (FX-9 …
FX-15, B-16 … B-20) lands first, as "A1 fixes, round 2".

### Measure first

| id | task | done when |
|---|---|---|
| T-20 | ⚑ **B-7 measurement on LibreOffice 26.8.0.3** (Q-44, audit 03). `tools/measure_lo.py` (dev only) builds probe decks with python-pptx and converts them with the same soffice command as the render engine. The probes name the **portable family** (Arial, Georgia, …), not the twin, so fontconfig substitutes as it does for a pen deck; the script prints `fc-match <family>` for each family and **stops if any does not resolve to its twin**. It reads glyph positions from the PDF with pypdfium2 and measures: line pitch as a multiple of size at 13, 24, 48 and 60 pt, regular and bold, for each of the six families; and the wrap margin, as the line count of a bold 14 pt label in a box 1.000×, 1.002×, 1.005× and 1.010× its advance sum (fontTools). It prints a table headed by the actual `soffice --version` (if not 26.8.0.3, it says so), and the output goes into report A2 against §6.4's 24.2 values (1.2 em; wraps at 1.000× and 1.002×, not at 1.005×). Every measured constant is stored with the LibreOffice version that produced it. If 26.8 differs, **stop and report**: no fit constant is set until Tyler or the auditor rules | the script's output is committed under `specs/002-skill-pack/evidence/`, and any difference is reported and ruled |

### Fit

| id | task | done when |
|---|---|---|
| T-21 | ⚑ **Fit tables for the six twins (B-8.11, Q-44).** `tools/gen_fit_tables.py` (fontTools, dev only) writes `src/keyline/fit/tables/<twin>-{regular,bold}.json`: per-codepoint advances in units per em, the maximum advance, and `line_pitch_em = 1.2` (B-21), stored with the LibreOffice version that measured it (Q-44b). Each table also lists which of the 134 Vietnamese letters its twin lacks (audit 04: Caladea lacks 88). Each table records the source file's name, version and licence, and so does `NOTICE`. Rebuilding is byte-stable | tables for Liberation Sans, Serif and Mono, Gelasio, Carlito and Caladea; `NOTICE` lists all six; a rebuild is byte-identical |
| T-22 | **Estimator (§6.4).** `fit/__init__.py`: the width of a string as rendered (caps, tracking × size per character; a missing character uses the maximum advance), `marL` and table cell margins subtracted, greedy wrapping at the margin T-20 settles, line pitch × the style's line spacing **plus 0.01 mm per line** (B-21) plus `spcBef`/`spcAft`, and bullets and tables as §6.4 says. Characters missing from the voice's twin use its maximum advance, and the pen prints **one warning per deck** naming them ("Caladea (for Cambria) lacks: …; LibreOffice renders them in a fallback font, so the check render is not faithful"); the build goes ahead, and the warning is not a registry entry (audit 04). It raises `DoesNotFit` with "needs N lines, region holds M". AC-13(a): committed test strings (Latin, Vietnamese with diacritics, digits, caps with tracking) against Pillow `ImageFont.Layout.BASIC` at 1000 px, for each twin whose TTF is present (the others skip by name). The report gives the largest ratio per twin and flags any plain-Latin string above 1.05, an estimator that would refuse text that fits (informational, audit 03) | `tests/unit/test_fit.py`; `test_ac13a_fit_widths.py` gives ratios in [0.995, 1.25] for all six twins here |

### Pen

| id | task | done when |
|---|---|---|
| T-23 | ⚑ **Pen skeleton and writer isolation (§6.1, D-015, Q-21, Q-45, Q-46).** `keyline.pen` exposes `Deck`, `PenError`, `DoesNotFit` and `EvidenceError`; `_api`, `_regions` and `_writer_pptx` are internal, and only `_writer_pptx` imports python-pptx. `Deck(pack=…, mode=…, voice=…, evidence=None)` and `Deck.from_brief(path)` build the voice's template in memory (B-8.9). The pen **refuses a voice with an error-level `voice-*` finding** (`PenError`, audit 02 on Q-29). `deck.next()` / `deck.add(role, headline, notes=None)` put the headline in the title placeholder (the quote slide's headline in the `quote` style, with no added quote marks). Unfilled placeholders are removed. The keyline rule is drawn on evidence slides. `_check_token()` rejects hex, `NNpt`, `NNcm`, `NNin`, `NNpx` and `NNemu` | AC-10 part 1: a test inspects every public signature and return type; the in-memory template for (neutral, mode) is byte-identical to the committed file (Q-46) |
| T-24 | **Text verbs.** `text`, `bullets` (≤ `bullets_max`), `source` (built from the brief slide's evidence sources, first-seen order, "; ", "Source: "), `note` (the disclosure on cover and close by default; "Note: " added if missing), `notes`, `attribution`. One component per region; style and component allowed by the role and mode; caption caps; no italic, no centering, `noAutofit`, `wrap="square"`, zero insets; every text checked by the estimator | AC-10's `PenError` cases for these verbs, and `DoesNotFit` naming lines needed against lines available |
| T-25 | ⚑ **`figure()` with sub-boxes** (audit 01 note, carried by audit 02; Q-43 as ruled by audit 03). The numeral and the label are two shapes, each with its own box inside the figure region: the numeral's box is the region's top rows, one numeral line tall; the label's box is the rest, top-anchored. Both span the region's full width, and they touch but do not overlap. A region shorter than the numeral's rows plus one label line raises `DoesNotFit`, naming both. At most `numerals_max` per slide; a `series` entry raises `PenError`; `accent=True` counts against `accent_budget` | AC-10's figure cases; the two boxes lie inside the region and touch without overlapping; `box-overlap` is silent on a figure slide |
| T-26 | **`table`, `chart_bar`, `image` (§6.1, §6.6).** Tables: hairline rules, no fills, header cells in `label` capped at `caption_exempt_words`. Charts from a `series` entry: pack fonts and the voice's colours, muted bars, at most one highlight in accent (counted against the budget), no legend, direct labels; axis ids rewritten to positive deterministic UInt32s with `axId`/`crossAx` kept paired. Images fitted without cropping, `alt` written to `descr` | unit tests per verb; `officecli validate` 0 errors on a chart deck (skips without OfficeCLI) |
| T-27 | **Determinism (§6.5).** Save through `zipnorm`; core properties from the template, author and last-modified-by from the argument; each chart workbook's `core.xml` set to the template's `created` and its inner zip normalised | building a deck with a chart twice gives identical bytes |

### Specimens and acceptance

| id | task | done when |
|---|---|---|
| T-28 | ⚑ **Specimens in three voices (B-8.13, Q-42 as ruled by audit 03).** `fixtures/packs/swiss-specimen.evidence.toml`, and three briefs whose stems name their voice: `swiss-specimen-presented-neutral`, `swiss-specimen-presented-night` and `swiss-specimen-read-field` (`.brief.toml`, and the decks with the same stems). Each has one slide per role, uses every verb, and has real sentences about the pack. They are built by a committed script with `Deck.from_brief` | AC-11: each builds twice byte-identically. AC-12: `keyline brief` exits 0 and `check --brief` exits 0 on each, with no `adapter-unresolved` and no `ooxml-invalid` (OfficeCLI present) |
| T-29 | **AC-8 again, and core purity (B-3, AC-15).** The drift base is rebuilt with the pen from its brief and the six drifts re-applied, each giving exactly its one finding. A subprocess runs `keyline lint --brief` on the presented specimen and asserts that neither `pptx` nor `pypdfium2` is in `sys.modules` | `test_ac08_drift_pen.py`, `test_ac15_core_purity.py` |
| T-30 | **AC-13(b) fit stress.** A deck with every text at the longest length the estimator accepts for its region, rendered with LibreOffice (its version recorded, B-7): no text ink falls outside its region box by more than 2 px at 1280 px | `test_ac13b_fit_stress.py` (skips without LibreOffice) |
| T-31 | **A2 acceptance sweep.** AC-10 … AC-13 and AC-15; the M1 baseline unchanged; the import boundary still holds (lint never imports `keyline.pen`); README and CHANGELOG | every A2 AC test green locally; CI green |
| T-32 | **Report A2** in `report.md`: each A2 AC with command, output and PASS/FAIL; T-20's measurements; the three contact sheets; the script-coverage limit (Caladea lacks 88 of 134 Vietnamese letters), carried to Phase B's `check.md` and voice step. Then **G-1** (Tyler: the three specimen contact sheets; both templates and the specimens opened in PowerPoint, noting any repair prompt (B-6); a new text box on the `night` specimen is readable (Q-33)), in parallel with the A2 audit. **Stop** | review by Tyler; audit by the external session |

## Phase B: skill (tasks written after the A2 audit)

Outline, from plan §4: `skill/keyline/` (SKILL.md, references, `kl.py`);
the voice step (B-8.15); `tools/gen_docs.py`; `tools/build_skill.py`; the BonsaiHub demo
with inline voices (B-8.14) in a fresh session with G-2a (Q-16); AC-17 … AC-23; report B;
G-2. `references/check.md` carries the known limits: B-5, audit 02's FX-8 list, source
lines inside table cells (B-12, continued) and audit 03's FX-15 note on invisible
"Source: " runs, as the `numtokens` docstring lists them; and audit 04's coverage limit (prefer another family than Cambria for Vietnamese text).
The voice step (B-8.15) carries the same limit (report A2): for a subject whose text is Vietnamese, the skill does not pick Cambria (its twin Caladea lacks 88 of the 134 Vietnamese letters), and when the pen's one-per-deck coverage warning appears, the skill changes the voice's font rather than accepting the check render.

## Acceptance map

| AC | phase | tasks |
|---|---|---|
| AC-1 | A1 | T-03, T-12, T-13, T-16, T-18 (35 entries, B-8.6) |
| AC-2 | A1 | T-01, T-03, T-04, T-15, T-18 |
| AC-3 | A1 | T-07, T-10 |
| AC-4 | A1 | T-07 |
| AC-5 | A1 | T-05 |
| AC-6 | A1 | T-06 |
| AC-7 | A1 | T-12 (with the voice, B-8.4, B-8.5) |
| AC-8 | A1 (repeated in A2) | T-13, T-14; T-29 |
| AC-9 | A1 | T-08, T-08r, T-09, T-09r |
| AC-14 | A1 | T-15 |
| AC-14b | A1 | T-16 |
| AC-16 | A1 | T-17 |
| AC-10 | A2 | T-23, T-24, T-25, T-26 |
| AC-11 | A2 | T-27, T-28 |
| AC-12 | A2 | T-26, T-28 |
| AC-13 | A2 | T-20, T-21, T-22 (a); T-30 (b) |
| AC-15 | A2 | T-29 |
| AC-17 … AC-23 | B | — |
