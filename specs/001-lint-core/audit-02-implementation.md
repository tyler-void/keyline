# Audit 02: implementation of spec 001

- **Auditor:** an external Claude session, plus a separate adversarial tester agent.
  Neither saw the implementing session.
- **Date:** 2026-09-25
- **Scope:** branch `001-lint-core` at `589d693` (29 commits over `main` `ce21744`)

## Verdict

**FIX, then merge.**

- All 12 acceptance criteria pass, and the auditor reproduced them independently.
- Constitution III ("any .pptx") fails on an independent corpus. The ACs did not
  cover that corpus. The gap is in the spec the auditor wrote, not in the
  implementation's fidelity to the spec.
- Eight fix items (FX-1 … FX-8) follow, each with an amendment and a new acceptance
  criterion. After they pass, merge `001-lint-core` into `main`.

## What was verified and holds

- **Clean clone, Python 3.11.15, OfficeCLI 1.0.152 on PATH:** `ruff check` and
  `ruff format --check` are clean. `pytest -q` gives **174 passed**, matching
  `report.md`.
- **Integrity:**
  - The golden decks and their build scripts are byte-identical to the bootstrap
    bundle.
  - `spec.md` gained 58 lines and lost 0. `decisions.md` gained 22 and lost 0.
  - The CLAUDE.md diff touches only the Identity bullet (F-1).
  - A search of `src/` for fixture shape names (`verdict`, `l3`, `n3`, `rule2`, `T2`,
    `TextBox N`, …) finds nothing, so there are no fixture-specific branches.
- **Amendments checked on independent decks:**
  - A-3: an OfficeCLI chart 0.50 cm from the left edge raises `edge-margin`.
  - A-5: a deck whose master has no `p:bg` falls back to white, with an advisory,
    and contrast still fires (C8C8C8 on white, 1.67:1).
- **Adversarial corpus, 130 files from 5 generators** (pptxgenjs 4.0.1, python-pptx
  1.0.2, LibreOffice 24.2, OfficeCLI 1.0.152, raw XML/zip edits):
  - All seven required malformed inputs exit 1 with one line.
  - XXE and billion-laughs attacks are rejected.
  - Handled correctly: scaled and rotated groups, `clrMapOvr`, per-master themes,
    4:3 and portrait decks, and Vietnamese NFD text.
  - Output is byte-identical across runs, hash seeds and modes.
  - A 60-slide deck lints in 0.21 s.
  - Of 241 findings on the main decks: 219 TRUE, 6 FALSE-POSITIVE, 16 DEBATABLE.
    Every false positive was confirmed by rendering and checked against the XML.

The corpus, its scripts and its notes ship with this audit as `stress-corpus/`.

## Auditor's own errors (root causes of several findings)

1. **A-4 left out `p:style/a:fontRef`.** When the plan (P-7) put `fontRef` last,
   after the master text styles, the auditor approved it. The result is FP-1 and FN-1.
2. **Spec §6 required full containment for the contrast backing shape,** which gives
   FP-3. The spec's model also includes only the slide's own shapes, which gives FP-2
   (deferred, see below).
3. **F-1 updated only the Identity bullet in CLAUDE.md.** The "Pure Python >= 3.10"
   line still contradicts D-012.

## Fix items

Each item has an amendment to append to the spec verbatim, and a new acceptance
criterion. The test decks are in `stress-corpus/decks/` (author metadata already
rewritten to `Tyler`).

- **FX-1 · Output encoding and precision.**
  - **Evidence:** `PYTHONIOENCODING=cp1252 keyline lint d25_ppx_localized_names.pptx
    --json` → `UnicodeEncodeError`, 0 bytes of JSON. Shape names such as
    "タイトル 1" can't be encoded. Windows uses this encoding for redirected stdout.
  - **A-16:** `--json` writes UTF-8 bytes to `sys.stdout.buffer` whatever the locale.
    In `measured` and `threshold`, ratios get 3 decimals. Messages show percentages
    with 1 decimal (report Q1: the 25.2% band must not read as 0.25 against 0.25).
  - **AC-13:** under `PYTHONIOENCODING=cp1252`, d25 exits 2 with valid UTF-8 JSON,
    byte-equal to the output under a UTF-8 locale. `kpi-recipe` slide 4 shows
    `"measured": 0.252`.
