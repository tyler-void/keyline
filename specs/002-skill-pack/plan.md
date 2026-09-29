# Plan 002: skill, brief and the Swiss pack

- **Spec:** [`spec.md`](spec.md) (M2). "A-n" means a spec 001 amendment, as in the spec.
- **Status:** approved with amendments by [audit 01](audit-01-plan.md) (2026-09-27): every
  proposal below is accepted except Q-7 (overruled by B-2); Q-20's open choice is made.
  Amendments B-1 … B-7 are in the spec's amendment log.
- **Amendment B-8** (systems and voices, D-020; [amendment-B8-voices.md](amendment-B8-voices.md),
  2026-09-29): a pack is one system plus voices. It arrived after T-09 part 2 had landed
  (`b35ff05`), so it reworks T-08 and T-09 and adjusts T-10, T-12, T-17 and T-18. The
  sections below are updated in place; the new ambiguities are Q-26 … Q-41.
- **Audit 02** ([audit-02-a1.md](audit-02-a1.md), 2026-09-29) of phase A1: FIX, then A2.
  Its rulings on Q-24 and Q-26 … Q-41 are marked below; amendments B-9 … B-15 are in the
  spec's amendment log; the fixes are in [`report.md`](report.md) (A1 fixes). The A2
  tasks follow §3 and the audit's "Carry into A2".
- **Audit 03** ([audit-03-a1fix.md](audit-03-a1fix.md), 2026-09-29) of the A1 fix round:
  FX-1 … FX-8 accepted; a second fix round FX-9 … FX-15 (B-16 … B-20), then A2 without
  another audit stop. Its rulings on Q-42 … Q-46 are marked below and in the A2 tasks;
  B-18 supersedes Q-30's "`[why]` keys that are not roles are ignored".
- **Branch:** `002-skill-pack`, from `main` at `678c69a`.
- **Decisions:** D-015 … D-019 are recorded in `docs/decisions.md` (commit `bb27a9b`);
  D-020 (B-8) supersedes D-017's "Arial only".

