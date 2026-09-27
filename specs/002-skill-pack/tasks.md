# Tasks 002: skill, brief and the Swiss pack

Order is the build order. Each task lands as its own commit(s), with its tests, on
`002-skill-pack`, and is pushed. "Done when" names the check an auditor can re-run.
Tasks marked ⚑ depend on an open question in [`plan.md`](plan.md) §9 and follow its
proposal unless Tyler rules otherwise. ruff fixes and formatting run only on
`src tests fixtures tools`. Spec 002's acceptance tests live in `tests/acceptance/m2/`,
because spec 001's `test_acNN_*.py` files keep their names and spec 002 restarts at
AC-1.

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
| T-08 | ⚑ **Pack format and Swiss data (§5.1, §5.2, §5.4).** `packs/__init__.py` (load by name or directory, validate, list), `packs/swiss/pack.toml` (palette, surfaces, grid, styles, roles, regions) and `README.md`, `keyline packs [--json]`; the seven §5.4 invariants as tests for both modes (Q-10, Q-20) | `tests/unit/test_packs.py`, `test_ac09_pack_invariants.py` |
| T-09 | ⚑ **Templates (§5.3).** `zipnorm.py`; `packs/swiss/src/build_templates.py` (raw OOXML); `swiss-presented.pptx`, `swiss-read.pptx`; constraint tests via the M1 adapter; rebuild byte-identical (Q-17, Q-21) | `test_ac09_templates.py`; `officecli validate` 0 errors on both templates (skips without OfficeCLI) |
| T-10 | **Pack rules (§3.4).** `off-palette-color`, `off-scale-size`, `off-pack-font`, `accent-overuse`; `--pack NAME\|DIR`; `accepted` downgrade (Q-24); `--pos`/`--neg` fixtures from the Swiss template with `pack = "swiss"` in `expect.toml` | AC-3 cases pass; the fixture harness passes `pack`/`brief` to lint |

### Brief and evidence

| id | task | done when |
|---|---|---|
| T-11 | ⚑ **Numeric tokens (§4.4).** `numtokens.py` (Q-19); `Shape.table_text` in the adapter; equality with the auditor's oracle on the anchors, `product.toml` strings and a seeded 5,000-string corpus; the Q-6 limits pinned as tests | `tests/unit/test_numtokens.py` |
| T-12 | ⚑ **Evidence and brief schema, `keyline brief` (§4.1–§4.3).** `brief.py`, the five §4.3 findings as registry entries (Q-2, Q-3, Q-14, Q-23); `fixtures/briefs/` with one file per schema error and `--pos`/`--neg` per finding | `test_ac07_brief.py` |
| T-13 | ⚑ **Deck vs brief (§4.5) and CLI resolution (§3.5).** `briefcheck.py`, the six §4.5 registry entries, `--brief` on `lint`/`check`, `--mode` default `None`, conflict errors (Q-13) | `tests/unit/test_briefcheck.py`, `tests/acceptance/test_cli_resolution.py` |
| T-14 | ⚑ **AC-8 drift decks.** `fixtures/briefs/src/build_drift.py` builds the base deck from the Swiss template (pen-like output) and the six drifted copies (Q-4) | `test_ac08_drift.py`: base exits 0; each drift gives exactly its one finding |

### Render, validate, doctor

| id | task | done when |
|---|---|---|
| T-15 | ⚑ **Render engines (§7).** `libreoffice` (private profile, `--outdir`, 120 s, pypdfium2 or pdftoppm, 1280 px), `auto`, `--engine`, known limits per engine; the no-engine message keeps the M1 substrings (Q-11, Q-18); `--engine officecli` on the M1 `officecli` tests (AC-2's allowed change) | `test_ac14_render_engines.py` (skips without LibreOffice); M1 `test_ac10_render.py` passes |
| T-16 | **Validate step (§7).** `officecli validate --json` parsing, `ooxml-invalid`, `--no-validate`, the skipped message; `fixtures/validate/editorial-bogus.pptx` built by a committed script | `test_ac14b_validate.py` (skips without OfficeCLI) |
| T-17 | ⚑ **doctor (§7).** All nine checks and tokens, install hints, exit rule, `--json`; the `NO_PPTX` path tested in a venv without python-pptx (Q-22) | `test_ac16_doctor.py` |

### Acceptance and report

| id | task | done when |
|---|---|---|
| T-18 | ⚑ **A1 acceptance sweep.** AC-1 (32 entries, Q-1), AC-2 (baseline identity; the stress re-lint table; the list of M1 test changes), an import-boundary test (lint never imports `pptx`, `pypdfium2`, `keyline.pen`, `keyline.render`); README, `docs/adapter.md` (roles, table text), CHANGELOG | every A1 AC test green locally; CI green |
| T-19 | **Report A1** in `report.md`: each A1 AC (AC-1 … AC-9, AC-14, AC-14b, AC-16) with command, output excerpt and PASS/FAIL; Deviations; Open questions. Then **stop** for the A1 audit (Q-15) | review by Tyler; audit by the external session |

## Phase A2: pen (tasks written after the A1 audit)

Outline, from plan §3: pen public API and token guard; region model; python-pptx writer
module; verbs (`text`, `bullets`, `figure`, `table`, `chart_bar`, `image`,
`attribution`, `source`, `note`, `notes`); fit tables generator and estimator;
determinism (zip, core properties, chart workbook, axis ids); specimen briefs, evidence
and decks; AC-8 repeated on a pen-built deck; AC-10 … AC-13, AC-15; report A2; G-1.

## Phase B: skill (tasks written after the A2 audit)

Outline, from plan §4: `skill/keyline/` (SKILL.md, references, `kl.py`);
`tools/gen_docs.py`; `tools/build_skill.py`; the BonsaiHub demo in a fresh session with
G-2a (Q-16); AC-17 … AC-23; report B; G-2.

## Acceptance map

| AC | phase | tasks |
|---|---|---|
| AC-1 | A1 | T-03, T-12, T-13, T-16, T-18 |
| AC-2 | A1 | T-01, T-03, T-04, T-15, T-18 |
| AC-3 | A1 | T-07, T-10 |
| AC-4 | A1 | T-07 |
| AC-5 | A1 | T-05 |
| AC-6 | A1 | T-06 |
| AC-7 | A1 | T-12 |
| AC-8 | A1 (repeated in A2) | T-13, T-14 |
| AC-9 | A1 | T-08, T-09 |
| AC-14 | A1 | T-15 |
| AC-14b | A1 | T-16 |
| AC-16 | A1 | T-17 |
| AC-10 … AC-13, AC-15 | A2 | — |
| AC-17 … AC-23 | B | — |
