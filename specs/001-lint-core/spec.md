# Spec 001: lint core

- **Milestone:** M0 (repo skeleton) + M1 (lint, render, check)
- **Status:** approved for planning. Stop after `plan.md` and `tasks.md`.
- **Decides:** Tyler · **Audits:** an external session, by cloning the repo
- **Append-only:** amendments go in the log at the bottom, with a date.

## Goal

`keyline lint deck.pptx` reads any `.pptx` directly, builds a normalized deck model,
runs a versioned rule registry, and emits findings under a fixed contract.
`keyline render` produces a PNG per slide and a contact sheet through OfficeCLI.
`keyline check` runs both. It is the gate that the M2 skill will require before
delivering any deck.

## Out of scope

The skill, style packs, a token "pen" API, font embedding, hooks, MCP, render-based
rules, and calibration. Do not build ahead of this spec.

## 1. Repository skeleton (M0)

- `pyproject.toml` with the `keyline` package under `src/` and a `keyline` console script.
- Python >= 3.10.
  - Runtime deps: `lxml`, `Pillow`.
  - Dev deps: `pytest`, `ruff`, and `python-pptx` (used only to generate fixtures).
- Suggested layout (the plan may refine it, with reasons):
  ```
  src/keyline/
    cli.py  model.py  findings.py  registry.py  config.py  render.py  thresholds.toml
    ooxml/   package reader, geometry, placeholders, text, color, theme
    rules/   one module per rule
  tests/  fixtures/{golden,rules,foreign}/  docs/  specs/
  ```
- GitHub Actions runs `ruff` and `pytest` on `ubuntu-latest` with Python 3.10 and
  3.12. Render tests skip there, because OfficeCLI is absent.
- The README describes the project status honestly: pre-alpha.

## 2. Deck model

Use dataclasses. Store every length in EMU as an integer.

- **Deck:** slide width and height (from `p:sldSz`); theme colors (`dk1 lt1 dk2 lt2
  accent1-6 hlink folHlink`) and major/minor latin fonts; the slides.
- **Slide:** 1-based index; layout name; resolved background; shapes in z-order
  (spTree document order, with groups flattened); `has_notes`, which is true when the
  notes slide exists and holds non-whitespace text.
- **Shape:**
  - id, name, and kind: `sp`, `pic`, `graphicFrame:chart`, `graphicFrame:table`,
    `graphicFrame:other` or `cxnSp`
  - preset geometry (the `prstGeom` value, or `custom`)
  - absolute `x y w h` and rotation
  - fill (`solid:#RRGGBB`, `gradient`, `none` or `unknown`)
  - placeholder type and idx
  - for connectors: the start and end shape ids (`stCxn`, `endCxn`)
  - text: paragraphs (with alignment) made of runs (text, size_pt, bold, italic,
    caps, spacing, resolved latin font, resolved color)

### Resolution requirements

1. **Placeholder geometry.** A placeholder with no `a:xfrm` inherits from the matching
   layout placeholder (matched by type, then idx), then from the master.
2. **Text size.** Resolve in this order: run `sz`, paragraph properties, the shape's
   `lstStyle`, the layout, then the master `txStyles` (title, body or other). If the
   size still cannot be resolved, it is `None`: rules skip that run and the adapter
   emits `adapter-unresolved` (advisory).
3. **Groups.** Compose the `grpSpPr` transforms (`off`, `ext`, `chOff`, `chExt`), with
   nesting.
4. **Colors.** Resolve `schemeClr` through the theme using the master's `clrMap`.
   Apply `lumMod`, `lumOff`, `tint` and `shade`. List the supported transforms in the
   docs. An unsupported transform gives color `None` plus an advisory.
5. **Theme fonts.** Map `+mj-lt` and `+mn-lt` to the theme's major and minor fonts.
6. **Background.** Look at the slide, then the layout, then the master. M1 resolves
   solid fills only. A gradient or image background is `unknown`, and rules that need
   the background skip it with an advisory.
7. **Rotation.** Use the axis-aligned bounding box of the rotated rectangle.

## 3. Findings contract

- A finding has exactly these keys, in this order: `rule, category, severity, slide,
  shape_id, shape_name, message, measured, threshold`.
  - `slide` is 0 for deck-level findings. `shape_id` may be null.
