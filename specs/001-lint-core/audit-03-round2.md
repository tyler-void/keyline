# Audit 03: round 2 of spec 001

- **Auditor:** an external Claude session. It did not see the implementing session.
- **Date:** 2026-09-26
- **Scope:** branch `001-lint-core` at `85e1285` (45 commits over `main` `ce21744`)

## Verdict

**SHIP.** Apply A-19 first; it is one small commit. Then merge `001-lint-core` into
`main` with a merge commit, not a squash, so the per-task history and the audit trail
stay intact.

## What was verified

- **Clean clone, Python 3.11.15, OfficeCLI 1.0.152:** `ruff check` and
  `ruff format --check` are clean, and `pytest -q` gives **215 passed**, matching the
  report.
- **Identity:** all 46 commits are `Tyler <code@tyler-void.dev>` (D-014). 45 of them
  carry the Claude trailer (D-013).
- **Integrity:**
  - The golden decks and their build scripts are still byte-identical to the bundle.
    `editorial-fixed` is unchanged since round 1.
  - The 13 stress fixtures are byte-identical to audit 02's `stress-corpus/decks/`.
  - Everything added since round 1 is append-only: spec (+58/−0), lessons (+7/−0),
    report (+223/−0).
  - CLAUDE.md changes exactly one line, the Python line (D-012).
  - `thresholds.toml` gains only `backing_coverage_min = 0.90` (A-15).
  - `src/` has no branch keyed on a fixture or stress-deck name.
- **Test changes to AC-1…AC-12** are exactly the two the report declares:
  - `test_ac02`: 3.57 → 3.569 (A-16);
  - `test_ac12`: `PptxGenJS` added to the allowlist (R2-8).
- **Snapshot changes** are precision only: 3 decimals for ratios and 1 decimal for
  percentages. No finding was added or removed.

## Full stress corpus, round 1 against round 2

All 130 files were re-linted with both builds.

- **Tracebacks:** 6 files in round 1, **0** in round 2. Every exit code is 0, 1 or 2.
- **Now lint normally:** o51–o56 and v09 (600 MB of embedded video).
- **o13 (`sldSz` 0×0):**
  - Round 1 linted it and produced 6 bogus `off-slide` errors.
  - Round 2 refuses it: "no valid p:sldSz".
  - 0 is below the schema minimum, so this is an improvement, not a regression.
- **Findings on the 25 main decks:** exactly 7 removed and 7 added. They are the
  targeted fixes, and nothing else moved:

  | Deck | Removed | Added |
  |---|---|---|
  | d15 | FP-1 (slide 2, 1.81:1) | FN-1 (slide 3, 1.12:1) |
  | d16 | FP-3 (slide 6) | — |
  | d17 | FP-4, FP-5 (hidden shapes) | FN-2 (dead-band, 58%) and the A-12 advisory |
  | d18 | FP-6 (title-not-dominant) | FN-3 (body-too-small at 9 pt) |
  | d20 | chart and table `off-slide` advisories | the same findings as errors (FN-4) |

  The other 20 decks are unchanged, finding for finding.
- **One new finding outside the targets:** d17 slide 6, `body-too-small` at 11 pt
  (`autofit 55.0%`). It follows directly from A-14. The fixture stores
  `fontScale="55000"` on text that LibreOffice re-fits to full size, which the stress
  tester had already marked debatable. This is recorded as lesson L-010, not as a
  defect.
- **Encoding:** every main deck, under utf-8, cp1252 and ascii, gave 50/50 runs with
  byte-identical JSON and no traceback.
- **Speed** (median of 3 whole-process runs, auditor sandbox, 2 vCPU):
  - perf_1000: 0.26 s
  - perf_2000: 0.43 s
  - perf_150_x60: 1.64 s

## Rulings on the round 2 deviations

All nine are accepted.

- **R2-5 (autofit from the shape's own `bodyPr` only) is correct.** `fontScale` is
  computed per shape instance. A layout's `normAutofit` only turns autofit on.

## Rulings on the round 2 open questions

1. **AC-20 margin → A-19** (below). Budgets stay as they are. The measurement changes
   from the median to the minimum of 3 runs. The minimum is the standard low-noise
   estimate of intrinsic cost: runner noise only ever adds time. Changing the method
   is not tuning a design threshold. Constitution V is about the thresholds that judge
   decks, not about CI budgets.
2. **d18 and its LibreOffice version.** The committed deck is the evidence, not the
   builder. AC-18 refers to the committed file. Add a line to
   `fixtures/foreign/stress/README.md` recording its SHA-256 and "built with
   LibreOffice 24.2.7.2; not reproducible on 26.8 (different fontScale)". d18 stays
   out of the reproducibility test.
3. **FP-2.** Still open. It is P1 in the lint 0.2 backlog.
4. **Strict OOXML.** Still P2 in the backlog.
5. **Local untracked files.** Tyler removes them. This is not a repo matter.

## Amendment to append (verbatim)

- **A-19 (2026-09-26, audit 03).** AC-9 and AC-20 are judged on the **minimum** of 3
  whole-process runs instead of the median. Budgets are unchanged: 1.0 s for AC-9 and
  for `perf_1000`, 2.0 s for `perf_150_x60`. The tests print all three times.

## Lessons to append

- **L-010 · 2026-09-26 · A stored autofit scale is trusted.** keyline applies
  `normAutofit@fontScale` as written. A generator that writes a scale without
  re-fitting the text, or an app that re-fits on open (LibreOffice does), can make
  keyline report a size that the viewer won't show. Example: d17 slide 6, where the
  stored scale is 55% and LibreOffice shows full size. Only a render-based size check
  (a backlog item) can settle this.

## After the merge

- **Lint 0.2 backlog, P1:**
  - layout and master shapes as content and as contrast backing (FP-2);
  - word counting for scripts written without spaces (CJK, Thai).
- **Next milestone:** spec 002, covering the skill, the brief (thesis, own-world,
  headline spine) and the first style pack.