- **FX-2 · No tracebacks, ever.**
  - **Evidence:** o51–o56 produce `ValueError` or `decimal.InvalidOperation`
    tracebacks. The triggers are `lumMod="75%"` (the Strict-style percentage),
    `lumOff="25000.0"`, a non-integer connector id, and a 40-digit length. d27 (Strict
    OOXML, which PowerPoint can save) is refused with the misleading reason "no valid
    p:sldSz".
  - **A-17:**
    - Parse every OOXML numeric attribute through one tolerant parser: integers,
      decimals, and `N%` percentages. If a value can't be parsed, drop the element
      and emit one `adapter-unresolved` advisory.
    - Add a top-level guard: an unexpected exception gives exit 1 with one line,
      `keyline: internal error while reading <part>: <ExceptionType>; rerun with
      --traceback and report it`. `--traceback` prints the full trace.
    - A Strict package gets an accurate reason: `Strict Open XML (ISO/IEC 29500
      Strict) is not supported yet`.
  - **AC-14:** o51–o56 and d27 produce no traceback. The d27 reason names Strict. An
    injected exception inside a rule gives the one-line internal-error message and
    exit 1.
- **FX-3 · Text color and font cascade (replaces A-4 for color and font).**
  - **Evidence:** d15 slide 2 renders white on navy, 11.62:1, in both OfficeCLI and
    LibreOffice. keyline reports `000000 on 1F3864 … 1.81:1` (FP-1). d15 slide 3
    renders white on FFF2CC, 1.12:1, and keyline reports nothing (FN-1).
  - **A-11:** Color and latin font resolve in this order:
    1. run `rPr`
    2. shape `lstStyle`
    3. **`p:style/a:fontRef`** (color from its child; font from `idx` major/minor)
    4. layout placeholder `lstStyle`
    5. master placeholder `lstStyle`
    6. master `txStyles`
    7. `defaultTextStyle`

    Size keeps the A-4 order. This order matches both renderers; PowerPoint has not
    been checked.
  - **AC-15:** d15 slide 2 has no `text-contrast`. d15 slide 3 gets `text-contrast`
    at 1.12:1.
- **FX-4 · Hidden shapes.**
  - **Evidence:** in d17 slide 4, `hidden="1"` shapes raise an `off-slide` error and
    a `text-contrast` warning (FP-4, FP-5). They also mask a 58% empty band (FN-2).
  - **A-12:** A shape with `cNvPr/@hidden="1"` is excluded from every rule and from
    dead-band content. So is any child of a hidden group. The slide gets one advisory
    with the count of hidden shapes.
  - **AC-16:** d17 slide 4 has no `off-slide` or `text-contrast` on the hidden shapes,
    and `dead-band` fires on the 8.0–19.05 cm band.
- **FX-5 · Off-slide severity for tables and charts.**
  - **Evidence:** in d20 slide 6, a table with text runs 5.00 cm past the right edge.
    keyline gives only an advisory ("possible bleed"), so the slide alone exits 0
    (FN-4).
  - **A-13:** Tables and charts (`graphicFrame:table`, `graphicFrame:chart`) count as
    text-bearing for `off-slide`. The bleed advisory stays only for `pic` and for
    `sp` shapes without text.
  - **AC-17:** d20 slide 6 gets an `off-slide` error on the table.
- **FX-6 · Autofit shrink.**
  - **Evidence:** in d18 slide 2, LibreOffice wrote `normAutofit fontScale="28122"`.
    The body renders at about 9.0 pt, but keyline reads 32 pt. It misses
    `body-too-small` (FN-3) and falsely fires `title-not-dominant` (FP-6).
  - **A-14:** Effective run size = resolved `sz` × `bodyPr/a:normAutofit@fontScale`
    (default 100%). Messages add "(autofit N%)". This supersedes the plan's R-2
    deferral.
  - **AC-18:** d18 slide 2 gets `body-too-small` at about 9.0 pt and no
    `title-not-dominant`.
