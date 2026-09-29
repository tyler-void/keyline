# Report A1 · Spec 002 (skill, brief and the Swiss pack)

- **Phase:** A1 (lint and data), tasks T-01 … T-19 of [`tasks.md`](tasks.md), with
  amendments B-1 … B-8. Phase A2 (pen) and B (skill) have not started.
- **Branch:** `002-skill-pack`, head `c335e18` when this report was written (the report's
  own commit follows it). Branched from `main` at `678c69a`.
- **Audit 02** ([audit-02-a1.md](audit-02-a1.md), verdict FIX): the fixes FX-1 … FX-8
  and amendments B-9 … B-15 are in [A1 fixes](#a1-fixes-audit-02) at the end.
- **Status:** every A1 acceptance criterion passes locally, including the LibreOffice and
  OfficeCLI paths. CI (Python 3.11 and 3.13, no LibreOffice, no OfficeCLI) is green on
  every task commit except `ff1717f` (T-12), which failed `ruff format --check`; see
  *Process notes*. **Stop here for the external audit of A1** (plan Q-15).

## Environment

| what | version |
|---|---|
| OS | Linux 7.2.4-zen2-1-zen |
| Python (`.venv`) | 3.11.16 |
| lxml / Pillow / python-pptx / pypdfium2 | 6.1.3 / 12.3.0 / 1.0.2 / 5.13.0 |
| LibreOffice (`soffice --version`) | `LibreOffice 26.8.0.3 680(Build:3)` |
| OfficeCLI | 1.0.152 |
| pdftoppm | 26.08.0 |

## Reproduce

```sh
python -m pip install -e '.[dev]'
pytest -q                      # 611 passed locally; LibreOffice/OfficeCLI tests skip without them
pytest -q -m officecli         # the OfficeCLI subset: 12 passed
python tools/m1_baseline.py    # baseline: no differences
```

The tests that need LibreOffice skip when `soffice` or a rasterizer is missing; the ones
that need OfficeCLI carry the `officecli` marker and skip without it. CI runs neither, so
the render, validate and template-validation results below come from this machine.

---

## Acceptance criteria

### AC-1 · Registry (as amended by B-1 and B-8.6: 35 entries) · PASS

```
$ keyline rules --json | python -c "…count by requires…"
35 {'pack': 4, 'none': 16, 'brief': 14, 'officecli': 1}
$ pytest -q tests/acceptance/m2/test_ac01_registry.py
1 passed
```

- 16 `none` = the 13 M1 entries + `claude-look-palette`, `title-too-long` and
  `closing-cliche`. 4 `pack` = the other §3.4 rules. 14 `brief` = the 11 §4 ids and
  the 3 voice ids (B-8.5). 1 `officecli` = `ooxml-invalid`.
- The test asserts the exact id set, `requires` on every entry, and the M1 entries'
  severity, category and basis. Those values were compared with `main`'s own
  `keyline rules --json` (run from a temporary worktree of `main`): no difference in
  any of the 13 entries.

### AC-2 · No regression · PASS

```
$ python tools/m1_baseline.py
baseline: no differences
$ pytest -q tests/acceptance/test_m1_baseline.py
2 passed
```

- The baseline (T-01, `c46622f`) holds the lint JSON of 74 (deck, mode) pairs, captured
  before any lint code changed: 44 rule fixtures, 4 foreign, 26 stress (13 decks × 2
  modes). It was compared after every task; all are byte-identical at HEAD.
- **Stress re-lint:** the 13 stress decks give no changed finding in either mode, as
  the auditor predicted. There is nothing to list.
- The golden snapshot tests of spec 001 pass unchanged.
- **Every change to a spec 001 test file** (`git diff --name-status 678c69a HEAD -- tests/`):

| file | change | allowed by |
|---|---|---|
| `tests/acceptance/test_cli.py` | `test_rules_listing` accepts the 13 M1 ids plus the 22 spec 002 ids (35), and `since` in {"0.1.0", "0.2.0"} | AC-2 bullet 1, with B-1 and B-8.6's count |
| `tests/rules/test_rule_fixtures.py` | cases may carry `pack` (with `voice`, B-8.8) or `brief`; the harness passes them to lint | AC-2 bullet 2 (plus B-8.8's `voice`) |
| `tests/acceptance/test_ac10_render.py` | the two `officecli`-marked tests pass `--engine officecli` | AC-2 bullet 3 |
| `tests/unit/test_config.py` | four tests added for the §3.2 keys and `portable_fonts`; no existing line changed (`git diff` shows 77 insertions, 0 deletions) | new tests, not a change |

- The no-engine messages keep "officecli is not installed", the npm hint and L-002, and
  gain the LibreOffice hint (AC-2 bullet 4; see AC-14).

### AC-3 · Rule fixtures · PASS

```
$ pytest -q tests/rules/test_rule_fixtures.py
55 passed
```

Every §3.4 rule has a `--pos` and a `--neg` deck in `fixtures/rules/`, built by
`fixtures/rules/src/build_rules.py`, with `expect.toml` cases:

| rule | pos | neg | pack cases |
|---|---|---|---|
| `claude-look-palette` | `--pos` (+ `--cream-only`) | `--neg`, `--cool` | — |
| `title-too-long` | `--pos` | `--neg` (and `--pos` in read mode) | — |
| `closing-cliche` | `--pos` | `--neg` | — |
| `off-palette-color` | `--pos` | `--neg` | `pack = "swiss"`, `voice = "neutral"` |
| `off-scale-size` | `--pos` (20 pt; 24 pt × 90 % autofit) | `--neg` (32 pt × 75 % = 24 pt) | same; plus a read-mode case |
| `off-pack-font` | `--pos` | `--neg` | same |
| `accent-overuse` | `--pos` | `--neg` (two accent runs in one shape count once) | same |

The pack-rule decks start from the Swiss template, built in memory for their voice.
Two more decks, `pack-voice-night` and `pack-voice-field`, are clean in their own voice
and off-palette (and, for `field`, off-font) when read against `neutral`.

### AC-4 · Claude-look anchors · PASS

```
$ keyline lint fixtures/rules/claude-look-palette--<deck>.pptx --json   (filtered)
pos: [('claude-look-palette', 'warning', '2 of 2 slides (100.0%) have a cream background and #C96442 is a terracotta accent')]
neg: []
cream-only: [('claude-look-palette', 'advisory', '2 of 2 slides (100.0%) have a cream background; no terracotta accent')]
cool: []
$ pytest -q tests/acceptance/m2/test_ac04_claude_look.py
4 passed
```

### AC-5 · Roles · PASS

```
$ keyline lint fixtures/rules/roles--ac5.pptx --json   (dead-band and notes-missing)
[(2, 'dead-band'), (3, 'dead-band')]
$ pytest -q tests/acceptance/m2/test_ac05_roles.py
5 passed
```

Slide 1 is on `keyline:statement` (no `dead-band`), slide 2 on an untagged layout at
index 2 (`dead-band`, the M1 behavior), slide 3 on `keyline:evidence` (`dead-band`), and
the `keyline:section` slide without notes gets no `notes-missing`.

### AC-6 · Source lines · PASS

```
$ keyline lint fixtures/rules/source-lines--ac6.pptx --json   (body-too-small)
[('source-10pt', '10 pt source line (min 12 pt in presented mode)'),
 ('source-code', '12 pt text in a 10-word paragraph (min 18 pt in presented mode)')]
$ pytest -q tests/acceptance/m2/test_ac06_source_lines.py
6 passed
```

The 12 pt source line and the 12 pt note line give nothing.

### AC-7 · Brief validation (with B-4 and B-8.4/B-8.5) · PASS

```
$ keyline brief fixtures/briefs/valid.brief.toml
01 cover      Toolshed Commons
02 statement  Repairs bring members back
03 section    What the bench does
04 evidence   Most returned tools need a repair before the next loan
05 evidence   Membership grew after the first bench opened
06 quote      I came to borrow a saw and stayed to learn how to sharpen one for the next person
07 close      Build the second bench this spring
0 findings: 0 error, 0 warning, 0 advisory
exit 0
$ keyline brief fixtures/briefs/two-covers.brief.toml
keyline: two-covers.brief.toml: slides[7].role: more than one cover
exit 1
$ pytest -q tests/acceptance/m2/test_ac07_brief.py tests/acceptance/m2/test_ac07_voice.py
31 passed / 16 passed
```

- `fixtures/briefs/src/build_briefs.py` writes every fixture as `valid.brief.toml` (or an
  evidence file) with exactly one change; `fixtures/briefs/expect.toml` gives each its
  exit code and, for exit 1, the exact line.
- **Schema errors, one fixture each** (exit 1, one line on stderr, nothing on stdout, no
  traceback): bad schema, missing key, mistyped key, unknown role, unknown evidence id,
  evidence file missing, evidence file invalid, value and series both, duplicate
  evidence id, first slide not a cover, two covers, `own_world` with 2 and with 8 items,
  evidence on a section and on a quote slide, a 6-word evidence label; B-4: unknown pack,
  mode the pack lacks; B-8: no voice, both (a TOML error, see Deviations), unknown voice
  name, missing role, extra role, bad hex, a font outside `portable_fonts`.
- **Findings, positive and negative each:** `brief-reads`, `brief-mood`, `brief-notes`,
  `brief-headline-long`, `brief-no-statement` (advisory), `voice-contrast` (error),
  `voice-claude-look` (warning; advisory with cream paper alone and when accepted),
  `voice-why`. The valid brief is the negative for all eight; read-mode variants are
  extra negatives for `brief-notes` and `brief-no-statement`, and `named-voice` for the
  voice ids.
- The demo's `product.toml` loads as primary evidence unchanged
  (`test_product_toml_is_valid_primary_evidence`).

### AC-8 · Deck vs brief (phase A1 form, B-3) · PASS

```
$ keyline check fixtures/briefs/drift/base.pptx --brief fixtures/briefs/drift/base.brief.toml -o $SCRATCH/ac8
validate: passed
0 findings: 0 error, 0 warning, 0 advisory
note (L-010): LibreOffice re-fits stored autofit text and substitutes fonts through fontconfig, …
render engine: LibreOffice 26.8.0.3 680(Build:3), rasterized with pypdfium2
exit 0
$ keyline lint fixtures/briefs/drift/<drift>.pptx --brief fixtures/briefs/drift/base.brief.toml --json
drift-headline: [(3, 'brief-headline', 'warning')]
drift-slide-count: [(0, 'brief-slide-count', 'error')]
drift-unsourced: [(3, 'unsourced-number', 'warning')]
drift-source-missing: [(4, 'source-missing', 'warning')]
drift-undisclosed: [(0, 'fiction-undisclosed', 'warning')]
drift-role: [(2, 'brief-role', 'warning')]
$ pytest -q tests/acceptance/m2/test_ac08_drift.py
9 passed
```

- `fixtures/briefs/src/build_drift.py` builds `base.pptx` the way the pen will: the
  Swiss neutral template, text in the region placeholders, the keyline rule on evidence
  slides, two source lines and the disclosure note on the last slide. The test asserts
  each placeholder sits exactly on its region box. Evidence is the read-only
  `examples/bonsaihub/product.toml`.
- Each drift is the base plus one pinned change (AC-8's table); each gives exactly one
  finding and nothing else moves. A rebuild into a temporary directory is
  byte-identical to the committed decks.
- A2 repeats AC-8 on a pen-built deck.

### AC-9 · Pack invariants and templates (with B-8.7 and B-8.9) · PASS

```
$ pytest -q tests/acceptance/m2/test_ac09_pack_invariants.py tests/acceptance/m2/test_ac09_templates.py
30 passed / 76 passed
$ python src/keyline/packs/swiss/src/build_templates.py $SCRATCH/tpl/new
$ sha256sum src/keyline/packs/swiss/swiss-neutral-*.pptx $SCRATCH/tpl/new/*.pptx
29726d09c939fdd84f11e43edc44aeecb040db23a5659bcedbeae361b360730e  src/keyline/packs/swiss/swiss-neutral-presented.pptx
2b7f19df4ba9d39986188ed35de95dd375ab3b71ef19a38043599c4e837c67e3  src/keyline/packs/swiss/swiss-neutral-read.pptx
29726d09c939fdd84f11e43edc44aeecb040db23a5659bcedbeae361b360730e  $SCRATCH/tpl/new/swiss-neutral-presented.pptx
2b7f19df4ba9d39986188ed35de95dd375ab3b71ef19a38043599c4e837c67e3  $SCRATCH/tpl/new/swiss-neutral-read.pptx
$ officecli validate src/keyline/packs/swiss/swiss-neutral-presented.pptx   (and -read)
Validation passed: no errors found.
Validation passed: no errors found.
```

- **Invariants (B-8.7):** 1 (hierarchy), 2 (body floor), 3 (source floor) and 7 (KPI
  numerals) on the system, both modes; 4 (contrast normal for every pair a style
  allows, and the surface accent) and 6 (font families) for each of the three voices
  in both modes; 5 (neutral paper, no terracotta) on `neutral` only, with
  `voice-claude-look` silent for all three stock voices.
- **Templates (§5.3, B-8.9):** built per (system, voice, mode) in memory; only the
  neutral pair is committed. For all six builds (3 voices × 2 modes) the tests read the
  file with spec 001's own reader and check: 16:9, no slides; master background paper
  and the section layout ink, in the voice's values; master and layouts hold
  placeholders only; every placeholder ≥ 1.27 cm from every edge; theme colours are the
  voice's values through the plan's role mapping (hlink = ink); theme major font =
  display and minor = text; layout names parse to every role; placeholder `lstStyle`s
  carry the pack's size and the voice's colour, `+mj-lt` for display styles and
  `+mn-lt` for text styles; section placeholders are paper and accent_on_ink;
  `txStyles` carry the mode's sizes at all nine levels. A python-pptx round trip (one
  slide per layout, every placeholder filled) lints with no `adapter-unresolved`, sizes
  on the scale, fonts equal to the voice's, colours in its palette. `officecli validate`
  passes on all six builds.
- The neutral pair rebuilds byte-identically, both in-process and through the build
  script into a new directory.

### AC-14 · Render engines · PASS (LibreOffice 26.8.0.3, B-7)

```
$ keyline render fixtures/golden/kpi-recipe.pptx -o $SCRATCH/ac14 --engine libreoffice
note (L-010): LibreOffice re-fits stored autofit text and substitutes fonts through fontconfig, so line breaks can differ from PowerPoint's.
render engine: LibreOffice 26.8.0.3 680(Build:3), rasterized with pypdfium2
$SCRATCH/ac14/slide-01.png … slide-04.png
$SCRATCH/ac14/contact.png
exit 0
$ PATH=<empty dir> keyline render fixtures/golden/kpi-recipe.pptx -o … --engine libreoffice
keyline: render failed: libreoffice is not installed; install LibreOffice (https://www.libreoffice.org/download/) and a rasterizer: pip install pypdfium2, or poppler's pdftoppm
exit 1
$ PATH=<empty dir> keyline check fixtures/golden/kpi-recipe.pptx -o …
validate: skipped (officecli is not installed)
7 findings: 0 error, 7 warning, 0 advisory
render: skipped (officecli is not installed; install it with: npm install -g @officecli/officecli; or install LibreOffice (https://www.libreoffice.org/download/) and a rasterizer: pip install pypdfium2, or poppler's pdftoppm)
exit 2
$ pytest -q tests/acceptance/m2/test_ac14_render_engines.py
8 passed
```

- One 1280-px PNG per slide and `contact.png`; `auto` picks LibreOffice when `soffice`
  and a rasterizer are present (tested), and falls back to OfficeCLI when `soffice` is
  not found (tested with a PATH holding only `officecli`).
- The pdftoppm rasterizer is tested too (pypdfium2 hidden in-process).
- **B-7:** every LibreOffice render prints the `soffice --version` line it ran on; the
  render results in this report ran on LibreOffice 26.8.0.3. The line-pitch and
  wrap-margin measurement B-7 asks for belongs to AC-13(b) and happens in A2.

### AC-14b · Validate step · PASS

```
$ keyline check fixtures/validate/editorial-bogus.pptx -o … --engine officecli
validate: 1 schema error(s)
slide 1 · ooxml-invalid · warning · /ppt/slides/slide1.xml /p:sld[1]/p:cSld[1]: [Schema] The element has invalid child element 'http://schemas.openxmlformats.org/presentationml/2006/main:bogus'.
14 findings: 0 error, 8 warning, 6 advisory
$ PATH=<empty dir> keyline check fixtures/validate/editorial-bogus.pptx -o …
validate: skipped (officecli is not installed)
13 findings: 0 error, 7 warning, 6 advisory
exit 2          (lint's exit code: `keyline lint` on the same deck also exits 2)
$ pytest -q tests/acceptance/m2/test_ac14b_validate.py
9 passed
```

`fixtures/validate/src/build_bogus.py` copies the golden `editorial.pptx` part by part
and adds `<p:bogus/>` to slide 1's `p:cSld`; the golden deck is untouched, and the
build is byte-stable. `--no-validate` skips the step; unreadable output gives one
finding with its first line; `lint` never validates.

### AC-16 · Doctor (with B-8.12) · PASS

```
$ keyline doctor
PYTHON_OK           Python 3.11.16
LXML_OK             lxml 6.1.3
PILLOW_OK           Pillow 12.3.0
PPTX_OK             python-pptx 1.0.2
RENDER_LIBREOFFICE  LibreOffice at /usr/bin/soffice
RASTER_PDFIUM       pypdfium2
VALIDATE_OFFICECLI  officecli validate at /usr/bin/officecli
FONT_OK             Arial: fc-match gives Liberation Sans
FONT_OK             Times New Roman: fc-match gives Liberation Serif
FONT_OK             Courier New: fc-match gives Liberation Mono
FONT_SUBSTITUTED    Georgia: fc-match gives Noto Serif
                    install: Gelasio (metric-compatible with Georgia): Gelasio-Regular.ttf and Gelasio-Bold.ttf from fonts/ttf in https://github.com/SorkinType/Gelasio (OFL-1.1)
FONT_SUBSTITUTED    Calibri: fc-match gives Noto Sans
                    install: Carlito (metric-compatible with Calibri): apt install fonts-crosextra-carlito
FONT_SUBSTITUTED    Cambria: fc-match gives Noto Serif
                    install: Caladea (metric-compatible with Cambria): apt install fonts-crosextra-caladea
PACKS: swiss
exit 0
$ pytest -q tests/acceptance/m2/test_ac16_doctor.py
6 passed
```

- `--json` reports every §7 check, one entry per portable font, the packs and
  `lint_can_run`.
- `NO_PPTX` is tested in a real venv that has lxml and Pillow but not python-pptx: it
  reports `NO_PPTX` with `pip install "keyline[pen]" (or pip install python-pptx)` and
  exits 0. A second venv without lxml and Pillow reports `NO_LXML` and `NO_PILLOW` and
  exits 1, which is why the CLI and `render.py` now import lxml and Pillow lazily.
- Without `fc-match`, fonts are checked by file name in the standard folders (Q-40).

---

## Amendment B-8 (what Tyler asked the report to cover)

**The three stock voices' checks, computed with `keyline.colorspace` and
`text_contrast.contrast` at HEAD** (they match B-8.10's table to the printed precision;
`test_stock_voice_values_and_checks` asserts every number):

| voice | fonts | ink/paper | muted/paper | accent/paper | paper/ink | accent_on_ink/ink | paper L\* / C\* / h | accent HSL h | `voice-contrast` | `voice-claude-look` |
|---|---|---|---|---|---|---|---|---|---|---|
| `neutral` | Arial / Arial | 16.85 | 5.98 | 4.61 | 16.85 | 4.72 | 95.4 / 1.02 / 110 | 6 | 0 pairs below 4.5 | no cream paper, no terracotta |
| `night` | Arial / Arial | 15.02 | 7.35 | 9.54 | 15.02 | 5.00 | 8.2 / 2.44 / 267 | 42 | 0 pairs below 4.5 | no cream paper, no terracotta |
| `field` | Georgia / Georgia | 14.11 | 6.47 | 6.49 | 14.11 | 7.55 | 95.1 / 2.51 / 144 | 221 | 0 pairs below 4.5 | no cream paper, no terracotta |

One observation (plan Q-34): `night`'s **ink** (`ECECE8`: L\* 93.3, C\* 2.06, h 110.0)
falls inside §3.2's cream band. B-8 tests only `paper`, so `voice-claude-look` is silent;
a test pins the fact.

**The neutral templates rebuilt byte-identically:** see AC-9 (SHA-256
`29726d09…0730e` presented, `2b7f19df…c67e3` read, the committed files and a fresh build
through the script). The data move itself was lossless: at T-08r the templates built
from the system plus the neutral voice were byte-identical to T-09's pre-B-8 files
(`b8423af2…` and `4dbb6656…`); T-09r then changed them on purpose (the template title
now names the voice).

**The 35 registry entries:** see AC-1.

**Fit-table twins on this machine** (`fc-list : family`):

| family | twin | present |
|---|---|---|
| Arial | Liberation Sans | yes |
| Times New Roman | Liberation Serif | yes |
| Courier New | Liberation Mono | yes |
| Georgia | Gelasio | **no** (fc-match gives Noto Serif) |
| Calibri | Carlito | **no** (Noto Sans) |
| Cambria | Caladea | **no** (Noto Serif) |

A1 builds no fit tables. As things stand, A2's AC-13(a) would run for the three
Liberation twins here and skip Gelasio, Carlito and Caladea by name. CI now installs
`fonts-crosextra-carlito` and `fonts-crosextra-caladea` (T-17), so CI can cover those
two. Gelasio has no GitHub release: its TTFs are in `fonts/ttf` of
https://github.com/SorkinType/Gelasio (OFL-1.1), which is where doctor points.

---

## Tasks and commits

| task | commit(s) |
|---|---|
| plan, tasks, audit 01, B-1 … B-7 | `b349766`, `9079538` |
| T-01 baseline | `c46622f` |
| T-02 dependencies and CI | `25fb094` |
| T-03 registry and context | `54d1d31` |
| T-04 config | `d2335fd` |
| T-05 roles | `797fca8`, `3e8f270` (restored the M1 rule decks the rebuild had rewritten) |
| T-06 source and note lines | `2ba9e09` |
| T-07 colour spaces and pack-free rules | `ca148f6` |
| T-08 pack format and Swiss data | `ea659b7` |
| T-09 zipnorm and templates | `4da8304`, `b35ff05` |
| B-8 amendment, D-020, plan Q-26 … Q-41 | `c753c12` |
| T-08r system and voices | `4a3b299` |
| T-09r templates per voice | `dff39b0`, `c335e18` (fix, see *Process notes*) |
| T-10 pack rules, `--pack`, `--voice` | `5c227ea` |
| T-11 numeric tokens, table text | `5f696e3` |
| T-12 briefs, evidence, `keyline brief`, voice checks | `ff1717f` |
| T-13 deck vs brief, CLI resolution (and the drift decks) | `e1ea9e5` |
| T-14 AC-8 test | `7fb1253` |
| T-15 render engines | `fe43a33` |
| T-16 validate step | `c297d46` |
| T-17 doctor | `13f2af2` |
| T-18 acceptance sweep, docs | `ba905c7` |
| T-19 this report | the next commit |

---

## Deviations

1. **Templates renamed.** Spec §5.1 and T-09 said one template per mode, and T-09
   committed `swiss-presented.pptx` and `swiss-read.pptx` (`b35ff05`) about an hour
   before B-8 arrived. I implemented B-8.9 as Q-26 proposes: `templates` left
   `pack.toml`, and the committed pair became `swiss-neutral-presented.pptx` and
   `swiss-neutral-read.pptx`. Reason: templates are now per voice, so the file name
   carries the voice.
2. **`ooxml-invalid`'s slide.** Spec §7 said `slide` is N when the part is
   `/ppt/slides/slideN.xml`; I implemented the slide's position in the deck (its
   `sldIdLst` order). The two agree whenever parts are numbered in order, as in the
   fixture. Where they differ, the position is the slide lint's own findings name.
3. **The §4.5 rules' fixtures live in `fixtures/briefs/drift/`.** The spec 001 harness
   requires a positive and a negative case for every rule with a deck check, and the
   AC-8 drift decks are exactly that for the six §4.5 rules, so `fixtures/rules/expect.toml`
   points at them (`deck = "../briefs/drift/…"`, `brief = …`). For the same reason the
   drift decks landed with T-13 and T-14 holds only the AC-8 test.
4. **Drifts made with python-pptx, not lxml part edits.** Plan §5 said the drifts would
   be applied "by lxml edits to named parts". I built each drift from a fresh base with
   python-pptx (the pen's writer) and normalised the zip. Each drift still yields
   exactly one finding. The layout swap sets python-pptx's private `rel._target`.
5. **"Both" voices is a TOML error.** B-8.4 makes "neither or both" a schema error, but
   `voice = "…"` and a `[voice]` table use the same key, so TOML refuses the file before
   the schema check runs. The fixture exits 1 with one line, tomllib's message:
   `brief voice-both.brief.toml is not valid TOML: Cannot overwrite a value (at line 15, column 13)`.
6. **An extra validation in the pack loader.** A style may now colour a surface only
   with a role in that surface's `text` list (T-08r). The spec does not say this. It
   makes Q-28's pairs equal to every pair a style can produce, and Swiss already
   satisfied it.
7. **Voice fonts match exactly, without A-8's weight stripping.** Q-30 first said "after
   A-8 normalisation"; I changed the plan text (in T-08r, before Tyler ruled) to
   casefolding and whitespace collapse, because "Calibri Light" has no metric twin.
8. **Test file placement.** `tasks.md` named `tests/acceptance/test_cli_resolution.py`;
   the file is `tests/acceptance/m2/test_cli_resolution.py`, beside the other spec 002
   acceptance tests.
9. **Small additions the spec does not mention:** `keyline brief` prints the findings
   after the spine; an accepted finding's message gains `(accepted: <reason>)`;
   LibreOffice renders print a note when the PDF has fewer pages than the deck has
   slides (hidden slides are not exported); the template's `dc:title` names the voice.

## Process notes

- **CI failed on `ff1717f` (T-12):** `ruff format --check` wanted a quote style change
  in `src/keyline/brief.py`, which I had not formatted before committing. The next
  commit (`e1ea9e5`, T-13) formatted it and CI has been green since. I now run
  `ruff format --check` on `src tests fixtures tools` before every commit.
- **A bug found while writing this report** (`c335e18`): `build_templates.py OUT_DIR`
  raised `FileNotFoundError` when `OUT_DIR` did not exist. `write_all` now creates it,
  and a test rebuilds into a new directory.
- **Measured numbers replaced guesses in three tests.** In each case the test's expected
  value was my arithmetic, and the code's output (the WCAG formula) was right: 2.51 (not
  2.58) and 2.47 (not 2.37) for two low-contrast fixtures; `-5` is significant (`-5*`,
  as plan Q-6 says). No threshold or rule changed.

## Open questions

1. **Q-26 … Q-41** (plan §9) are B-8's ambiguities, each implemented as proposed. Four
   need an explicit ruling:
   - **Q-29:** voice findings are `keyline brief` findings only; `lint` and `check` name
     a failing voice on stderr and leave the deck's JSON unchanged.
   - **Q-32:** an accent role with the same value as a non-accent role is a schema
     error. B-8.5's list does not include this error.
   - **Q-33:** a dark-paper voice keeps the literal theme mapping (dk1 = ink, even when
     ink is light).
   - **Q-34:** `night`'s ink is in the cream band (see B-8 above).
2. **Twins before A2 (Q-41):** install Carlito, Caladea and Gelasio on this machine so
   AC-13(a) covers all six families here, or let it skip three by name?
3. **B-7 in A2:** the first A2 step measures line pitch and the wrap margin on
   LibreOffice 26.8.0.3 against §6.4's 24.2 values, and reports before any constant
   changes.
4. **G-1 and B-6:** only the neutral templates are committed. For the PowerPoint check,
   `python src/keyline/packs/swiss/src/build_templates.py OUT_DIR --voice night` (or
   `field`) writes the others.

---

## A1 fixes (audit 02)

Audit 02 ruled FIX, then A2. Its file is committed unchanged (`59360d1`, with B-9 … B-15
appended to the spec's amendment log and L-016 to the lessons). Each fix below landed
as its own commit with its tests. After each one, `pytest -q` passed in full and
`python tools/m1_baseline.py` printed `baseline: no differences`.

| FX | commit | full suite after it | M1 baseline |
|---|---|---|---|
| FX-1 | `5ed1fb6` | 619 passed | no differences |
| FX-2 | `9ad763d` | 624 passed | no differences |
| FX-3 | `6efe82f`, `ecc017f` (follow-up) | 631 passed; 670 after the follow-up | no differences |
| FX-4 | `af571f3` | 636 passed | no differences |
| FX-5 | `275082a` | 657 passed | no differences |
| FX-6 | `3275883` | 662 passed | no differences |
| FX-7 | `3477af7` | 663 passed | no differences |
| FX-8 | `a910810` | 669 passed | no differences |

### FX-1 · OfficeCLI works on private copies (B-14, L-016) · `5ed1fb6`

- **What changed.** `keyline.officecli.private_copy()` copies the deck to a
  unique file in a fresh temp directory. It runs `officecli close <copy>` in a `finally`
  and deletes the directory. The validate step and the officecli render engine use it,
  so the user's path never reaches OfficeCLI.
- **Reproduced first.** `officecli validate P` on a clean deck, then on the bogus deck
  copied to the same `P`, printed "Validation passed" twice; after `officecli close P` it
  reported the error.
- **Test:** `tests/acceptance/m2/test_fx1_officecli_copies.py`: sequences A (clean, then
  bogus) and B (bogus, then clean) on one path, each run twice in a row; four `check`
  runs in a row on a replaced deck (0, 1, 0, 1 `ooxml-invalid`); an officecli render
  after the deck is replaced (5 PNGs for the new 5-slide deck); the copy is unique,
  released and deleted, also when the call fails.

```
$ git stash push src/keyline/validate.py && pytest -q tests/acceptance/m2/test_fx1_officecli_copies.py -k sequence
4 failed, 4 deselected in 5.93s          (the old code: every sequence run is stale)
$ git stash pop && pytest -q tests/acceptance/m2/test_fx1_officecli_copies.py
8 passed in 35.08s
```

### FX-2 · `accepted` is limited to `acceptable_rules` (B-10) · `9ad763d`

- **What changed.** `thresholds.toml` `[common]` gains `acceptable_rules`. `accepted`
  in a pack, a pack voice or an inline voice may list only those rules, each with a
  non-empty reason. Anything else is a schema error.
- **Test:** `tests/unit/test_packs.py` and `test_voices.py` (gates and empty reasons are
  refused); the brief fixture `voice-accepted-gate.brief.toml`;
  `test_cli_resolution.py::test_a_brief_cannot_waive_a_gate` (the audit's scenario:
  `drift-undisclosed.pptx` with a waiving brief now exits 1, not 0).

```
$ keyline brief fixtures/briefs/voice-accepted-gate.brief.toml
keyline: voice-accepted-gate.brief.toml: [voice]: accepted[1]: 'fiction-undisclosed' cannot be accepted (only claude-look-palette, voice-claude-look, closing-cliche, accent-overuse, equal-card-row, title-underline)
exit 1
```

### FX-3 · Render numbering and hygiene (B-13) · `6efe82f`

- **What changed.**
  - LibreOffice exports hidden slides (`impress_pdf_Export` with
    `ExportHiddenSlides`). Checked on 26.8.0.3: a 4-slide deck with one hidden slide gave
    3 pages before and 4 after.
  - A page count that still differs is a render failure.
  - A deck with no slides fails with "deck has no slides".
  - Earlier `slide-*.png` and `contact.png` files are removed.
  - Names are zero-padded to max(2, digits).
  - `soffice` and `officecli` run in their own process group, which a timeout kills
    whole, and LibreOffice's temp directory is always removed.
  - An unusable `-o` is a render failure.
- **Test:** `tests/acceptance/m2/test_fx3_render.py`:
  - the hidden-slide deck's four PNGs are pixel-identical to the unhidden deck's;
  - padding, including a 3-page PDF named for a 120-slide deck;
  - the 0-slide neutral template;
  - `-o` on a file;
  - a reused directory;
  - a fake `soffice` whose child process dies on a 1 s timeout.

```
$ keyline render src/keyline/packs/swiss/swiss-neutral-presented.pptx -o $SCRATCH/e
keyline: render failed: deck has no slides
exit 1
$ keyline check fixtures/golden/kpi-recipe.pptx -o $SCRATCH/afile --no-validate     (afile is a file)
7 findings: 0 error, 7 warning, 0 advisory
render: skipped (cannot use $SCRATCH/afile as the output directory: File exists)
exit 2
$ pytest -q tests/acceptance/m2/test_fx3_render.py
7 passed
```

- **Follow-up `ecc017f`.** CI has neither LibreOffice nor OfficeCLI, so `render` stopped
  at the engine check before reaching "deck has no slides" or the unusable `-o`.
  Two FX-3 tests failed in CI on every push from `6efe82f` to `525ccb2`, though
  they passed here, where both engines exist. `render` now checks the user's inputs
  first: the deck, its slide count, and an `-o` that exists but is not a directory.
  `test_input_errors_come_before_the_engine_check` runs both cases with an empty PATH.
  I should have simulated CI's missing engines before pushing FX-3.

### FX-4 · The validate step's error paths (B-15) · `af571f3`

- **What changed.**
  - OfficeCLI's error envelope becomes one `ooxml-invalid` finding that carries its
    message, with the copy's name replaced by the deck's.
  - An officecli that cannot start (`officecli --version` fails) counts as absent:
    `validate: skipped (officecli could not run: …)`, `auto` render does not pick it,
    and doctor reports `NO_VALIDATOR` with the reason.
  - `test_auto_falls_back_to_officecli_without_soffice` links node beside an npm
    launcher, or skips when node is unreachable.
- **Test:** `tests/acceptance/m2/test_fx4_validate_errors.py`:
  - the envelope as parsed, and named after the user's deck;
  - the real OfficeCLI on a file it cannot open;
  - a stand-in `officecli` that exits 127 with "env: 'node': No such file or directory",
    for `check`, render and doctor.

```
$ pytest -q tests/acceptance/m2/test_fx4_validate_errors.py
5 passed
```

### FX-5 · Schema tightening and one-line errors (B-12 items 1–7, X-17) · `275082a`

- **What changed.**
  - `fullmatch` for ids, hex values and names.
  - Line breaks in headlines and reads are refused.
  - A brief's `voice` must be a name.
  - Every table in the pack loader is type-checked, with non-empty `modes`, bounded
    grid integers and finite numbers.
  - `--pack` with a mode the pack lacks is exit 1.
  - Paths that are directories, unreadable, not UTF-8 or nested too deeply are one-line
    errors.
  - `--pack NAME` always means the bundled pack (a path needs a separator or a leading
    `.`).
- **Test:**
  - `tests/unit/test_schema_mutations.py` replaces every value in `pack.toml` (6,524
    mutants), the neutral voice, the valid brief and both evidence files with 13 other
    values, or removes it. Each gives a one-line error or loads. Before the fix, 498
    pack mutants and 3 brief mutants raised other exceptions.
  - `tests/acceptance/m2/test_fx5_schema.py` has one test per item.

```
$ keyline brief fixtures/briefs
keyline: briefs: brief briefs is a directory, not a file
exit 1
$ keyline lint fixtures/briefs/drift/base.pptx --pack fixtures/briefs/packs/presented-only --voice src/keyline/packs/swiss/voices/neutral.toml --mode read
keyline: mode: pack swiss has no read mode (presented)
exit 1
$ pytest -q tests/acceptance/m2/test_fx5_schema.py tests/unit/test_schema_mutations.py
21 passed
```

The `--pack NAME` rule (X-17) is part of FX-5 in the audit but sits outside its
"B-12 (to append)" paragraph, so it is not in the spec's amendment log; see *Open
questions (audit 02)*.

### FX-6 · Source and note line detection (B-12, continued) · `3275883`

- **What changed.** The spaces before the colon may be any Unicode space separator (Zs)
  or a tab. Classification reads the paragraph's inked text, the text §4.4 scans.
- **Test:** `tests/unit/test_line_kind.py`:
  - no-break, narrow no-break and ideographic spaces;
  - a zero-width space is not a space;
  - a hidden "Source: " prefix leaves "12,400 trees" in the scan.

```
$ pytest -q tests/unit/test_line_kind.py
19 passed
```

### FX-7 · `night`'s ink, every background checked, exact font names (B-9, B-11) · `3477af7`

- **What changed.**
  - `voice-claude-look` tests every background role (Swiss: paper and ink).
  - `night`'s ink is `ECECEC`. Recomputed: C\* 0.00; ink/paper 15.06, paper/ink 15.06,
    accent_on_ink/ink 5.02, the auditor's values. muted/paper 7.35 and accent/paper
    9.54 are unchanged.
  - `off-pack-font` compares exact names after casefold and whitespace collapse.
- **Fixtures changed by the rulings:**
  - `off-pack-font--pos` gains Arial Black and Arial Narrow;
  - `off-pack-font--neg` replaces "Arial Bold", now a finding, with "  ARIAL ";
  - `pack-voice-night` is rebuilt with the new ink.

  These are spec 002 fixtures; no golden or provided fixture changed.
- **Test:**
  - `test_ac09_pack_invariants.py` carries B-9's `night` values, and a new test shows a
    cream ink fires;
  - `test_pack_rules.py::test_off_pack_font_matches_exact_names`, while `font-count`'s
    A-8 still folds both names into Arial.

```
$ keyline brief fixtures/briefs/named-voice.brief.toml      (voice = "night")
0 findings: 0 error, 0 warning, 0 advisory
$ pytest -q tests/acceptance/m2/test_ac09_pack_invariants.py tests/unit/test_pack_rules.py
36 passed
```

### FX-8 · The recorded limits · `a910810`

- **What changed.** The `numtokens` docstring lists B-5's limits and the audit's new
  ones. Each new limit is pinned by a test and agrees with the oracle:
  - "B2B" gives `2B`, "4K" gives `4K`, "COVID-19" gives `19`, "iPhone 15" gives `15`;
  - "5 %" with a no-break space gives a non-significant `5`;
  - a source line inside a table cell is not recognised.

  `build_drift.py` pins python-pptx 1.0.2 (the ruling on deviation 4). L-016 landed with
  the audit commit.
- The commit is typed `docs:` rather than `fix:` because it changes no behaviour.
- `check.md` does not exist before phase B; its task carries these limits (see
  `tasks.md`).

```
$ pytest -q tests/unit/test_numtokens.py
38 passed
```

### Metric twins installed (Q-41)

Gelasio came from its upstream repository, whose TTFs sit in `fonts/ttf` (it publishes no
releases), into `~/.local/share/fonts/gelasio/`, with no sudo:

```
$ sha256sum ~/.local/share/fonts/gelasio/*.ttf
e0ef3addf1acf35f5c6aef2be00d0a2c01363bf70a5950e16650976051a0c462  Gelasio-Bold.ttf
48c797fbe0e07c48a18cb962e7bdfa23f19618327dddf54093265328dc9eb39d  Gelasio-Regular.ttf
$ fc-cache -f && fc-match Georgia && fc-match "Georgia:bold"
Gelasio-Regular.ttf: "Gelasio" "Regular"
Gelasio-Bold.ttf: "Gelasio" "Bold"
```

Carlito and Caladea were already installed as system packages (`sudo pacman -S
ttf-carlito ttf-caladea`; `pacman -Qi` shows them installed on 2026-09-29 at 16:05 +07,
before this step):

```
$ fc-match Calibri; fc-match Cambria
Carlito-Regular.ttf: "Carlito" "Regular"
Caladea-Regular.ttf: "Caladea" "Regular"
$ keyline doctor | grep FONT
FONT_OK             Arial: fc-match gives Liberation Sans
FONT_OK             Times New Roman: fc-match gives Liberation Serif
FONT_OK             Courier New: fc-match gives Liberation Mono
FONT_OK             Georgia: fc-match gives Gelasio
FONT_OK             Calibri: fc-match gives Carlito
FONT_OK             Cambria: fc-match gives Caladea
```

So all six families' twins are present here, and A2's AC-13(a) can cover each of them.

### Open questions (audit 02)

1. **X-17 in the amendment log.** The `--pack NAME` rule is implemented but was not
   appended, because it sits outside the "B-12 (to append)" paragraph. Should it be
   recorded, for example as part of B-12?
2. **Line breaks (B-12 item 2).** B-12 lists `\n \r \v U+2028 U+2029`. The check also
   refuses the other characters `str.splitlines()` splits on (`\f`, `\x1c`–`\x1e`,
   `\x85`), since each would also break the one-line spine.

