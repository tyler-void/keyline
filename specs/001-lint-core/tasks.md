# Tasks 001: lint core

Order is the build order. Each task lands as its own commit(s), with its tests, on
`001-lint-core`. "Done when" names the check an auditor can re-run.
Tasks marked ⚑ touched an open question in `plan.md` §9. Audit 01 resolved all of them
(see plan §9); each ⚑ task implements the ACCEPTED or AMENDED behavior.

## M0: skeleton

| id | task | done when |
|---|---|---|
| T-01 | `pyproject.toml` (hatchling, `src/` layout, `keyline` console script, Python ≥ 3.11 (D-012), runtime `lxml` + `Pillow`, dev extra `pytest ruff python-pptx`), `ruff.toml`, `src/keyline/__init__.py` (`__version__ = "0.1.0"`), `__main__.py`, a stub `cli.py` whose `--version` works | `pip install -e .[dev] && keyline --version` prints `0.1.0`; `ruff check` is clean |
| T-02 | `.github/workflows/ci.yml`: ubuntu-latest, matrix 3.11 / 3.13 (D-012), `ruff check`, `ruff format --check`, `pytest -q` | CI is green on the branch (AC-11, partial) |
| T-03 | README: status "pre-alpha", install, the three commands, and the L-002 limitation. CHANGELOG entry | Review |

## Core plumbing

| id | task | done when |
|---|---|---|
| T-04 | `units.py` (EMU/cm/pt, `round2` with Decimal half-up) and `geom.py` (Box, intersect, contains inclusive, slide coverage, rotated AABB with exact 90° cases) | `tests/unit/test_units.py`, `test_geom.py` |
| T-05 | ⚑ `config.py` + `thresholds.toml` (both modes, `calibrated = false`, `large_text_pt` + `large_text_bold_pt`), read with stdlib `tomllib` (D-012; no custom reader, no parity test) | `tests/unit/test_config.py` |
| T-06 | ⚑ `findings.py`: ordered Finding, sort key, JSON writer, stderr writer + summary, exit-code logic. `registry.py`: RuleSpec, `@rule`, duplicate-id guard | `tests/unit/test_findings.py` (ordering, null shape_id, advisory never exits 2, byte-stable JSON) |

## OOXML adapter