- With `--json`, write a JSON array to stdout, sorted by `(slide, rule, shape_id)`.
- Always write human-readable lines to stderr, followed by a one-line summary.
- **Exit codes:**
  - 0: no findings at severity `warning` or `error`
  - 2: at least one such finding
  - 1: could not scan (not a zip, not a pptx, parse failure). Print a one-line reason.
- `advisory` findings never change the exit code.
- Output is byte-identical across runs.

## 4. Registry

Every rule declares these fields:

- `id`
- `category`: `slop` or `quality`
- `severity`: `error`, `warning` or `advisory`
- `scope`: `slide` or `deck`
- `basis`: `geometry`, `text`, `color` or `structure`
- `since`: `"0.1.0"`
- `summary`: one line
- `rationale`: a section of `docs/research.md` or a lesson id

`keyline rules [--json]` lists the registry.

## 5. Modes and thresholds

`--mode presented|read`; the default is `presented`. All thresholds live in
`thresholds.toml` with `calibrated = false`.

| Key | presented | read |
|---|---|---|
| `body_min_pt` | 18 | 11 |
| `caption_exempt_words` (text this short is not body) | 5 | 5 |
| `title_ratio_min` | 2.0 | 1.6 |
| `edge_margin_cm` | 1.27 | 1.27 |
| `edge_margin_tolerance_cm` (explicit, so 1.25 cm is not a finding) | 0.05 | 0.05 |
| `dead_band_ratio` | 0.25 | 0.25 |
| `contrast_normal` / `contrast_large` (WCAG 2.x) | 4.5 / 3.0 | 4.5 / 3.0 |
| `large_text` | >= 18 pt, or >= 14 pt bold | same |
| `font_family_max` | 2 | 2 |

**Cover rule for M1:** slide 1 is treated as the cover. This is a documented
limitation until M2 adds slide roles.

## 6. Rules in M1

| id | cat | severity | basis | fires when | exempt |
|---|---|---|---|---|---|
| `off-slide` | quality | error | geometry | a text-bearing shape extends more than 0.05 cm beyond the slide | a non-text shape (possible bleed) beyond the edge gets an advisory instead |
| `edge-margin` | quality | warning | geometry | a shape with text or a visible fill is closer to any edge than `edge_margin_cm − edge_margin_tolerance_cm` | shapes covering >= 95% of the slide (backgrounds); connectors |
| `dead-band` | quality | warning | geometry | on a content slide, a horizontal band with no shapes taller than `dead_band_ratio` x slide height | slide 1 (cover); full-slide backgrounds do not count as content |
| `box-overlap` | quality | **advisory** | geometry | the boxes of two text-bearing shapes intersect by more than 0.1 cm on both axes | a text shape inside a non-text backing shape (containment is not overlap) |
| `body-too-small` | quality | warning | text | a run smaller than `body_min_pt` in a paragraph longer than `caption_exempt_words` words | charts, tables, notes |
| `title-not-dominant` | quality | warning | text | the largest title-like text is smaller than `title_ratio_min` x the largest body text on that slide | KPI numerals (>= 48 pt and <= 5 words) are not title-like; slides with no body text (paragraphs over 4 words) |
| `text-contrast` | quality | warning | color | a run's contrast against its effective background is below the WCAG threshold. The effective background is the topmost filled shape beneath the run whose box fully contains the run's shape; otherwise it is the slide background | unknown colors or backgrounds (advisory) |
| `notes-missing` | quality | warning (advisory in `read`) | structure | a content slide has no speaker notes | slide 1 |
| `font-count` | quality | warning | text | the deck's text uses more than `font_family_max` distinct resolved latin families | text inside charts |
| `title-underline` | slop | warning | geometry | a non-text filled shape <= 0.35 cm tall sits with its top within 1.0 cm below the title's bottom and its left within 1.0 cm of the title's left, and is narrower than 50% of the content width | full-width hairlines (>= 50% of content width) are structure, not accent |
| `equal-card-row` | slop | warning | geometry | >= 3 filled shapes of the same size (±3%) on the same row (y ±0.2 cm) with equal gaps (±0.3 cm), each with text on it or centered over it | the shapes are linked by connectors (a process flow) |

The adapter also emits `adapter-unresolved` and `unsupported-content`, both advisory.

## 7. Render and check

