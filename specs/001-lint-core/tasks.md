# Tasks 001: lint core

Order is the build order. Each task lands as its own commit(s), with its tests, on
`001-lint-core`. "Done when" names the check an auditor can re-run.
Tasks marked ⚑ depend on an open question in `plan.md` §9 and follow whatever Tyler
decides.

## M0: skeleton

| id | task | done when |
|---|---|---|
| T-01 | `pyproject.toml` (hatchling, `src/` layout, `keyline` console script, Python ≥ 3.10, runtime `lxml` + `Pillow`, dev extra `pytest ruff python-pptx`), `ruff.toml`, `src/keyline/__init__.py` (`__version__ = "0.1.0"`), `__main__.py`, a stub `cli.py` whose `--version` works | `pip install -e .[dev] && keyline --version` prints `0.1.0`; `ruff check` is clean |
| T-02 | `.github/workflows/ci.yml`: ubuntu-latest, matrix 3.10 / 3.12, `ruff check`, `ruff format --check`, `pytest -q` | CI is green on the branch (AC-11, partial) |
| T-03 | README: status "pre-alpha", install, the three commands, and the L-002 limitation. CHANGELOG entry | Review |

## Core plumbing

| id | task | done when |
|---|---|---|
| T-04 | `units.py` (EMU/cm/pt, `round2` with Decimal half-up) and `geom.py` (Box, intersect, contains inclusive, slide coverage, rotated AABB with exact 90° cases) | `tests/unit/test_units.py`, `test_geom.py` |
| T-05 | ⚑ `config.py` + `thresholds.toml` (both modes, `calibrated = false`) + the flat-TOML reader for 3.10, with a parity test against `tomllib` on ≥ 3.11 | `tests/unit/test_config.py` |
| T-06 | ⚑ `findings.py`: ordered Finding, sort key, JSON writer, stderr writer + summary, exit-code logic. `registry.py`: RuleSpec, `@rule`, duplicate-id guard | `tests/unit/test_findings.py` (ordering, null shape_id, advisory never exits 2, byte-stable JSON) |

## OOXML adapter

| id | task | done when |
|---|---|---|
| T-07 | `ooxml/package.py` + `ns.py`: safe parser, zip checks (not a zip / no presentation part / size and member caps), rels resolution, part cache. `ScanError` → exit 1 with a one-line reason | `tests/adapter/test_package.py`: random bytes, `.docx`, a zip bomb, XXE |
| T-08 | `ooxml/theme.py` + `color.py` ⚑: clrScheme, sysClr, clrMap(+ovr), `lumMod lumOff tint shade`, alpha policy, unsupported → None + diagnostic. Transforms documented in `docs/adapter.md` | `tests/adapter/test_color.py`, one case per transform and per unsupported path |
| T-09 | `ooxml/placeholders.py` ⚑ + `geometry.py` ⚑: own xfrm, layout/master inheritance, group composition with Fraction, rotation AABB, group rot/flip if approved | `tests/adapter/test_geometry.py` + AC-6 fixture (T-16) |
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
| T-24 | ⚑ `test_ac12_hygiene.py` (commit identities, fixture docProps, NOTICE) | Passes on the branch |
| T-25 | `specs/001-lint-core/report.md`: each AC with its command, an output excerpt and PASS/FAIL; Deviations; Open questions | Review by Tyler; audit by the external session |

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
| AC-12 | T-24 + the Tyler decision on R-12 |
