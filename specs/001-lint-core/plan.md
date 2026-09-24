# Plan 001: lint core

- **Spec:** [`spec.md`](spec.md) (M0 + M1)
- **Status:** approved with amendments by [audit 01](audit-01-plan.md) (2026-09-24).
  Every proposal below is marked **ACCEPTED** or **AMENDED (A-x)**; amendments are in
  the spec's amendment log, decisions D-012…D-014 in `docs/decisions.md`.
- **Branch:** `001-lint-core`

This plan says how the spec gets built. Where the spec was silent or ambiguous, the
plan made a **proposal**, marked **[P-n]**. Audit 01 ruled on every one of them
(see [§9](#9-resolution-of-open-questions)). Where a proposal was amended, the text
below already describes the amended behavior.

Facts about the golden decks quoted below were read from their XML on 2026-09-24
(`unzip -p fixtures/golden/<deck>.pptx ppt/slides/slideN.xml`). Contrast ratios
were computed with the WCAG 2.x formula and match the spec: E8422E/F2F2F0 = 3.57,
CC3322/F2F2F0 = 4.61.

---

## 1. Module layout

The layout follows the spec's suggestion. It adds four modules, each with its reason.

```
pyproject.toml                  hatchling build; console script keyline = keyline.cli:main
src/keyline/
  __init__.py                   __version__ = "0.1.0"
  __main__.py                   python -m keyline
  cli.py                        argparse: lint | rules | render | check. Thin; no logic
  lint.py            (added)    lint_path(path, mode) -> LintResult. The in-process entry
                                point that tests and `check` call, so the CLI stays thin
  model.py                      dataclasses: Deck, Slide, Shape, Paragraph, Run, Box
  units.py           (added)    EMU<->cm/pt, fixed-point rounding for messages and JSON
  geom.py            (added)    Box ops on integer EMU: intersect, contains, coverage, AABB
  findings.py                   Finding (ordered keys), sort, JSON/human writers, exit code
  registry.py                   RuleSpec, @rule decorator, REGISTRY (sorted by id)
  config.py                     loads thresholds.toml for a mode (stdlib tomllib, D-012)
  thresholds.toml               the spec §5 table; calibrated = false
  render.py                     OfficeCLI screenshots + Pillow contact sheet
  ooxml/
    ns.py                       namespace map, qualified-name helpers
    package.py                  zip + [Content_Types] check, rels, safe lxml parser, part cache
    theme.py                    clrScheme, fontScheme, fmtScheme (fill/bgFill style lists)
    color.py                    color element -> RGB, clrMap, transforms
    fill.py          (added)    shape fill + background resolution (keeps color.py small)
    placeholders.py             ph matching slide -> layout -> master
    geometry.py                 xfrm read, placeholder inheritance, group composition, rotation
    text.py                     paragraph/run property cascade
    adapter.py                  builds the Deck model; collects adapter diagnostics
  rules/
    __init__.py                 imports every rule module (registration by import)
    _common.py                  shared predicates: text_bearing, visible_fill, is_background,
                                is_content_slide, pick_title, words()
    off_slide.py  edge_margin.py  dead_band.py  box_overlap.py  body_too_small.py
    title_not_dominant.py  text_contrast.py  notes_missing.py  font_count.py
    title_underline.py  equal_card_row.py
tests/
  conftest.py                   fixture paths, lint() helper, officecli skip marker
  unit/                         units, geom, color transforms, config, findings ordering
  adapter/                      cascade tests on small hand-written XML packages (in-memory)
  rules/                        test_<rule>.py: every rule's positive and negative decks
  acceptance/                   test_ac01_kpi.py … test_ac12_hygiene.py, one file per AC
fixtures/
  golden/  editorial.pptx  kpi-recipe.pptx  editorial-fixed.pptx (new)
           src/editorial.sh  src/kpi-recipe.sh  src/editorial-fixed.sh (new)
  rules/   <rule-id>--pos[-N].pptx  <rule-id>--neg[-N].pptx
           src/build_rules.py  src/_deck.py (python-pptx helpers)
  foreign/ pptx-default-placeholders.pptx  nested-groups.pptx
           src/build_foreign.py
  expected/ <deck>.<mode>.json  lint output snapshots for goldens (reviewed by hand)
.github/workflows/ci.yml        ruff + pytest, ubuntu-latest, Python 3.11 and 3.13 (D-012)
docs/adapter.md                 supported OOXML subset, transforms, known gaps (spec §2.4)
```

Dependency direction: `rules → model/geom/units/config`. `ooxml → model`. Rules never
touch XML. `cli → lint → (ooxml.adapter, registry, findings)`. `render` imports
nothing from `ooxml`.

Package reading safety: every part is parsed with
`lxml.etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False)`. The
zip is rejected (exit 1) if its total uncompressed size exceeds a cap (proposed 512 MB)
or it has no `ppt/presentation.xml`.

---

## 2. Adapter resolution order

All lengths are integer EMU. Every lookup below reads only the parts the relationships
reach: presentation → slide → layout → master → theme. Parts are never found by
filename or position (L-001).

### 2.1 Slide order, size, layout, notes

1. `ppt/presentation.xml` `p:sldSz@cx/@cy` gives the slide size.
2. `p:sldIdLst/p:sldId` gives document order. Each `@r:id` resolves through
   `ppt/_rels/presentation.xml.rels`. The slide index is the 1-based position in
   this list.
3. The slide rels have one `…/slideLayout` target. The layout name is
   `p:cSld@name`. The layout rels have one `…/slideMaster` target. The master rels
   have one `…/theme` target.
4. **Notes.** The slide rels may have a `…/notesSlide` target. `has_notes` is true
   when that part's `p:sp` elements with `p:ph@type="body"` hold non-whitespace
   `a:t` text. **[P-1 · ACCEPTED]** Only body placeholders count. A slide-number field
   (`sldNum` placeholder) is not a note.

### 2.2 Geometry

Per shape, in this order:

1. **Own transform.** For `p:sp`, `p:pic` and `p:cxnSp`: `p:spPr/a:xfrm` (`a:off`,
   `a:ext`, `@rot`, `@flipH`, `@flipV`). For `p:graphicFrame`: `p:xfrm`.
2. **Placeholder inheritance** (spec §2.1). When the transform is missing and the
   shape has `p:nvPr/p:ph`, match a placeholder on the layout and use its `a:xfrm`.
   If that is missing too, match on the master and use the master's `a:xfrm`.
   Matching follows `placeholders.py` **[P-2 · AMENDED (A-6)]**:
   - The slide `ph@type` defaults to `obj` and `ph@idx` defaults to `0`.
   - **Layout:** match by `idx` first (python-pptx 1.0.2 semantics). If no layout
     placeholder has that idx, fall back to the first with the same `type`. The type
     fallback is keyline-only and documented in `docs/adapter.md`.
   - **Master:** match by type after mapping to master types: `ctrTitle→title`;
     `subTitle, obj, body, tbl, chart, dgm, media, clipArt, pic→body`; `dt, ftr,
     sldNum, hdr` stay the same.
3. **Unresolved.** If there is still no geometry, the shape's box is `None` and the
   adapter emits `adapter-unresolved`. Rules that need a box skip the shape.
4. **Groups** (spec §2.3). The `p:grpSp` elements are walked recursively in document
   order. The spTree `p:grpSpPr` is the identity. For each enclosing group, from
   innermost to outermost:
   `x' = off.x + (x − chOff.x) · ext.cx / chExt.cx`, and the same for `y`.
   `w' = w · ext.cx / chExt.cx`, `h' = h · ext.cy / chExt.cy`. A zero `chExt` gives
   scale 1. The arithmetic uses `fractions.Fraction` and rounds to int once at the
   end (half away from zero), so AC-6 holds to ±1 EMU.
   **[P-3 · ACCEPTED]** Group rotation is applied by rotating the child's center about the
   group's center and adding the rotations. Group flips mirror the child's center.
   The spec does not cover either case.
5. **Rotation** (spec §2.7). `rot` is in 60000ths of a degree. The final box is the
   axis-aligned bounding box of the rotated rectangle about its center:
   `W = |w·cosθ| + |h·sinθ|`, `H = |w·sinθ| + |h·cosθ|`. Multiples of 90° are
   special-cased exactly. Other angles use float math, rounded once to int.

The model keeps the unrotated `x y w h`, the `rot`, and a derived `box`, which is the
AABB. Rules use `box`.

### 2.3 Text properties (size, bold, italic, caps, spacing, latin font, color)

Each run property resolves through one cascade: the A-4 order for size, which the
other properties share **[P-4 · ACCEPTED]**. `N` is `a:pPr@lvl + 1` (default 1).
Steps 3–4 apply to placeholders only.

| step | source | OOXML |
|---|---|---|
| 1 | run | `a:r/a:rPr@sz` (`@b @i @cap @spc`, `a:latin@typeface`, `a:solidFill`) |
| 2 | shape list style | `p:txBody/a:lstStyle/a:lvlNpPr/a:defRPr` |
| 3 | layout placeholder | matched layout placeholder `p:txBody/a:lstStyle/a:lvlNpPr/a:defRPr` |
| 4 | master placeholder **[P-5 · AMENDED (A-4)]** | matched master placeholder `p:txBody/a:lstStyle/a:lvlNpPr/a:defRPr` |
| 5 | master text styles | `p:txStyles/p:titleStyle` for `title`/`ctrTitle`; `p:bodyStyle` for other placeholders; `p:otherStyle` for non-placeholder shapes, each `a:lvlNpPr/a:defRPr` |
| 6 | presentation default **[P-6 · AMENDED (A-4)]** | `p:presentation/p:defaultTextStyle/a:lvlNpPr/a:defRPr` |
| 7 | shape style (color and font only) **[P-7 · ACCEPTED]** | `p:style/a:fontRef` (`@idx` major/minor → theme font; child color) |
| 8 | fallback | size: `None` → `adapter-unresolved` (spec). Color: `tx1` through the clrMap. Font: `None` → `adapter-unresolved` |

A-4 drops `a:pPr/a:defRPr` from the cascade. `docs/adapter.md` records this as
PowerPoint behavior that has not been verified against PowerPoint.

- **Units.** `sz` is in hundredths of a point and is stored as an int (`size_pt` is
  `sz / 100`). `spc` is in hundredths of a point.
- **Theme fonts** (spec §2.5). `+mj-lt` and `+mn-lt` map to the theme's
  `a:majorFont/a:latin` and `a:minorFont/a:latin`. Other `+..-..` tokens resolve to
  `None` and emit an advisory.
- **Autofit.** `a:bodyPr/a:normAutofit@fontScale` is **not applied** in M1. Sizes are
  nominal. See R-2.

### 2.4 Color (spec §2.4)

A color element resolves like this:

- `a:srgbClr@val` → RGB.
- `a:sysClr@lastClr` → RGB. (The theme's `dk1`/`lt1` are `sysClr` in both goldens.)
- `a:schemeClr@val`:
  - `bg1 tx1 bg2 tx2` map through the clrMap. The clrMap is the master's `p:clrMap`,
    overridden by `p:clrMapOvr/a:overrideClrMapping` on the layout or the slide
    **[P-8 · ACCEPTED]**. (The spec says "master's clrMap". Overrides are rare but real.)
  - Then the theme's `a:clrScheme` (`dk1 lt1 dk2 lt2 accent1-6 hlink folHlink`).
  - `phClr` takes the color that the referencing `a:fillRef`/`a:fontRef`/`a:bgRef`
    carries.
- `a:prstClr`, `a:hslClr`, `a:scrgbClr` → `None` plus an advisory **[P-9 · ACCEPTED]**.

**Transforms**, applied in document order:

| transform | formula (documented in `docs/adapter.md`) |
|---|---|
| `lumMod`, `lumOff` | RGB→HSL; `L = L·lumMod + lumOff`, clamped to [0,1]; HSL→RGB |
| `tint` | per sRGB channel: `c + (1 − c)·(1 − tint)` (LibreOffice/python-pptx convention, see R-4) |
| `shade` | per channel: `c · shade` |
| `alpha` | **[P-9 · ACCEPTED]** `alpha = 100%` is ignored. Anything lower → `None` plus an advisory (an unblended color would give a false contrast) |
| anything else | `None` + `adapter-unresolved` naming the transform |

### 2.5 Shape fill

Fill resolves in this order:

1. `p:spPr` children: `a:solidFill` → `solid:#RRGGBB`; `a:gradFill` → `gradient`;
   `a:noFill` → `none`; `a:blipFill`/`a:pattFill` → `unknown`; `a:grpFill` → the
   enclosing group's resolved fill.
2. Placeholder inheritance from the layout and then the master `p:spPr`, with the
   same matching as §2.2.
3. `p:style/a:fillRef`: `idx="0"` → `none`. Otherwise use the theme
   `a:fmtScheme/a:fillStyleLst[idx]`. If that entry is `a:solidFill`, its `phClr`
   takes the fillRef's color. Otherwise → `gradient`/`unknown`.
4. `none`.

A `p:pic` has fill `unknown` (an image). A `graphicFrame` has fill `none`, and rules
treat it as visible content through its kind.

### 2.6 Background (spec §2.6)

1. Look at the slide `p:cSld/p:bg`, then the layout's, then the master's. The first
   one present wins.
2. Inside `p:bg`:
   - `p:bgPr/a:solidFill` → solid.
   - `p:bgPr` with `a:gradFill`, `a:blipFill` or `a:pattFill` → `unknown`.
   - `p:bgPr/a:noFill` → `#FFFFFF` plus `adapter-unresolved` (`what =
     background-default`) **[P-10 · AMENDED (A-5)]**.
   - `p:bgRef@idx` plus a child color: 1–999 index `a:fillStyleLst`; ≥1001 index
     `a:bgFillStyleLst` (idx − 1000); 0 means none. A solid entry with `phClr` → the
     bgRef color, so it counts as **solid** **[P-10 · ACCEPTED]**. Anything else → `unknown`.
3. If no `p:bg` is found anywhere → `#FFFFFF` plus one `adapter-unresolved`
   advisory (`what = background-default`) **[P-10 · AMENDED (A-5)]**. PowerPoint
   paints these white. Both goldens set `p:bg` on every slide, and neither their
   layouts nor their masters have one.

### 2.7 Adapter diagnostics

- `adapter-unresolved` is emitted once per `(slide, shape_id, what)`. `what` is one
  of: `geometry`, `size`, `font`, `color`, `background`, `background-default`,
  `transform:<name>`.
- `unsupported-content` is emitted once per `(slide, shape_id)` for:
  - `graphicFrame:other` (SmartArt, OLE, media);
  - `mc:AlternateContent` (the adapter reads `mc:Fallback`, **[P-11 · ACCEPTED]**: audit 01 approved the
    plan with no separate ruling on this one);
  - `a:tbl` text, which is not modeled in M1;
  - `p:contentPart`.

---

## 3. Findings, registry, config

- **Finding keys.** `rule, category, severity, slide, shape_id, shape_name, message,
  measured, threshold`, built as an ordered dict. **[P-12 · ACCEPTED]** `measured` and
  `threshold` are JSON numbers in the unit the message states: cm with 2 decimals,
  pt with up to 2 decimals, ratios with 2 decimals, counts as ints. `null` when not
  applicable.
- **Sort key.** `(slide, rule, shape_id with null first, message)` **[P-13 · ACCEPTED]**. The
  spec's key `(slide, rule, shape_id)` has ties: kpi slide 4 gets two `dead-band`
  findings with `shape_id` null. `message` breaks ties deterministically.
- **JSON.** `json.dumps(list, ensure_ascii=False, indent=2) + "\n"` on stdout. Floats
  come only from `units.round2()`, which uses `Decimal` quantize with
  `ROUND_HALF_UP`, so their repr is stable across 3.11 and 3.13.
- **Stderr.** One line per finding (`slide 2 · edge-margin · T2 · 1.20 cm from top
  edge (min 1.27 cm)`), then a summary (`14 findings: 1 error, 11 warning, 2
  advisory`).
- **Exit codes.** 1 is for a scan failure, with a one-line reason. 2 means there is at
  least one `warning` or `error`. 0 otherwise.
- **Registry.** A `RuleSpec` has `id category severity scope basis since summary
  rationale`. **[P-14 · ACCEPTED]** Some findings need a different severity by mode or case
  (`notes-missing` is advisory in read mode; `off-slide` is an advisory for bleed;
  some rules emit advisories when they have to skip). For these, `RuleSpec.severity`
  is the default, and findings carry their actual severity. A `severity_notes`
  string in `keyline rules` output documents the overrides.
  **[P-15 · ACCEPTED]** `adapter-unresolved` and `unsupported-content` are registered too
  (category `quality`, basis `structure`, severity `advisory`), so `keyline rules`
  lists everything that can appear in the output.
- **Rationale** per rule: `off-slide` L-003; `edge-margin` L-006; `dead-band` L-003;
  `box-overlap` L-005; `body-too-small` research §"The canon agrees on 'one claim per
  slide'…"; `title-not-dominant` same; `text-contrast` L-006; `notes-missing`
  research §canon; `font-count` research §"ANTI-TELLS.md should start…";
  `title-underline` research §"ANTI-TELLS.md…"; `equal-card-row` L-004. The exact
  section titles get checked against `docs/research.md` in T-12.
- **Config.** `thresholds.toml` has `calibrated = false` and one table each for
  `[presented]` and `[read]`. `large_text` becomes two keys, `large_text_pt = 18` and
  `large_text_bold_pt = 14`. Thresholds are read as strings of decimals into
  `Decimal`/`Fraction`, so boundary comparisons are exact. The file is read with the
  stdlib `tomllib` (D-012: Python ≥ 3.11).

---

## 4. How each rule measures

Definitions shared through `rules/_common.py`:

- **text-bearing:** a `sp` with at least one run of non-whitespace text.
  **[P-16 · ACCEPTED]** Charts and tables are not text-bearing in M1. Their text is not modeled.
- **visible:** text-bearing, or fill ≠ `none`, or kind `pic`, `graphicFrame:*`.
- **background shape:** a visible shape whose box, clipped to the slide, covers
  ≥ 95% of the slide area **[P-17 · ACCEPTED]**.
- **content slide:** slide index > 1 (spec §5 cover rule).
- **words(text)** **[AMENDED (A-7)]**: the number of whitespace-separated tokens
  that contain at least one letter or digit, so `·`, `|` and `—` are not words.
- **title (`pick_title`)** **[P-18 · AMENDED (A-1)]**: if the slide has a `title` or
  `ctrTitle` placeholder with text, that shape. Otherwise, among the slide's
  text-bearing shapes that are not KPI numerals, the one with the largest max run
  size, with ties going to the earliest in z-order. A shape is a **KPI numeral** when
  its max run size ≥ 48 pt and its whole text has ≤ 5 words (Q3 accepted: per shape).
- **body paragraph** **[AMENDED (A-2)]**: a paragraph with `words >
  caption_exempt_words`, in a text-bearing shape that is not the title. It is shared
  by `body-too-small` and `title-not-dominant`.
- All comparisons use integer EMU. Thresholds in cm are converted once
  (`1 cm = 360000 EMU`).

| rule | measurement |
|---|---|
| `off-slide` | For each shape with a box: `overrun = max(0, −left, −top, right − W, bottom − H)`. It fires when `overrun > 18000 EMU` (0.05 cm). Text-bearing → `error`. Otherwise → `advisory` ("possible bleed"). `measured` = overrun in cm. |
| `edge-margin` | Candidates are the *visible* shapes: text-bearing, fill ≠ `none`, `pic`, or any `graphicFrame` **[P-19 · AMENDED (A-3)]**. Background shapes and `cxnSp` are excluded. Shapes already reported by `off-slide` are skipped **[P-20 · ACCEPTED]**. For each side, margin = the distance to that edge. It fires when `min(margins) < 439200 EMU` (1.27 − 0.05 cm). **One finding per shape** **[P-21 · ACCEPTED]**: it names the worst side, `measured` = that margin, `threshold` = 1.27. |
| `dead-band` | On content slides: collect `[top, bottom]` of every visible non-background shape, including `cxnSp`, even at zero height **[P-22 · ACCEPTED]**. Clip to `[0, H]` and merge overlapping or touching intervals. The gaps are `[0, first]`, the gaps between intervals, and `[last, H]`. It fires for each gap `> 0.25·H` (strict), with `shape_id` null, `measured` = gap/H and the band's cm span in the message. On kpi slide 4 this also fires for the middle band (3.20 to 8.00 cm = 25.2%), not only the bottom one. |
| `box-overlap` | For every pair of text-bearing shapes: `ox = min(r) − max(l)`, `oy = min(b) − max(t)`. It fires when both are `> 36000 EMU` (0.1 cm). Severity is `advisory`. **[P-23 · ACCEPTED]** The spec's exemption ("a text shape inside a non-text backing shape") can't occur between two text-bearing shapes, and audit 01 removed it as a spec error. Kpi's backing cards have no text, so they are never in a pair. `shape_id` is the lower id of the pair, and both names appear in the message. |
| `body-too-small` | For each text-bearing `sp` (charts, tables and notes are never in the model's slide text): for each body paragraph (A-2), look at its runs whose size is known. It fires if any of them is `< body_min_pt`. **One finding per shape** **[P-24 · ACCEPTED]**, with `measured` = the smallest such size. Runs with unknown size are skipped (the adapter already reported them). |
| `title-not-dominant` | `t` = the title's max run size. `b` = the max run size over body paragraphs, which by definition exclude the title **[P-25 · AMENDED (A-2)]**. It skips when there is no title or no body paragraph. It fires when `t < title_ratio_min · b` (exact `Fraction`). `measured` = `t/b`. Without excluding the title, kpi slide 2 would fire: its title "What a text-only gate cannot see" has 6 words, and AC-1 forbids that finding. |
| `text-contrast` | For each text-bearing shape, for each run with text: fg = the resolved color. bg = the first shape found walking **down** the z-order from **this shape itself** **[P-26 · ACCEPTED]** whose box **contains the shape's box, edges inclusive** **[P-27 · ACCEPTED]**, and whose fill ≠ `none`. With no such shape, bg is the slide background. Solid → WCAG 2.x ratio. `gradient`/`unknown`/`pic`, or an unknown fg → `advisory` under this rule id. Large text = size ≥ `large_text_pt`, or bold and ≥ `large_text_bold_pt`. It fires when `ratio < contrast_large or contrast_normal`. One finding per shape, for the worst run. `measured` = ratio (2 dp). This finds `l3` (3.57 < 4.5). It does not flag `n3` (76 pt bold, so the 3.0 threshold applies). |
| `notes-missing` | On content slides with `has_notes == false`: `warning` in presented mode, `advisory` in read mode. `shape_id` is null. |
| `font-count` | Deck level (`slide` 0). The set of resolved `latin` typefaces over runs with text, in every slide shape (groups flattened, notes excluded, charts and tables not modeled). Families are normalized **[P-28 · AMENDED (A-8)]**: case-fold, then strip one trailing token from `{thin, extralight, ultralight, light, regular, book, medium, semibold, demibold, bold, extrabold, ultrabold, black, heavy, condensed, narrow}`. So `Calibri` and `Calibri Light` are one family. It fires when the count > `font_family_max`. The message lists them sorted. |
| `title-underline` | The title comes from `pick_title` (A-1). Candidates are `sp` shapes with no text, fill ≠ `none`, and `h ≤ 0.35 cm`, where `title.top + 0.5·title.h ≤ top ≤ title.bottom + 1.0 cm` **[P-29 · AMENDED (A-9)]** and `|left − title.left| ≤ 1.0 cm` and `w < 0.5 · content_width`, with `content_width = W − 2·edge_margin_cm` (accepted). Outline-only lines are out of scope for M1 (backlog). In editorial, `rule2` (29.47 cm ≥ 15.67 cm) is exempt under any reasonable definition. |
| `equal-card-row` | Candidates: visible non-background `sp` with fill ≠ `none`. **Rows** **[P-30 · ACCEPTED]**: sort by (top, left). A shape joins the current row if its top is within ±0.2 cm of the row's first shape. Otherwise it starts a new row. Within a row, sort by left and scan for maximal runs of ≥ 3 consecutive shapes where each `w`, `h` is within ±3% of the run's first shape, each gap (`left[i+1] − right[i]`, ≥ 0) is within ±0.3 cm of the first gap, and every shape **carries text or has a text-bearing shape over it**. "Over it" means that shape's box is inside the card, edges inclusive, and its horizontal center is within ±3% of the card's width from the card's center **[P-31 · ACCEPTED]**. **Exempt** **[P-32 · ACCEPTED]** if the `cxnSp` shapes whose `stCxn`/`endCxn` both point at run members connect all members into one component. One finding per run: `shape_id` = the first card, `measured` = the count. |

Advisories that rules emit when they have to skip (spec §2.6, text-contrast exempt)
use the rule's own id with severity `advisory` (P-14, accepted).

---

## 5. Fixtures

### 5.1 Golden

- `kpi-recipe.pptx` and `editorial.pptx` are not touched. A test checks their SHA-256
  against values recorded in T-13.
- **`editorial-fixed.pptx`.** `src/editorial-fixed.sh` is a copy of `editorial.sh`.
  Its diff touches only the `y` values of `rule3 … verdicttx` and the `l3` color
  (`E8422E → CC3322`). Constraint arithmetic:
  - `verdicttx` must end at ≤ 17.78 cm. It ends at 18.51 now, so it has to rise
    ≥ 0.73 cm.
  - Only 0.60 cm of space sits between the `d1–d3` boxes (bottom 12.55) and `rule3`
    (13.15).
  - A plain shift is therefore not enough, and the internal gaps have to shrink.
  - Candidate: `rule3` 12.85, `ftlab` 13.15, row pitch 1.05 → 1.00 (`r1*` 14.00, `hr1`
    14.80, `r2*` 15.00, `hr2` 15.80, `r3*` 16.00), `verdicttx` 16.90 (ends at 17.75,
    margin 1.30), and `verdict` 16.99.
  - Audit 01 accepted this as re-spacing and judges "no new warning" in read mode.
  - Shape heights do not change. The final numbers are chosen during T-21. Evidence:
    the lint JSON (AC-4) and one OfficeCLI screenshot, which is committed only to the
    report, not as a fixture.
- `fixtures/expected/*.json` hold reviewed lint output for each golden in each mode.
  A snapshot test diffs against them, so any behavior change shows up in review.

### 5.2 Rule fixtures (`fixtures/rules/`)

- **Builder.** One script, `src/build_rules.py`, uses python-pptx and the helpers in
  `src/_deck.py`: blank 16:9 deck, `text()`, `rect()`, `connector()`, `notes()`.
  Every deck sets `core_properties.author` and `last_modified_by` to `Tyler` (see
  R-5).
- **Expectation file.** Each deck's expectation lives next to it in
  `fixtures/rules/expect.toml`: rule, mode, required finding ids or shape names, and
  forbidden ones.
- **Reproducibility test.** The builder runs into `tmp_path`, and the test compares
  each part's canonical XML (C14N, `docProps/*` excluded) with the committed deck.
  The zip bytes differ, because python-pptx writes zip timestamps.

| rule | positive (must fire) | negative (must not fire at warning or error) |
|---|---|---|
| `off-slide` | Text box running 1.0 cm past the right edge (error). A 30° rotated text box whose AABB crosses the bottom edge although its unrotated box doesn't (error). A filled rect 2 cm past the left edge (advisory only) | Text box ending 0.04 cm past the edge. Text box fully inside |
| `edge-margin` | Text 1.00 cm from the left. Filled rect 0.50 cm from the bottom. Picture 0.8 cm from the top | Text at 1.25 cm (tolerance). A full-slide background rect. A connector 0.2 cm from the edge. An empty, unfilled text box 0.3 cm from the edge |
| `dead-band` | Slide 2: all content in the top 45% | Same layout on slide 1 (cover). Slide 2 with a full-slide background rect plus content spread evenly |
| `box-overlap` | Two text boxes overlapping 1.0 × 1.0 cm (advisory) | Overlap of 0.05 cm on one axis. Text box inside a filled card with no text |
| `body-too-small` | Presented: 14 pt, 8-word paragraph | 14 pt, 5-word caption. The same 12 pt, 8-word deck in read mode (the 11 pt floor) |
| `title-not-dominant` | Title 24 pt, 10-word body 18 pt | Title 44 pt, body 18 pt. A 72 pt one-word KPI and a 24 pt title with 10-word 10 pt body (the KPI is not the title). A slide with no paragraph over 4 words |
| `text-contrast` | 9.5 pt E8422E on F2F2F0 slide bg. CADCFC text inside a white card on a dark slide (backing shape wins over slide bg) | 76 pt bold E8422E on F2F2F0 (large). White text in a text box inside a 1E2761 card with equal edges. A gradient background gives an advisory only |
| `notes-missing` | Slide 2 with no notes slide. Slide 2 whose notes hold only whitespace | Slide 2 with notes. Slide 1 without notes. The positive deck in read mode is advisory only |
| `font-count` | Runs in Georgia, Calibri and Arial | Georgia and Calibri, plus a chart whose text is Arial. `+mn-lt` resolving to the same family as an explicit `Calibri` |
| `title-underline` | 3 cm × 0.15 cm rect 0.4 cm below the title, left-aligned | A full-width hairline. A bar above the title. A bar 1.5 cm below. A bar offset 2 cm right |
| `equal-card-row` | Three equal filled rects with their own text. Three equal cards with centered text boxes over them (the kpi pattern) | The positive deck with connectors between the cards. Widths differing by 10%. Equal cards with gaps 0.5/1.5 cm. Two cards only |

### 5.3 Foreign fixtures (`fixtures/foreign/`, `src/build_foreign.py`)

- **`pptx-default-placeholders.pptx` (AC-5).**
  - The deck is `Presentation()`, with no template argument, and layout 1 ("Title and
    Content"). The title and body placeholders are filled, and the builder writes no
    `a:xfrm`. The test asserts that no `a:xfrm` exists in the slide.
  - The expected EMU values are pinned as literals in the test. They are
    cross-checked two ways: against the layout's `a:xfrm` read by hand, and against
    python-pptx's own inherited `placeholder.left/top/width/height`. python-pptx is an
    independent implementation, so it serves as the oracle.
  - Sizes resolve from the master `txStyles` (title 44 pt, body lvl1 32 pt). The
    background resolves through `p:bgRef idx=1001` → `bg1` → `lt1`, so this deck
    also exercises the `bgRef` path of P-10.
- **`nested-groups.pptx` (AC-6).**
  - python-pptx only writes identity group transforms, so the builder writes raw
    `p:grpSp` XML with lxml instead.
  - The outer group has `off=(1 cm, 1 cm)`, `ext=(10 cm, 5 cm)`, `chOff=(0, 0)` and
    `chExt=(20 cm, 10 cm)`, which is scale 0.5.
  - The inner group has scale 2 and a non-zero `chOff`. Three leaf rects sit at
    known positions.
  - The expected absolute values are worked out by hand in the builder's docstring
    and pinned as literals in the test.
  - A third, rotated (90°) inner group is included (P-3 accepted; audit 01 asked
    for it in the AC-6 fixture).
- **Adapter unit fixtures.** Small XML packages built in memory by
  `tests/adapter/_pkg.py` cover these cases: the text cascade, including `lvl`;
  clrMap and overrides; each transform; `bgRef`; `fillRef`; `grpFill`; `sysClr`;
  unsupported colors. They are not committed as `.pptx`.

### 5.4 Invalid inputs (AC-7)

Tests generate these in `tmp_path`: 4 KiB from `random.Random(0)`, and a minimal
`.docx` zip (`[Content_Types].xml` + `word/document.xml`) written with `zipfile`.
python-docx is not needed.

---

## 6. Render and check

- **`render.py`**
  - Finds `officecli` on `PATH`. If it is missing, exit 1 with
    `npm install -g @officecli/officecli`.
  - Runs `officecli view <deck> screenshot --page i -o DIR/slide-NN.png` for each
    slide.
  - Builds `contact.png` with Pillow: a 3-column grid, 16 px gutters, and slide
    numbers drawn with `ImageFont.load_default()`.
  - Always prints L-002 to stderr.
- **`check`**
  - Runs lint and then render. With `--json`, stdout holds the lint JSON only, and
    the PNG paths go to stderr **[P-33 · AMENDED (A-10)]**.
  - The exit code is lint's. Render is best effort: if OfficeCLI is missing or render
    fails, `check` prints `render: skipped (<reason>)` to stderr and keeps lint's
    code. `--require-render` turns a render failure into exit 1.

---

## 7. Test and CI plan

- **pytest markers.** `officecli` (skipped when the binary is missing) and `slow`.
- **CI.** `.github/workflows/ci.yml` runs on `ubuntu-latest` with the matrix
  `["3.11", "3.13"]` (D-012). Steps: `pip install -e .[dev]`, `ruff check`, `ruff format
  --check`, `pytest -q`.
- **AC-9.** The test times `subprocess.run([sys.executable, "-m", "keyline", "lint",
  kpi])` with `time.perf_counter`, so interpreter start is included. The budget is
  < 1.0 s.
- **AC-12.** `tests/acceptance/test_ac12_hygiene.py` checks four things:
  - `git log --format='%an <%ae>%n%cn <%ce>'` and every trailer against the D-014
    allowlist: names `Tyler`/`tyler-void` with `code@tyler-void.dev`; Claude
    `Co-Authored-By` trailers with `noreply@anthropic.com` (D-013); and
    `GitHub <noreply@github.com>` as committer. The test skips when there is no
    `.git`.
  - Every fixture's `docProps/core.xml` creator and `lastModifiedBy`.
  - There is no file whose name or content hash matches an `anthropics/skills`
    file. This is a manual audit step in the report, because the lint core makes no
    network calls and the check needs a fetch.
  - `NOTICE` exists.

---

## 8. Risks

| id | risk | mitigation |
|---|---|---|
| R-1 | **Inheritance fidelity.** PowerPoint's real cascade differs from the spec's in places. PowerPoint ignores `pPr/defRPr` for runs, uses the master placeholder `lstStyle`, and styles text boxes from `defaultTextStyle`. Neither golden has `txStyles` or `defaultTextStyle`. They pass only because every run has an explicit `sz`. Foreign decks will expose any gap. | A-4. The foreign fixtures. `docs/adapter.md` lists the known gaps. |
| R-2 | **Autofit ignored.** `normAutofit@fontScale` shrinks the rendered text. `body-too-small` would under-report on shrunk decks. | Documented. Proposed for M2+ as a separate `autofit-shrunk` rule, not built now. |
| R-3 | **Boundary values in the goldens.** kpi slide 3 title/body is exactly 2.00. kpi slide 4 middle band is 25.2%. `6E6E68` on F2F2F0 is 4.58 (vs 4.5). kpi labels share card edges exactly. `mark` is at 1.25 vs 1.22. `l1`/`n1` overlap is exactly 0.10 cm. | Integer EMU and exact `Fraction`/`Decimal` comparisons everywhere. No float in any threshold test. The snapshot JSON makes drift visible. |
| R-4 | **tint/shade semantics.** Implementations disagree (sRGB vs linear, HSL vs RGB). There is no PowerPoint available to arbitrate. | Pick one convention and document it. Unit-test the formula, not "PowerPoint parity". The report lists it as uncalibrated. |
| R-5 | **Fixture metadata identity.** python-pptx's default template may carry third-party author metadata. OfficeCLI decks say `OfficeCLI` (a tool, not a person). | The builders overwrite `author`/`last_modified_by`. The AC-12 test scans every fixture. |
| R-6 | ~~Python 3.10 has no `tomllib`.~~ **Closed by D-012**: Python ≥ 3.11, stdlib `tomllib`. | — |
| R-7 | **Untrusted input.** A zip bomb, XXE, or an XML billion-laughs attack. | The safe parser (§1), an uncompressed-size cap, and a ZIP member count cap. A test exercises each one. |
| R-8 | **Box heuristics on foreign decks.** Title detection without placeholders, card detection and containment are uncalibrated (constitution V). | Every threshold lives in config. The report says "uncalibrated". No tuning to the goldens (CLAUDE hard rule). |
| R-9 | **OfficeCLI drift.** `render` is tested only locally (1.0.152 here), never in CI. | AC-10 is marked `officecli`. The report records the version used. |
| R-10 | **`mc:AlternateContent`, SmartArt, OLE, tables.** Content the model can't see creates silent false negatives. | `unsupported-content` advisories make the gap visible. |
| R-11 | **Speed.** AC-9 includes interpreter start and lxml import (~0.1–0.2 s). | Parts are parsed once and cached. No per-shape XPath compilation. Profiled in T-19. |
| R-12 | ~~Commit identity.~~ **Closed by D-013 and D-014**: trailers allowed, current identity kept, no rewrite. | AC-12 uses the D-014 allowlist. |

---

## 9. Resolution of open questions

Audit 01 ruled on every open question. Nothing is pending. The table shows where each
proposal ended up; the rulings themselves are in [`audit-01-plan.md`](audit-01-plan.md).

| P | status | | P | status |
|---|---|---|---|---|
| P-1 | ACCEPTED | | P-18 | AMENDED (A-1) |
| P-2 | AMENDED (A-6) | | P-19 | AMENDED (A-3) |
| P-3 | ACCEPTED (rotated group in AC-6 fixture) | | P-20 | ACCEPTED |
| P-4 | ACCEPTED | | P-21 | ACCEPTED |
| P-5 | AMENDED (A-4) | | P-22 | ACCEPTED |
| P-6 | AMENDED (A-4) | | P-23 | ACCEPTED (exemption removed) |
| P-7 | ACCEPTED (fallback `tx1`) | | P-24 | ACCEPTED (word counting: A-7) |
| P-8 | ACCEPTED | | P-25 | AMENDED (A-2) |
| P-9 | ACCEPTED | | P-26 | ACCEPTED |
| P-10 | AMENDED (A-5); `bgRef` solid accepted | | P-27 | ACCEPTED |
| P-11 | ACCEPTED (no separate ruling; plan approved) | | P-28 | AMENDED (A-8) |
| P-12 | ACCEPTED | | P-29 | AMENDED (A-9); `content_width` accepted |
| P-13 | ACCEPTED | | P-30 | ACCEPTED |
| P-14 | ACCEPTED | | P-31 | ACCEPTED |
| P-15 | ACCEPTED | | P-32 | ACCEPTED ("linked" = one connected component) |
| P-16 | ACCEPTED | | P-33 | AMENDED (A-10); JSON behavior accepted |
| P-17 | ACCEPTED | | | |

Other questions: KPI numeral per shape (Q3), editorial-fixed re-spacing and read-mode
judgment (Q27), the python-pptx oracle for AC-5 (Q28) and a whole-process AC-9 budget
(Q30) were accepted. R-6 is closed by D-012; R-12 by D-013 and D-014.