- **FX-7 · Contrast backing coverage.**
  - **Evidence:** in d16 slide 6, a text box is 0.1 in larger than its navy card on
    every side. The text renders on the card, but keyline measures it against the
    slide background: `FFFFFF on FFFFFF 1:1` (FP-3).
  - **A-15:** The backing shape is the topmost filled shape beneath the text shape
    whose box covers at least `backing_coverage_min` (0.90, in `thresholds.toml`) of
    the text shape's box area, edges inclusive. This replaces "fully contains".
  - **AC-19:** d16 slide 6 has no `text-contrast`. AC-1 … AC-4 are unchanged.
- **FX-8 · Scale.**
  - **Evidence:** one slide with 1,000 shapes lints in 1.50 s, and 60 slides × 150
    shapes in 6.03 s (auditor's timing). `box-overlap` compares every pair of shapes
    using `Fraction`. Separately, a deck with 600 MB of embedded video hits the 512 MB
    cap, even though keyline never decompresses media.
  - **A-18:**
    - Pairwise rules use integer EMU and a sort-and-sweep over x.
    - The uncompressed-size cap counts only XML and rels parts. Media members are
      never read.
  - **AC-20:** `perf_1000` < 1.0 s and `perf_150_x60` < 2.0 s, generated by
    `stress-corpus/src/perf_shapes.py`. A test with a large stored media member
    passes the cap.

## Deferred (backlog, not blockers)

| Priority | Item | Evidence |
|---|---|---|
| P1 | Non-placeholder layout and master shapes (honoring `showMasterSp`) count as content and as contrast backing | FP-2 (d16 slide 4: white title on a layout navy panel reported 1:1); report Q2 |
| P1 | Word counting for scripts without spaces (CJK, Thai): body detection is blind to them today | d23 |
| P2 | A table text model (fonts, contrast, size) | FN-5, FN-6 (d03 slide 3) |
| P2 | Strict OOXML support through namespace mapping | d27 |
| P3 | Read `mc:Choice` when its namespace is understood | d17 slide 5 |
| P3 | Title underlines drawn as lines (`cxnSp`, `a:ln`) | d20 slide 7 |

## Rulings on report.md open questions

1. **Ratio precision.** Fixed in FX-1 (3 decimals).
2. **Layout and master shapes.** Deferred at P1 (above).
3. **Default template fails two defaults.** Not a defect. Record it as lesson L-009
   (calibration data: stock Office templates sit 0.76 cm from the top and have a 1.38×
   title-to-body ratio). Thresholds are unchanged until M6 calibration.
4. **Unverified against PowerPoint.** Accepted. Optional: open a probe deck in
   PowerPoint for the web to check the A-11 cascade, hidden shapes, autofit and
   tint/shade in one pass.
5. **P-11 (`mc:Fallback`).** Accepted retroactively.
6. **editorial-fixed spacing (0.05 cm gap).** Not a lint defect under constitution
   VIII. A minimum gap between stacked text is a backlog rule candidate.
7. **CLAUDE.md Python line.** Update it to ">= 3.11 (D-012)". This was the auditor's
   miss in F-1.
8. **Duplicate `research.md`.** Tyler deletes it locally. Not a repo matter.

All 11 deviations in report.md are accepted. Deviation 4 (the default output name
in `editorial-fixed.sh`) prevented an overwrite of a golden deck; good catch.

## Handoff notes

- `stress-corpus/decks/` holds the 16 decks named above. Their `docProps` authors were
  rewritten to `Tyler`; the original python-pptx template carries a third-party
  author name. Lint output is byte-identical before and after the rewrite.
- `stress-corpus/src/` rebuilds the full corpus. Builders must overwrite
  `core_properties.author` and `last_modified_by`, or AC-12 fails.
- Copy the decks that the new ACs use into `fixtures/foreign/stress/`, with their
  builder scripts. Do not copy the whole corpus.