| id | task | done when |
|---|---|---|
| T-07 | `ooxml/package.py` + `ns.py`: safe parser, zip checks (not a zip / no presentation part / size and member caps), rels resolution, part cache. `ScanError` → exit 1 with a one-line reason | `tests/adapter/test_package.py`: random bytes, `.docx`, a zip bomb, XXE |
| T-08 | `ooxml/theme.py` + `color.py` ⚑: clrScheme, sysClr, clrMap(+ovr), `lumMod lumOff tint shade`, alpha policy, unsupported → None + diagnostic. Transforms documented in `docs/adapter.md` | `tests/adapter/test_color.py`, one case per transform and per unsupported path |
| T-09 | `ooxml/placeholders.py` ⚑ + `geometry.py` ⚑: own xfrm, layout/master inheritance, group composition with Fraction, rotation AABB, group rot/flip (P-3 accepted) | `tests/adapter/test_geometry.py` + AC-6 fixture (T-20) |
| T-10 | `ooxml/text.py` ⚑: the §2.3 cascade for size, b, i, cap, spc, latin (theme `+mj-lt`/`+mn-lt`), color. `ooxml/fill.py` ⚑: shape fill and background (§2.5, §2.6) | `tests/adapter/test_text.py`, `test_fill.py` on in-memory packages |
| T-11 | `model.py` + `ooxml/adapter.py`: build the Deck (slides in `sldIdLst` order, spTree z-order with groups flattened, kinds, connectors' stCxn/endCxn, `has_notes` ⚑), emit `adapter-unresolved` / `unsupported-content` | `tests/adapter/test_adapter_golden.py` asserts the model of both goldens (shape counts, T2 box = 540000/432000/10800000/720000 EMU, slide-4 connector ids) |

## Rules

Each rule task = the rule module + its fixtures in `build_rules.py` + `expect.toml`
rows + `tests/rules/test_<id>.py`. Done when its positive and negative decks behave as
listed in plan §5.2.

| id | task |
|---|---|
| T-12 | `rules/_common.py` ⚑ (text_bearing, visible, background, content slide, words, `pick_title`, KPI numeral), the fixture builder skeleton `fixtures/rules/src/_deck.py`, the reproducibility test, and a check that each registry `rationale` names a real lesson id or a real `docs/research.md` heading |
| T-13 | `off-slide` ⚑, `edge-margin` ⚑. Also record the goldens' SHA-256 in `tests/acceptance/golden_hashes.txt` |
| T-14 | `dead-band` ⚑, `box-overlap` ⚑ |
| T-15 | `body-too-small` ⚑, `title-not-dominant` ⚑ |
| T-16 | `text-contrast` ⚑, `notes-missing` |
| T-17 | `font-count` ⚑, `title-underline` ⚑, `equal-card-row` ⚑ |

## CLI, render, fixtures, acceptance

| id | task | done when |
|---|---|---|
| T-18 | `lint.py` + `cli.py`: `keyline lint [--json] [--mode]`, `keyline rules [--json]` | `tests/acceptance/test_ac07_invalid.py`, `test_ac08_determinism.py` (3 runs × each golden × each mode, byte-equal) |
| T-19 | AC-9 timing test; profile if it's over budget | `test_ac09_speed.py` |
| T-20 | `fixtures/foreign/src/build_foreign.py`: python-pptx placeholder deck, raw-XML nested groups ⚑ | `test_ac05_placeholders.py`, `test_ac06_groups.py` |
| T-21 | ⚑ `fixtures/golden/src/editorial-fixed.sh` (a copy of `editorial.sh` with only the re-spacing and the `l3` color changed) → `editorial-fixed.pptx` built with OfficeCLI 1.0.152 | `git diff --no-index editorial.sh editorial-fixed.sh` shows only those lines; `test_ac04_editorial_fixed.py` exits 0 |
| T-22 | Golden acceptance tests + reviewed JSON snapshots in `fixtures/expected/` | `test_ac01_kpi.py`, `test_ac02_editorial_read.py`, `test_ac03_editorial_presented.py` |
| T-23 | `render.py` + `keyline render` ⚑ + `keyline check` ⚑ | `test_ac10_render.py` (marked `officecli`, runs locally); the missing-binary path is tested with an empty `PATH` |
| T-24 | ⚑ `test_ac12_hygiene.py`: commit identities against the D-014 allowlist (names `Tyler`/`tyler-void` with `code@tyler-void.dev`; Claude `Co-Authored-By` trailers per D-013; committer `GitHub <noreply@github.com>`), fixture docProps, NOTICE | Passes on the branch |
| T-25 | ✅ `specs/001-lint-core/report.md`: each AC with its command, an output excerpt and PASS/FAIL; Deviations; Open questions | Review by Tyler; audit by the external session |

## Round 2: audit 02 fix items

Each task implements one fix item from [`audit-02-implementation.md`](audit-02-implementation.md)
with its acceptance test. Decks: `fixtures/foreign/stress/`. AC-1…AC-12 stay green; every
golden snapshot change is explained in `report.md`.

| id | fix item | task | done when |
|---|---|---|---|
| T-26 | FX-1 (A-16) | `--json` writes UTF-8 bytes to `sys.stdout.buffer`; ratios in `measured`/`threshold` get 3 decimals; percentages in messages get 1 decimal | `tests/acceptance/test_ac13_encoding.py` |
| T-27 | FX-2 (A-17) | one tolerant numeric parser for OOXML attributes (int, decimal, `N%`); unparseable → element dropped + one `adapter-unresolved`; top-level guard with `--traceback`; Strict packages get their own reason | `tests/acceptance/test_ac14_no_traceback.py` |
| T-28 | FX-3 (A-11) | color and latin font cascade puts `p:style/a:fontRef` third; size keeps the A-4 order | `tests/acceptance/test_ac15_fontref.py` |
| T-29 | FX-4 (A-12) | `cNvPr/@hidden="1"` shapes (and children of hidden groups) leave the model; one advisory per slide with the count | `tests/acceptance/test_ac16_hidden.py` |
| T-30 | FX-5 (A-13) | tables and charts are text-bearing for `off-slide` | `tests/acceptance/test_ac17_table_off_slide.py` |
| T-31 | FX-6 (A-14) | effective run size = `sz` × `normAutofit@fontScale`; messages add "(autofit N%)" | `tests/acceptance/test_ac18_autofit.py` |
| T-32 | FX-7 (A-15) | contrast backing = topmost filled shape beneath covering ≥ `backing_coverage_min` (0.90) of the text box | `tests/acceptance/test_ac19_backing.py` |
| T-33 | FX-8 (A-18) | integer sort-and-sweep for pairwise rules; the size cap counts only XML and rels parts | `tests/acceptance/test_ac20_scale.py` |

## Acceptance map

| AC | tasks |
|---|---|
| AC-1 | T-13…T-17, T-22 |
| AC-2 | T-13, T-16, T-17, T-22 |
| AC-3 | T-15, T-22 |
| AC-4 | T-21 |
| AC-5 | T-09, T-10, T-20 |
| AC-6 | T-09, T-20 |
| AC-7 | T-07, T-18 |
| AC-8 | T-06, T-18 |
| AC-9 | T-19 |
| AC-10 | T-23 |
| AC-11 | T-02 and everything else |
| AC-12 | T-24 (D-013, D-014) |
| AC-13 | T-26 |
| AC-14 | T-27 |
| AC-15 | T-28 |
| AC-16 | T-29 |
| AC-17 | T-30 |
| AC-18 | T-31 |
| AC-19 | T-32 |
| AC-20 | T-33 |