This plan covers all three phases (A1, A2, B). Only **A1** is broken down into tasks
([`tasks.md`](tasks.md)); A2 and B are broken down after the A1 audit, when their
inputs (the pack, the regions, the template) exist. Where the spec is silent or
self-contradictory the plan makes a proposal, marked **[Q-n]** and listed in
[§9](#9-open-questions).

**Checked before writing** (commands in the reply that delivered this plan):

- `product.toml` SHA-256 is `9b0fea6e…586f8b`, as §10 requires.
- All eight §3.3 colour anchors reproduce within ±0.02 (L\*, C\*, h, HSL h), and so do
  all eight §5.2 contrast ratios.
- The auditor's `numbers_ref.py` agrees with all 20 anchors of the §4.4 table.
- The three new rules that need no pack (`title-too-long`, `closing-cliche`,
  `claude-look-palette`), implemented roughly, fire on **none** of the 42 existing
  fixture decks in either mode. AC-2's "byte-identical snapshots" is therefore
  achievable, not just hoped for.
- `numbers_ref.py` is not in ruff style and must stay unchanged, so `ruff.toml` now
  excludes `specs/*/evidence` (commit `28fcd93`); CI's `ruff check .` stays green.

---

## 1. Module layout

The spec's §1 layout, with these refinements:

| Spec | Plan | Why |
|---|---|---|
| `src/keyline/numbers.py` | `src/keyline/numtokens.py` | `src/keyline/ooxml/numbers.py` already exists (the A-17 attribute parser). Two `numbers.py` with different jobs invite the wrong import [Q-19] |
| — | `src/keyline/zipnorm.py` | §6.5's zip normalisation is needed in **A1** by the template builders, then by the pen (A2) and `build_skill.py` (B). One stdlib-only module; lint never imports it |
| — | `src/keyline/context.py` | the `LintContext` passed to rules (`pack`, `brief`, `evidence`), so `lint.py` and the rules share one type |
| `packs/swiss/src/` | `packs/swiss/src/build_templates.py` writing raw OOXML with lxml | no python-pptx default template (4:3 layouts, a third-party author in its `docProps`, a non-palette theme); byte-stable without the pen extra [Q-17] |
| `pen/` | `pen/__init__.py` (public: `Deck`, `PenError`, `DoesNotFit`, `EvidenceError`), `pen/_api.py`, `pen/_regions.py`, `pen/_writer_pptx.py` | D-015: every python-pptx call lives in `_writer_pptx.py` behind an internal interface |
| `fit/` | `fit/__init__.py` (estimator), `fit/tables/<twin>-{regular,bold}.json` for every `portable_fonts` family, `tools/gen_fit_tables.py` | the tables are data; the generator is dev-only (fontTools); B-8.11 |
| — | `packs/voices.py`; `packs/<pack>/voices/<name>.toml` | B-8: loading and validating a voice (pack file, `--voice FILE` or a brief's inline table) and the three voice checks, pure data, no deck |

Everything else is as in spec §1: `roles.py`, `brief.py`, `briefcheck.py`,
`colorspace.py`, `packs/__init__.py`, `render.py`, `doctor.py`, `rules/`,
`skill/keyline/`, `tools/build_skill.py`, `tools/gen_docs.py`, `examples/bonsaihub/`,
`fixtures/{briefs,pen,packs}/`.

**Import boundaries** (enforced by AC-15 and one extra test in A1):
`lint`/`rules`/`ooxml`/`brief`/`briefcheck`/`numtokens`/`colorspace`/`packs` never
import `pptx`, `pypdfium2`, `keyline.pen` or `keyline.render`. `render.py` imports
`pypdfium2` lazily, inside the rasteriser function.

**pyproject:** runtime deps stay `lxml`, `Pillow`. Extras `pen = ["python-pptx>=1.0.2"]`,
`render = ["pypdfium2"]`. The `dev` extra gains `pypdfium2` and `fontTools`. Package
data: `packs/*/pack.toml`, `packs/*/README.md`, `packs/*/voices/*.toml`, `packs/*/*.pptx`
(the committed neutral templates, B-8.9), `fit/tables/*.json`.

---

## 2. Phase A1: lint and data

### 2.1 Groundwork: registry, context, config

- **Registry** gains `requires: none | pack | brief | officecli` (a validated field;
  the 13 M1 entries get `none`). `keyline rules --json` adds the key; the human listing
  adds a column.
- **Rule signature.** Rules become `check(deck, cfg, ctx)`. The registry inspects the
  arity at registration and adapts two-argument checks, so the M1 test that injects a
  two-argument `_boom` rule (AC-14 of spec 001) keeps working **unchanged**. This keeps
  AC-2's list of allowed test changes exact.
- **Runner.** `lint_deck(deck, diags, cfg, ctx)` skips a rule whose `requires` is not
  met (`pack` without a pack, `brief` without a brief); `officecli` rules never run in
  lint, only in `check`'s validate step.
- **`accepted`.** When a pack is given, findings whose rule id is in the pack's
  `accepted` list are downgraded to `advisory` (any registry id) [Q-24].
- **Config.** `config.py` today rejects non-numbers and unknown keys. It gains a typed
  schema: numbers stay exact `Fraction`s; the new list keys (`source_prefixes`,
  `note_prefixes`, `closing_cliches`, `mood_words`) are lists of strings, NFC-normalised
  and casefolded on load. The §3.2 per-mode keys go in `[presented]`/`[read]`, the
  common keys in `[common]`. Unknown keys and wrong types still fail loudly.

### 2.2 Roles (§2)

- `roles.py` parses the layout name with the spec's regex into `(role, variant)`;
  `Slide.role`/`Slide.variant` are set by the adapter (it already reads the layout
  name).
- `is_content_slide` becomes role-aware: a slide **with** a role is judged by its role
  only; a slide without one keeps the M1 index rule. So in a mixed deck, a tagged
  slide 1 is not automatically the cover [Q-8].
- `dead-band`: with a role, runs only on `evidence`. `notes-missing`: with a role,
  exempts `cover` and `section`.

### 2.3 Source and note lines (§3.1)

`rules/_common.py` gains `line_kind(paragraph, cfg) -> "source" | "note" | None`
(NFC, left-strip, casefold, prefix, optional spaces, `:` or `：`). `body_paragraphs`
keeps one definition for both rules (A-2) and now excludes source and note paragraphs,
so they are body in neither `body-too-small` nor `title-not-dominant` (B-2, overruling
Q-7). `body-too-small` checks them against `source_min_pt` instead, with "source
line"/"note line" in the message. They still count as text for contrast, fonts and the
pack rules.

### 2.4 Colour spaces and the three pack-free rules (§3.3, §3.4)

- `colorspace.py`: `lab(hex) -> (L, C, h)` and `hsl(hex) -> (h, s, l)` exactly as §3.3,
  pure floats; comparisons against thresholds use the float values (these rules never
  sit on an integer boundary the way geometry does).
- `claude-look-palette` (deck): cream ratio = cream slides / **all** slides; a slide
  whose background is unknown counts as not cream [Q-25]. The terracotta scan covers
  inked run colours, visible solid fills and resolved slide backgrounds (hidden shapes
  excluded, A-12). Warning when both hold, advisory when only cream holds.
- `title-too-long`: title (A-1) words (A-7) > `title_words_max`; `quote` exempt.
- `closing-cliche`: last slide's title text, normalised as §3.4 says; no title → no
  finding.

### 2.5 Pack format (§5.1) and the Swiss pack (§5.2)

**B-8: system and voices.** `pack.toml` is the **system**: structure only, colours
named by role. A **voice** (`voices/<name>.toml`, or a brief's inline `[voice]`) gives
the six roles their values and names two fonts. The loader validates both and returns
a `Pack` (system) and a `Voice`; everything that used `pack.palette` or `pack.fonts`
takes the pair. The shape below is the system as first planned; B-8 changes it as
follows, and T-08's rework implements it:

- `[palette]`, `fonts` and `templates` leave `pack.toml` (Q-26). `palette_roles =
  ["paper", "ink", "muted", "hairline", "accent", "accent_on_ink"]` is added, and
  every role name in the system (surfaces, style colours, theme, `accents`,
  `keyline_rule`) must be one of them.
- Every style gains `font = "display" | "text"` (Q-27).
- `thresholds.toml` `[common]` gains `portable_fonts` (B-8.3) as a list of
  `{ family, metric_twin }` tables (Q-38).
- Voice file:

```toml
schema = 1
name = "neutral"                   # equals the file stem (Q-30)
[fonts]
display = "Arial"                  # a portable_fonts family
text = "Arial"
[palette]                          # exactly the system's palette_roles
paper = "F2F2F0"
ink = "111111"
muted = "5C5C5A"
hairline = "B8B8B4"
accent = "CC3322"
accent_on_ink = "E8422E"
[why]                              # optional in a pack voice; required per role inline
paper = "…"
accepted = []                      # optional { rule, reason } (Q-31)
```

- Stock voices (B-8.10): `neutral` (the values above), `night`, `field`. Their check
  numbers were recomputed with `colorspace.py` and `text_contrast.contrast` on
  2026-09-29 and match B-8's table to the printed precision.

**`pack.toml` shape as first planned** (every value is data; validated on load, errors
name the key):

```toml
schema = 1
name = "swiss"
version = "1.0.0"
modes = ["presented", "read"]
templates = { presented = "swiss-presented.pptx", read = "swiss-read.pptx" }
fonts = ["Arial"]
containers = "rules"
alignment = "left"
accent_budget = 1
accents = ["accent", "accent_on_ink"]
accepted = []

[palette]
paper = "F2F2F0"
ink = "111111"
muted = "5C5C5A"
hairline = "B8B8B4"
accent = "CC3322"
accent_on_ink = "E8422E"

[surfaces.paper]
background = "paper"
text = ["ink", "muted", "accent"]
[surfaces.ink]
background = "ink"
text = ["paper", "accent_on_ink"]

[grid]                       # §6.3; EMU so every region edge is an integer
columns = 12
gutter_emu = 180000          # 0.50 cm
margin_x_emu = 540000        # 1.50 cm
margin_y_emu = 549000        # 1.525 cm
row_emu = 90000              # 0.25 cm; 64 rows fill the content height exactly

[styles.presented.headline]  # one table per mode and style (§5.2 type scale)
size_pt = 48
weight = "bold"
color = { paper = "ink", ink = "paper" }   # colour per surface
caps = false
tracking = 0.0               # fraction of size (label: 0.08)
line_spacing = 1.0
space_before_pt = 0
space_after_pt = 0
# … cover_title, statement, quote, lede, body, numeral, label, source; same keys
# for [styles.read.*]; body/bullets also carry indent_emu and marker

[roles.evidence]
surface = "paper"
title = "headline"
layouts = ["keyline:evidence", "keyline:evidence:figure"]
[roles.evidence.components.presented]
text = ["body"]
bullets = ["body"]
figure = ["numeral", "label"]
table = ["body", "label"]
chart_bar = []
image = []
source = ["source"]
note = ["source"]
# [roles.evidence.components.read] adds "lede" to text; likewise every role

[regions."keyline:evidence"]   # grid units: columns 1–12, rows 0–64
title = { col = 1, span = 12, row = 0, rows = 17 }
main = { col = 1, span = 12, row = 20, rows = 36 }
footer = { col = 1, span = 12, row = 58, rows = 6 }   # source + note, fixed
keyline_rule = { row = 18, thickness_emu = 43200 }     # 0.12 cm, ink, drawn by the pen
```

**Grid arithmetic** (why those numbers): content width 12192000 − 2·540000 =
11112000 EMU; minus 11 gutters = 9132000 = 12 × **761000** EMU columns (2.114 cm).
Content height 6858000 − 2·549000 = 5760000 = 64 × 90000. Eight columns =
8·761000 + 7·180000 = 7348000 EMU = **20.41 cm**, enough for "212 years" at 120 pt
bold (≈ 19.3 cm, and 19.3 / 0.99 = 19.5 cm with §6.4's margin).

**Worked example, presented `keyline:evidence`:** title rows 0–17 (4.25 cm: two
headline lines need 2 × 48 × 1.2 pt = 4.06 cm); keyline rule at row 18; main rows
20–56 (9.0 cm); footer rows 58–64 (1.5 cm: two 12 pt lines need 1.02 cm). The
largest empty band possible on an evidence slide (footer unused) is 3.53 cm = 18.5 %
of the height, under `dead_band_ratio`. Every evidence layout in both modes keeps a
figure-capable region ≥ 8 columns, including the read two-region variant (8 + 4
columns) [Q-10].

**Layouts per mode** (names follow §2; the plan's first cut, finalised in T-09):
`keyline:cover`, `keyline:section`, `keyline:statement`, `keyline:evidence`,
`keyline:evidence:figure` (figure region 8 columns + text region 4 columns in read; a
wide figure region + label in presented), `keyline:quote`, `keyline:close`; the read
template adds `keyline:evidence:two-col`.

**Theme colours** (all palette values, §5.3): dk1 ink, lt1 paper, dk2 muted,
lt2 hairline, accent1 accent, accent2 accent_on_ink, accent3 muted, accent4 hairline,
accent5 ink, accent6 muted, **hlink ink**, folHlink muted. The mapping is by role and
lives in the system; each voice supplies the values (B-8.9), also for dark-paper voices
(Q-33). Major font = the voice's display font, minor = its text font.
`hlink` is ink, not accent (decided for Q-20 on the auditor's recommendation): a
hyperlink in accent would be an accent element and spend the slide's whole
`accent_budget` of 1.

**Type scale:** as §5.2, unchanged. The §5.4 invariants were checked by hand against
it (hierarchy: the tightest pair is presented evidence 48/24 = 2.00; read evidence
28/16 = 1.75 ≥ 1.6), and T-08 turns them into tests. Under B-8.7, invariants 1, 2, 3
and 7 are tested on the system, 4 (contrast) and 6 (fonts) per voice, and 5 (neutral
paper, no terracotta) on `neutral` only.

### 2.6 Templates (§5.3)

- **B-8.9:** built per (system, voice, mode) by `keyline.packs.templates.build(pack,
  voice, mode)`, in memory and byte-stable. Theme colours come from the voice through
  the role mapping; theme major font = display, minor = text; each placeholder's
  `lstStyle` names `+mj-lt` or `+mn-lt` by its style's `font`. Only the `neutral`
  templates are committed (`swiss-neutral-{presented,read}.pptx`, Q-26), and AC-9
  rebuilds them byte-identically. The pen (A2) builds its voice's template in memory.
- Built by `packs/swiss/src/build_templates.py` from raw OOXML parts (presentation,
  one master, the layouts, theme, `presProps`/`viewProps`/`tableStyles`, `docProps`
  with empty author), then `zipnorm.write()`; `created`/`modified` are a fixed date so
  the pen can copy them (§6.5).
- **Placeholders only** in master and layouts. Every region that holds text is a
  placeholder: the title region is `type="title"`, the others are `type="body"` with a
  fixed `idx` per region name; each placeholder's `lstStyle` carries its style's size,
  weight, colour, caps, tracking and spacing for the template's mode, and its `xfrm` is
  the region box. `txStyles` and `defaultTextStyle` carry the mode's body/title sizes,
  so nothing in a pen deck resolves through the adapter's `adapter-unresolved` path.
- Master `p:bg` solid paper; the `section` layout `p:bg` solid ink and its placeholder
  `lstStyle`s set paper (and accent_on_ink for the label).
- A test (AC-9) re-opens both templates with the M1 adapter (not python-pptx) and checks
  every §5.3 constraint, plus: the templates are byte-identical when rebuilt.

### 2.7 Pack rules (§3.4)

`off-palette-color`, `off-scale-size`, `off-pack-font`, `accent-overuse`, all
`requires = "pack"`, measured exactly as the §3.4 table says: hex comparison
case-insensitive; sizes compared in hundredths of a point against the mode's scale;
families compared after A-8 normalisation; accent elements counted once per shape.
Each gets `--pos`/`--neg` fixtures built from the Swiss template (AC-3).

B-8.8: the rules read the resolved **voice**: its palette values, its two fonts, and
the values of the system's `accents` roles. `lint`/`check` gain `--voice NAME|FILE`
(Q-35); `--brief` supplies the voice; a disagreeing `--voice` is exit 1; `--pack` with
no voice is exit 1, "pack rules need a voice (--voice or --brief)". `expect.toml`
cases gain `voice`, required with `pack` (Q-36). `accepted` from the pack and the
voice are unioned (Q-31).

### 2.8 Evidence, briefs and `keyline brief` (§4.1–§4.3)

- `brief.py`: loads the brief and its evidence files with `tomllib`, resolves paths
  relative to the brief file (evidence **and** a pack given as a directory), checks the
  schema, and returns typed objects. Unknown keys are ignored (§4.1). Every schema
  error is a `BriefError` with a one-line reason, which the CLI turns into exit 1.
- Beyond §4.3's list, an unknown pack or a mode the pack does not offer is also a
  schema error [Q-14].
- The five §4.3 findings are registry entries with `requires = "brief"`. The spec
  gives only their severity; the plan proposes category, scope, basis and rationale
  [Q-2].
- Output: the spine to stderr (`NN role  headline`), `{"spine", "findings"}` JSON with
  `--json`, exit 0/1/2 as §4.3.
- **Voice (B-8.4, B-8.5).** Exactly one of `voice = "<name>"` (a voice of the brief's
  pack) or an inline `[voice]` table; neither or both is exit 1. The voice schema
  errors (missing or extra role, malformed hex, a font outside `portable_fonts`, an
  unknown voice name) are exit 1 with one line. `voice-contrast` (error),
  `voice-claude-look` (warning; advisory on cream alone or when accepted) and
  `voice-why` (warning, inline voices only) are registry entries with `requires =
  "brief"`, category `quality`, scope `deck`, `slide` 0; they are `keyline brief`
  findings (Q-28 … Q-30, Q-32, Q-34). Outside `keyline brief`, see Q-29.

### 2.9 Numeric tokens and table text (§4.4)

- `numtokens.tokens(text) -> list[(token, significant)]`, written from §4.4, then held to
  the auditor's oracle: a test runs both on the §4.4 anchors, every string in
  `product.toml`, and a seeded corpus of ~5,000 generated strings (digits, separators,
  signs, currencies, suffixes, spaces, letters), and asserts identical output. The
  oracle is imported from `specs/002-skill-pack/evidence/` by path, never copied.
- `Shape.table_text` (row-major plain cell text) is added by the adapter and read only
  by `numtokens`; `paragraphs` stay table-free so M1 results cannot move. The M1
  "table text is not read" advisory stays.

### 2.10 Deck versus brief (§4.5) and CLI resolution (§3.5)

- `briefcheck.py` implements the six §4.5 findings, pairing slides by index over the
  common prefix. Registry entries with `requires = "brief"`.
- CLI: `lint`/`check` gain `--pack` and `--brief`; `--mode` defaults to `None`.
  Conflicts are exit 1 (`mode conflict: --mode read, brief says presented`); an explicit
  `--pack` conflicts when it resolves to a different pack **directory** than the
  brief's [Q-13]. No flag and no brief: mode `presented`, no pack. New commands:
  `brief`, `doctor`, `packs`. B-8 adds `--voice NAME|FILE`, resolved like `--pack`
  and compared with the brief's voice by content [Q-35]; `keyline packs` lists each
  pack's voices [Q-39].
- **AC-8 in A1** uses a deck built by a fixture script that writes what the pen will
  write (Swiss template layouts, region boxes, source and note lines), because the pen
  does not exist until A2; A2 re-runs AC-8 on a pen-built deck [Q-4].

### 2.11 Render engines, validate, doctor (§7)

- `render.py` gains `engine = auto | libreoffice | officecli`. LibreOffice:
  `soffice --headless --norestore -env:UserInstallation=file://<tmp profile>
  --convert-to pdf --outdir <tmp> DECK`, 120 s timeout, then `pypdfium2` (lazy import)
  or `pdftoppm -png`, 1280 px wide; `soffice` looked up on PATH, then the two standard
  install paths. Each engine prints its known limits (§7).
- **Message compatibility:** the no-engine reason keeps the substring
  `officecli is not installed`, the npm hint and L-002, and adds the LibreOffice hint.
  The M1 tests that assert those strings then pass unchanged; the only M1 test edits
  are the ones AC-2 lists (`--engine officecli` on the `officecli`-marked tests) [Q-11].
- **Validate step:** `check` runs `officecli validate DECK --json` after lint when
  OfficeCLI is present; each error (three `warnings` entries: message, `Path:`,
  `Part:`) becomes one `ooxml-invalid` finding; unparsable output gives one finding
  with its first line; `--no-validate` skips; without OfficeCLI, `validate: skipped
  (officecli is not installed)`. `ooxml-invalid` is a registry entry with
  `requires = "officecli"`.
- **doctor:** one line per §7 check with its token and, for anything missing, the
  install command; exit 0 iff Python ≥ 3.11 with lxml and Pillow; `--json` as an
  object. The font check uses `fc-match Arial` where it exists; elsewhere it looks for
  Arial in the standard font folders [Q-22]. **B-8.12:** the check covers every
  `portable_fonts` family, one line each: `FONT_OK` when `fc-match` returns the family
  or its metric twin, else `FONT_SUBSTITUTED` [Q-40, Q-41].

### 2.12 No-regression method (AC-2)

- **T-01 records a baseline before any lint code changes:** the lint JSON of every M1
  rule fixture, foreign deck and stress deck, in both modes, under
  `fixtures/expected/m1-baseline/`. M1 has golden snapshots but no rule-fixture
  snapshots, so this is how "rule-fixture snapshots are byte-identical" becomes
  checkable [Q-5]. A test asserts byte-identity for the golden, rule and foreign decks;
  for the stress decks it asserts identity or a listed, explained change (AC-2's last
  clause).
- M1 test edits are limited to AC-2's list, and each one is listed in the report.

---

## 3. Phase A2: pen, fit, determinism

Tasks T-20 … T-32 in [`tasks.md`](tasks.md). From audit 02's "Carry into A2": B-7's
measurement on LibreOffice 26.8.0.3 comes first, before any fit constant is used; the
numeral and the label of `figure()` each get their own box inside the figure region;
the pen refuses a voice with an error-level `voice-*` finding (Q-29); AC-8 runs again
on a pen-built deck (B-3). B-8.11 and B-8.13 add fit tables for all six portable families
and specimens in three voices.

- **Public API (`keyline.pen`):** `Deck.from_brief(path)`, `Deck(pack, mode, voice,
  evidence=None)` (B-8.9: the deck builds its voice's template in memory), `deck.next()`, `deck.add(role, headline, notes=None)`, the builder's
  verbs (§6.1), `deck.save(path, author="")`. Parameters are only style names, region
  names, evidence ids and content; `_check_token()` rejects raw-looking strings
  (`#hex`, `NNpt`, `NNcm`, `NNin`, `NNpx`, `NNemu`). AC-10's signature test inspects
  `inspect.signature` of every public callable and fails on parameter names or
  annotations that denote colour, font, size, length, coordinate or alignment.
- **Writer isolation (D-015):** the builder produces a writer-neutral slide plan
  (region box, style tokens resolved to values, text, kind); `_writer_pptx.py` turns it
  into python-pptx calls. No python-pptx type crosses the public API; a test checks the
  return types.
- **Slides:** added from the template layout named by the role (variant from the
  region set used, or explicit); the headline goes into the title placeholder; unused
  placeholders are removed from the slide; the keyline rule is drawn on evidence
  slides.
- **Fit (§6.4):** `tools/gen_fit_tables.py` (fontTools) writes per-codepoint advance
  widths (units per em) for the metric twin of every `portable_fonts` family, Regular
  and Bold (B-8.11), recording each source file's name, version and licence in
  `NOTICE`, plus `line_pitch_em = 1.2`; AC-13(a) runs per twin present and skips the
  rest by name; the estimator wraps greedily at 0.99 × width, adds tracking and caps, and
  raises `DoesNotFit` with "needs N lines, region holds M". AC-13(a) compares with
  Pillow (BASIC layout); AC-13(b) renders a fit-stress deck with LibreOffice and checks
  ink stays inside each region box.
- **Determinism (§6.5):** `zipnorm` on save; core properties from the template; the
  chart workbook's `core.xml` dates set to the template's `created` and its inner zip
  normalised; chart axis ids remapped to positive deterministic UInt32s with each
  `axId`/`crossAx` pair kept consistent (§6.6).
- **Specimens:** `fixtures/packs/swiss-specimen-{presented,read}.brief.toml` and
  `swiss-specimen.evidence.toml`, one slide per role, every verb used, real sentences
  about the pack. B-8.13: presented in `neutral` and in `night`, read in `field`;
  AC-11 and AC-12 apply to all three, and G-1 reviews three contact sheets. AC-11 (two builds byte-identical), AC-12 (`check --brief` exit 0, no
  `adapter-unresolved`, no `ooxml-invalid` with OfficeCLI), AC-15 (core purity).
- **Gate G-1:** Tyler reviews the specimen contact sheets (LibreOffice renders).

## 4. Phase B: skill, packaging, demo (plan only)

- **Skill folder** `skill/keyline/`: `SKILL.md` (frontmatter per §8.2; body ≤ 200
  lines, no `${`, no `` !` ``, no absolute paths), `references/{brief,craft-floor,
  anti-tells,pen,check}.md`, `scripts/kl.py` (`lib/` on `sys.path` when packaged,
  otherwise the installed package; `kl.py run SCRIPT.py` via `runpy`).
- **Generated docs:** `tools/gen_docs.py` writes the numeric tables between
  `<!-- gen:begin NAME -->`/`<!-- gen:end -->` from `thresholds.toml` and `pack.toml`;
  `--check` fails on drift (CI). Tests: every `<!-- rule:ID -->` resolves; every
  Appendix A id is present with a valid enforcement; `pen.md` covers every public verb;
  `check.md` has a recipe per warning/error id.
- **Packaging:** `tools/build_skill.py` → `dist/keyline.zip` (one `keyline/` folder with
  `SKILL.md`, `references/`, `scripts/`, `lib/keyline/` without tests or caches,
  `LICENSE`, `NOTICE`), built through `zipnorm`, < 3 MB, two builds byte-identical.
  AC-20 runs it in a fresh venv with only lxml, Pillow and python-pptx.
- **Demo (§10):** the two BonsaiHub decks are produced by a **fresh** Claude Code
  session with the skill installed from `dist/keyline.zip`, using prompts P-1 and P-2
  verbatim; Tyler approves each spine (G-2a). The implementing session cannot be that
  fresh session [Q-16]. AC-22 surface runs are Tyler's (manual).
- **B-8.14, B-8.15:** the skill's loop gains a voice step after the direction (derive
  the voice from `own_world`, one `why` line per role; stock voices only as a
  fallback); `craft-floor.md` anchors `rule:voice-*`; `anti-tells.md` gains
  `one-look-for-everything`. Each BonsaiHub brief carries an inline voice derived from
  `[product.world]`, and `keyline brief` exits 0 on both.
- **Gate G-2:** Tyler's soul verdict on both contact sheets, voice included.

---

## 5. Fixtures

| family | how | used by |
|---|---|---|
| `fixtures/rules/` (new `--pos`/`--neg` for the 7 §3.4 rules, AC-4's four anchor decks, AC-5's role deck, AC-6's source lines) | extended `build_rules.py`; pack-rule decks start from the Swiss template | AC-3 … AC-6 |
| `fixtures/briefs/` (`valid.brief.toml`, one file per §4.3 schema error, `--pos`/`--neg` per §4.3 finding, a small evidence file) | hand-written TOML | AC-7 |
| `fixtures/briefs/drift/` (AC-8 base deck + six drifted copies) | `fixtures/briefs/src/build_drift.py`, from the Swiss template; the drifts are applied by lxml edits to named parts so that nothing else moves | AC-8 |
| `fixtures/validate/editorial-bogus.pptx` | `editorial.pptx` with `<p:bogus/>` injected in slide 1's `p:cSld` by a committed script (the golden itself is not edited) | AC-14b |
| `fixtures/expected/m1-baseline/` | captured in T-01 | AC-2 |
| `fixtures/briefs/voice/` (one brief per voice schema error, both-or-neither, `--pos`/`--neg` per `voice-*` id, an inline voice) and `fixtures/voices/` (voice files for `--voice FILE`) | hand-written TOML | AC-7, B-8.5 |

Every builder sets author and last-modified-by to `Tyler`; AC-12 of spec 001 keeps
scanning every committed deck.

## 6. CI

- `apt-get install fonts-liberation fonts-crosextra-carlito fonts-crosextra-caladea`
  (AC-23, B-8.11; Gelasio is not packaged there, so Georgia skips by name); `pip install -e .[dev]` with `dev` now
  including `pypdfium2` and `fontTools`.
- LibreOffice and OfficeCLI are absent in CI, so render and validate tests skip there,
  as in spec 001; the report records where each ran.
- `ruff` runs as today (`check .` and `format --check .` are read-only); locally, fixes
  and formatting are run only on `src tests fixtures tools`.

## 7. Risks

| id | risk | mitigation |
|---|---|---|
| R-1 | **LibreOffice version.** The spec's fit measurements (1.2 em pitch, the 0.99 wrap margin) come from LibreOffice 24.2; this machine has 26.8.0.3, which already differs on autofit (d18). | Record the version with every render; measure pitch and wrap on 26.8 in A2 before trusting AC-13(b); report differences, never tune to them [Q-18] |
| R-2 | **Hand-built templates.** A raw-OOXML package may open in python-pptx and pass `officecli validate` yet be refused or repaired by PowerPoint. | Model the parts on what PowerPoint itself writes; validate with OfficeCLI; Tyler opens both templates in PowerPoint at G-1 [Q-17] |
| R-3 | **Tokenizer false positives.** Day-of-month dates ("27 September 2026"), versions ("v2.0.1") and "3 × 4" are significant tokens, so `unsourced-number` fires on them. | Documented limit in `check.md`; the pen and skill write month-year dates [Q-6] |
| R-4 | **Regression through shared code.** New config types, the rule signature and the role-aware `is_content_slide` touch every M1 rule. | Baseline snapshots first (T-01); the arity adapter; M1 behaviour for untagged slides |
| R-5 | **Scope.** Spec 002 is roughly three times spec 001. | The A1/A2/B gates; A1 alone is 19 tasks |
| R-6 | **Fit versus PowerPoint.** Liberation Sans is metric-compatible with Arial, but PowerPoint's line breaking is unverified (D-017). | The 1 % margin; G-1 in PowerPoint |
| R-7 | **Sandbox assumptions.** python-pptx is documented as pre-installed in the API container; LibreOffice on claude.ai is inferred. | `doctor` tokens; AC-20 stands in for the sandbox; AC-22 records the real run |
| R-8 | **Speed.** Spec 001's AC-9/AC-20 budgets still hold with seven more rules and the brief checks. | The rules are linear; AC-9/AC-20 stay in CI |
| R-10 | **Voices widen the surface.** Every voice is a new colour and font combination the templates, the pack rules and (A2) the fit tables must handle; a dark-paper voice inverts the theme's dk/lt meaning (Q-33). | Invariants 4 and 6 per voice; the three stock voices in AC-9; specimens in three voices at G-1 |
| R-11 | **Missing twins.** Carlito, Caladea and Gelasio are not installed on this machine (Q-41), so renders here substitute Noto for Calibri, Cambria and Georgia. | Doctor reports it per family; A2's AC-13(a) skips by name; the report lists what was present |
| R-9 | **Licensing.** Width tables derive from Liberation Sans (OFL), and under B-8 from every twin (Liberation, Carlito, Caladea, Gelasio: OFL); skill text must not copy Anthropic's skills. | Each source font's file, version and licence in `NOTICE`; anti-tells cite `docs/research.md` only; AC-23 |

## 8. Order of work

A1 tasks T-01 … T-19 ([`tasks.md`](tasks.md)) → report A1 → **stop for the external
audit of A1** [Q-15] → A2 tasks (written after the audit) → report A2 → G-1 and the A2
audit → B tasks → report B → G-2 → B audit → PR.

---

## 9. Open questions

Each has a proposal; implementation follows the proposal unless Tyler rules otherwise.

1. **Q-1 · Registry count.** AC-1 says 32 entries (13 + 1 + 7 + 11 = 32); AC-2 says
   `test_rules_listing` accepts "the 31 ids". *Proposal:* 32; AC-2's 31 is a typo.
2. **Q-2 · Fields of the 11 §4 ids.** The spec gives severity (and scope for §4.5) but
   not category, basis, scope for §4.3, or rationale. *Proposal:* category `quality`
   for all; basis `text` for `brief-headline`, `brief-headline-long`, `brief-mood`,
   `unsourced-number`, else `structure`; scope `deck` for `brief-no-statement`,
   `brief-mood`, `brief-slide-count`, `fiction-undisclosed`, else `slide`; rationale
   the research section on tells, or the canon section for `brief-reads` and
   `brief-headline-long`.
3. **Q-3 · Registry scope of brief findings.** §4.3 findings index brief slides, not
   deck slides, under the same `slide` key. *Proposal:* keep the key (as the spec
   says); `keyline brief` output never mixes with deck findings.
4. **Q-4 · AC-8 in A1 needs a pen-built deck.** *Proposal:* A1 uses a fixture-built deck
   that mimics the pen's output; A2 repeats AC-8 with the pen.
5. **Q-5 · "Rule-fixture snapshots."** M1 has none. *Proposal:* T-01 captures them
   (and foreign and stress baselines) before any change; they become the snapshots.
6. **Q-6 · Tokenizer limits.** "27 September 2026" → `27`\*, "v2.0.1" → `2.0.1`\*,
   "3 × 4" → `3×`\*, "$-5" → `-5`\* (the `$` is dropped because a sign before the
   currency is the only order §4.4 allows). *Proposal:* accept as known limits (like
   §4.4.5), document them in `check.md`, and have the skill write month-year dates.
7. **Q-7 · Source/note lines in `title-not-dominant`.** §3.1 removes them from body
   only in `body-too-small`, but A-2 made one body definition for both rules.
   *Proposal:* follow §3.1 literally for now (no effect on Swiss decks, whose titles
   are far larger); ask whether A-2's single definition should win.
   **Ruling (audit 01): overruled.** One body definition; source and note paragraphs are
   body in neither rule (B-2). §2.3 is updated.
8. **Q-8 · Mixed decks.** Does "slide 1 is the cover" still apply to a slide 1 that has
   a non-cover role? *Proposal:* no; a role, when present, decides.
9. **Q-9 · AC-5's "untagged layout at index 2".** *Proposal:* one deck ordered
   `keyline:statement`, untagged, `keyline:evidence`, so the untagged slide is slide 2.
10. **Q-10 · Margins and the 8-column rule.** §6.3 says regions sit "inside
    `edge_margin_cm` + `edge_margin_tolerance_cm`"; §5.3 says ≥ `edge_margin_cm`.
    *Proposal:* 1.50 cm / 1.525 cm outer margins satisfy both; and the ≥ 8-column
    figure region applies to every evidence layout, including read's two-region
    variant (8 + 4).
11. **Q-11 · The `check` no-engine message.** An M1 test asserts
    `render: skipped (officecli is not installed`, which AC-2 does not list among the
    allowed test changes. *Proposal:* keep that substring in the new message so the
    test is untouched.
12. **Q-12 · `requires = "officecli"` in `lint`.** `ooxml-invalid` only arises in
    `check`. *Proposal:* lint never runs it and never lists it as skipped.
13. **Q-13 · `--pack` vs the brief's pack.** A name and a directory can name the same
    pack. *Proposal:* compare resolved directories.
14. **Q-14 · `keyline brief` and the pack.** An unknown pack, or a mode the pack does
    not offer, is not in §4.3's exit-1 list. *Proposal:* both are schema errors (exit
    1).
15. **Q-15 · A1 → A2.** §11 puts the external audit after report A1. *Proposal:* stop
    after report A1 and wait for the audit and Tyler, as in spec 001.
16. **Q-16 · Who runs the demo.** §10 needs a fresh Claude Code session with the skill
    installed from the zip; installing into `~/.claude/skills/` is Tyler's machine
    configuration. *Proposal:* Tyler starts that session; the implementing session
    prepares the exact commands and prompts.
17. **Q-17 · Templates from raw OOXML** rather than python-pptx's default template (see
    §1 and R-2). *Proposal:* raw OOXML; Tyler opens both templates in PowerPoint at G-1.
18. **Q-18 · LibreOffice 26.8 here, 24.2 in the spec.** *Proposal:* measure and render
    with what is installed, record the version, and report any AC that holds on one
    version only; installing 24.2 is Tyler's call.
19. **Q-19 · `numbers.py` → `numtokens.py`** (see §1). *Proposal:* rename.
20. **Q-20 · Theme colour mapping** (§2.5) and **the layout list per mode** are plan
    choices; flagged here so Tyler sees them before T-09.
    **Ruling (audit 01): accepted; decided:** `hlink` maps to ink, not accent (§2.5).
    The rest of the mapping and the layout list stand.
21. **Q-21 · Pen placeholders.** *Proposal:* every text region is a layout placeholder
    (so hand-typed text lands on scale, §5.3), and the pen deletes the placeholders it
    does not fill; figures, tables, charts and images are ordinary shapes at their
    region box. (A2 detail, raised now because it shapes the A1 templates.)
22. **Q-22 · The font check off Linux.** `fc-match` is usually absent on macOS and
    Windows. *Proposal:* look for Arial in the standard font folders there; if nothing
    can be checked, print `FONT_SUBSTITUTED` with a note rather than claiming
    `FONT_OK`.
23. **Q-23 · `brief-mood` tokenising.** Hyphenated mood words ("cutting-edge") stay one
    token after whitespace splitting and punctuation stripping, so they match; "state
    of the art" does not. *Proposal:* as specified.
24. **Q-24 · `accepted`.** *Proposal:* any registry id, downgraded to advisory only
    when that pack is in effect.
    **Ruling (audit 02): superseded by B-10.** Only `acceptable_rules`, each with a reason.
25. **Q-25 · Cream ratio denominator.** *Proposal:* all slides; unknown backgrounds are
    not cream.

### B-8 questions (2026-09-29)

**Rulings (audit 02):** accepted: Q-26, Q-27, Q-28, Q-30 (with `fullmatch`, B-12 item 1),
Q-32 (a schema error under B-12 item 4), Q-33 (G-1 checks in PowerPoint that a new text
box on the `night` specimen is readable), Q-35 (for the CLI; a brief's `voice` is a name
only, B-12 item 3), Q-36 … Q-40. Q-29: (a), (b) and (d) accepted; (c) stands, and in A2
the pen refuses (`PenError`) a voice with an error-level `voice-*` finding. **Q-31
overruled** by B-10; **Q-34 overruled** by B-9. Q-41: install the twins before A2 (done;
see `report.md`, A1 fixes).

26. **Q-26 · Template files and the `templates` key.** Templates are now built per
    (system, voice, mode) in memory (B-8.9), so the system cannot name fixed files, and
    T-09 part 2 committed `swiss-presented.pptx`/`swiss-read.pptx` before B-8 arrived.
    *Proposal:* drop `templates` from `pack.toml`; commit the neutral pair as
    `packs/swiss/swiss-neutral-presented.pptx` and `swiss-neutral-read.pptx` (the voice
    in the name, so nobody takes them for the only look); `build_templates.py
    [OUT_DIR]` writes them; AC-9 rebuilds them byte-identically.
27. **Q-27 · Display and text styles.** B-8 gives every style a `font` but does not
    say which. *Proposal:* display: `cover_title`, `statement`, `headline`, `quote`,
    `numeral`; text: `lede`, `body`, `label`, `source`. Placeholder `lstStyle`s use
    `+mj-lt` for display and `+mn-lt` for text, so hand-typed text follows the voice.
28. **Q-28 · The pairs `voice-contrast` checks.** "A (text color, surface) pair that the
    system allows." *Proposal:* every role in `surfaces.<s>.text` against
    `surfaces.<s>.background`. The loader requires each style colour on a surface to be
    in that list (added in T-08r), so these are all the pairs any style allows; for Swiss
    they are exactly the five columns of B-8's check table. `hairline` is not text and
    is not checked.
29. **Q-29 · Voice findings outside `keyline brief`.** B-8.5 runs the voice checks "in
    `keyline brief`, and whenever a pack voice is loaded", but the three entries are
    `requires = "brief"`, and §4.3 says brief findings are not repeated by `check`.
    *Proposal:* (a) the schema errors apply on every load, in every command (exit 1);
    (b) the three findings are `keyline brief` findings only (JSON and exit code);
    (c) when `lint`, `check` or the pen load a voice that has a `voice-*` finding at
    warning or error, stderr gets one line per finding (`voice night: …`) and the
    deck's JSON is unchanged; (d) AC-9 asserts that no stock voice has any `voice-*`
    finding.
30. **Q-30 · Voice file details.** *Proposal:* a pack voice's `name` matches
    `^[a-z0-9-]+$` and equals its file stem, else a schema error; hex values match
    `^[0-9A-Fa-f]{6}$` (no `#`) and are stored upper case; fonts match a
    `portable_fonts` family after casefolding and whitespace collapse, and are stored in
    its spelling (not A-8's weight stripping: "Calibri Light" has no twin);
    `schema = 1` is required in a voice file and optional in an inline `[voice]` (the
    brief's `schema` governs); `[why]` keys that are not roles are ignored (§4.1's
    unknown-keys rule); an empty `why` line counts as missing; `voice-why` gives one
    finding per missing role.
31. **Q-31 · `accepted` in a voice.** *Proposal:* as the pack's (Q-24): any registry id,
    downgraded to advisory while that voice is in effect; the pack's and the voice's
    lists are unioned.
32. **Q-32 · An accent role sharing a value.** `accents` stays in the system as role
    names. If a voice gave an accent role the same hex as a non-accent role (accent =
    ink), `accent-overuse` would count every ink shape as an accent. *Proposal:* a
    schema error, "accent has the same value as ink". It is not in B-8.5's list, so it
    needs a ruling; no stock voice is affected.
33. **Q-33 · Dark-paper voices and the theme.** In `night`, `paper` is dark and `ink`
    light, so the plan's mapping gives dk1 = `ECECE8` (light) and lt1 = `16181B`
    (dark). *Proposal:* keep the mapping literal, as B-8.9 says. The master's `clrMap`
    (bg1 = lt1, tx1 = dk1) still resolves bg1 to paper and tx1 to ink, so scheme-coloured
    text stays readable; only PowerPoint's theme picker shows "Dark 1" as a light swatch.
    Checked in PowerPoint at G-1 with the `night` specimen.
34. **Q-34 · `night`'s ink is in the cream band.** `ECECE8` has L\* 93.3, C\* 2.06,
    h 110.0, inside §3.2's cream band. B-8.5 tests only `paper`, so `voice-claude-look`
    is silent; but the deck rule `claude-look-palette` looks at resolved backgrounds,
    and a `night` section slide (ink surface) is cream. The rule needs at least half the
    slides cream, and stays advisory without a terracotta. *Proposal:* accept, and pin
    it with a test; revisit if the `night` specimen shows it.
35. **Q-35 · `--voice` resolution.** *Proposal:* a value containing a path separator or
    ending in `.toml` is a voice file (pack-voice schema); otherwise a voice name of the
    resolved pack. `--voice` with no pack from `--pack` or the brief is exit 1,
    "--voice needs a pack (--pack or --brief)". It conflicts with the brief when the
    resolved fonts or palette differ (content, as Q-13 compares directories):
    `voice conflict: --voice night, brief says neutral`.
36. **Q-36 · `expect.toml` with a pack.** *Proposal:* `voice` is required whenever
    `pack` is given (B-8.8 makes a pack without a voice exit 1); the harness fails
    loudly otherwise.
37. **Q-37 · "One sans family".** §5.2's direction says one sans family; `field` is
    Georgia (B-8.10). *Proposal:* the README says "one family per voice, regular and
    bold" and lists the three voices with their `why` lines; §5.2 stays as written,
    superseded by B-8.
38. **Q-38 · `portable_fonts` in `config.py`.** Config accepts numbers and lists of
    strings. *Proposal:* a third type, a list of `{family, metric_twin}` tables (both
    non-empty strings, families unique after A-8 normalisation), exposed as a tuple of
    pairs.
39. **Q-39 · Voices in `keyline packs`.** *Proposal:* the listing adds the voice names;
    `--json` adds `"voices": [{"name", "display", "text"}]`.
40. **Q-40 · Doctor without `fc-match`** (extends Q-22). *Proposal:* each portable
    family is `FONT_OK` when a known file for it or its twin is in the standard font
    folders (a fixed table: `arial.ttf`, `times.ttf`, `cour.ttf`, `georgia.ttf`,
    `calibri.ttf`, `cambria.ttc` and the twins' files), else `FONT_SUBSTITUTED`, with a
    note that the check was by file name.
41. **Q-41 · Twins on this machine.** Liberation Sans, Serif and Mono are installed;
    Carlito, Caladea and Gelasio are not (`fc-match` gives Noto Serif for Georgia and
    Cambria, Noto Sans for Calibri). A1 builds no fit tables, but doctor reports
    `FONT_SUBSTITUTED` for those three here. *Proposal:* report A1 records it; before
    A2, Tyler decides whether to install them here (system packages and Gelasio's
    upstream release) or let AC-13(a) skip them by name.

### A2 questions (2026-09-29, with the A2 tasks)

**Rulings (audit 03, §5):**
- **Q-42 accepted, with one change:** every stem names its voice:
  `swiss-specimen-presented-neutral`, `swiss-specimen-presented-night`,
  `swiss-specimen-read-field`, so a fourth voice never forces a rename. They share one
  evidence file.
- **Q-43 accepted, with three additions:** (a) both boxes span the region's full width,
  and the label is top-anchored; (b) a region shorter than the numeral's rows plus one
  label line raises `DoesNotFit`, naming both; (c) the two boxes touch but do not
  overlap, so `box-overlap` stays silent (a test asserts it).
- **Q-44 accepted, with two additions:** (a) the probe decks name the portable family
  (Arial, Georgia, …), not the twin, so the measurement goes through fontconfig's
  substitution as a pen deck does; the script prints `fc-match <family>` for each family
  and stops if any does not resolve to its twin; (b) every measured constant is stored
  with the LibreOffice version that produced it (principle IV).
- **Q-45 accepted.**
- **Q-46 accepted, with one test:** the in-memory template for (neutral, mode) is
  byte-identical to the committed file.
- **T-22:** AC-13(a) passes between 0.995 and 1.25; the report also gives the largest
  ratio per twin and flags any plain-Latin string above 1.05 (informational).
- **T-20:** record the actual `soffice --version` at run time; if it is not 26.8.0.3,
  say so. The stop-and-report rule applies unchanged.

**Rulings (audit 04, [audit-04-t20.md](audit-04-t20.md), amendment B-21):** keep the 0.99
wrap margin; `line_pitch_em = 1.2` for all six twins, with 0.01 mm per line in the height
test; the widened measurement (stress set, pack spacings) must pass B-21's two criteria
(it did on 26.8.0.3, `e93fa4a`); the fit tables list each twin's missing Vietnamese
letters, and the pen warns once per deck when text uses them (not a registry entry).

42. **Q-42 · Specimen files for three voices** (B-8.13). *Proposal:*
    `fixtures/packs/swiss-specimen-presented.brief.toml` (voice `neutral`),
    `swiss-specimen-presented-night.brief.toml` (voice `night`) and
    `swiss-specimen-read.brief.toml` (voice `field`), one shared
    `swiss-specimen.evidence.toml`, and decks with the same stems. AC-11 and AC-12 apply
    to all three.
43. **Q-43 · Figure sub-boxes.** §6.3 says a pen shape's box is its full region box; the
    audit asks for separate boxes for the numeral and the label. *Proposal:* the
    numeral's box is the top of the figure region, one numeral line tall (size × line
    pitch, rounded up to whole grid rows); the label's box is the rest of the region
    below it. Together they cover the region, so `dead-band` still sees the layout's
    composition, and neither shape is body text.
44. **Q-44 · Where the B-7 measurements go.** *Proposal:* `tools/measure_lo.py` output is
    committed as evidence, `line_pitch_em` is stored per twin in its width table (as
    §6.4 says for Liberation Sans), and the wrap margin is one constant in the
    estimator. Values differing from §6.4's 24.2 figures wait for a ruling (B-7).
45. **Q-45 · The brief-less `Deck` needs a voice** (B-8). *Proposal:* `Deck(pack=…,
    mode=…, voice=…, evidence=None)` with `voice` required (a name of the pack or a
    voice file, as `--voice`); `Deck.from_brief(path)` takes the brief's voice.
46. **Q-46 · The pen's template.** *Proposal:* the pen builds its voice's template in
    memory (`templates.build(pack, voice, mode)`) and opens it with python-pptx; the
    committed neutral files are for inspection and tests only.