- `keyline render deck.pptx -o DIR`
  - For each slide: `officecli view <deck> screenshot --page i -o DIR/slide-NN.png`.
  - Then build `DIR/contact.png`: a 3-column grid with slide numbers.
  - If OfficeCLI is missing, exit 1 with the install command.
  - Always print the known limitation L-002 (fonts fall back to sans).
- `keyline check deck.pptx [--mode] [-o DIR]`: runs lint, then render, and prints the
  findings and the PNG paths. Its exit code is lint's; a render failure gives 1.

## 8. Fixtures

- **`fixtures/golden/`**
  - `kpi-recipe.pptx` and `editorial.pptx` are provided. **Do not edit them.** Their
    build scripts are in `src/`.
  - Create `editorial-fixed.pptx`. Copy `src/editorial.sh` to
    `src/editorial-fixed.sh` and change only what fixes the true defects:
    - re-space the bottom block (`rule3` through `verdicttx`) so that every shape's
      bottom margin is >= 1.27 cm and no new warning-level finding appears;
    - change the `l3` label color so it reaches >= 4.5:1 on `F2F2F0`. `CC3322` gives
      4.61:1 at hue 6°, so it is still a signal red, not a terracotta.

    Change nothing else. `mark` at y = 1.25 cm stays; the tolerance covers it.
- **`fixtures/rules/`:** every rule has at least one positive and one negative deck,
  built by scripts committed in `fixtures/rules/src/`. Commit the `.pptx` files so
  tests never need OfficeCLI.
- **`fixtures/foreign/`**
  - At least one deck made with python-pptx from its default template, using
    title-and-content layout placeholders with no explicit `xfrm`.
  - At least one deck with nested groups whose child geometry has known absolute
    values.

## 9. Acceptance criteria

Each criterion needs evidence in `report.md`: the command, an output excerpt, and
PASS or FAIL.

**AC-1 · `kpi-recipe.pptx`, presented mode**
- Exits 2.
- Must include:
  - `dead-band` on slide 2 and on slide 4 (the bottom band)
  - `edge-margin` on the titles of slides 2, 3 and 4 (1.20 cm from the top)
  - `equal-card-row` on slide 2
- Must not include:
  - any overlap finding on slide 3 (the L-001 regression)
  - `equal-card-row` on slide 4 (its boxes are connected)
  - `dead-band` on slide 1
  - `title-not-dominant` on slide 2

**AC-2 · `editorial.pptx`, read mode**
- Exits 2.
- Must include:
  - `edge-margin` on the shapes named `verdict` (0.88 cm) and `verdicttx` (0.54 cm)
  - `text-contrast` on `l3` (E8422E on F2F2F0 = 3.57:1, at 9.5 pt)
- Must not include:
  - `edge-margin` on `mark` (1.25 cm is within the 0.05 cm tolerance)
  - `body-too-small`
  - `text-contrast` on `n3` (76 pt bold is large text, so the 3.0 threshold applies)
  - `title-underline` on `rule2` (a full-width hairline)
  - any overlap finding at warning or error severity

**AC-3 · `editorial.pptx`, presented mode**
- Must include `body-too-small` on `d1`, `d2`, `d3` (12.5 pt) and on `verdicttx` (11 pt).

**AC-4 · `editorial-fixed.pptx`, read mode**
- Exits 0.

**AC-5 · python-pptx placeholder deck**
- The title and body geometry resolve from the layout. No `adapter-unresolved` is
  emitted for them. The test asserts the expected EMU values.

**AC-6 · Nested-group deck**
- Each child's absolute geometry equals the expected values within 1 EMU.

**AC-7 · Invalid input**
- Random bytes and a `.docx` both exit 1 with a one-line reason.

**AC-8 · Determinism**
- Three runs on each golden fixture produce byte-identical JSON.

**AC-9 · Speed**
- Linting `kpi-recipe.pptx` takes under 1 s wall time in CI.

**AC-10 · Render** (skipped without OfficeCLI)
- `kpi-recipe.pptx` produces 4 slide PNGs and `contact.png`.

**AC-11 · CI**
- Green on Python 3.10 and 3.12. `ruff` is clean.

**AC-12 · Hygiene**
- `git log --format='%an <%ae>'` shows only allowed identities.
- No file is copied from `anthropics/skills`.

## Amendment log

- 2026-09-24: created.
