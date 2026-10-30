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

---

## A1 fixes, round 2 (audit 03)

Audit 03 ([audit-03-a1fix.md](audit-03-a1fix.md)) accepted FX-1 … FX-8 and found
FX-9 … FX-15. It is committed unchanged in `3e635cc`, with B-16 … B-20 appended to the
spec's amendment log and the rulings on Q-42 … Q-46 recorded in `plan.md` and `tasks.md`.
Each fix below landed as its own commit with its tests. Before each push, the full suite
ran twice: once normally, and once with a CI-like PATH that holds every `/usr/bin`
command except LibreOffice, OfficeCLI, pdftoppm and node (the lesson from `ecc017f`).
`python tools/m1_baseline.py` printed `baseline: no differences` after each fix.

| FX | amendment | commit | full suite | CI-like PATH |
|---|---|---|---|---|
| FX-9 | B-19 | `f43b9cf` | 675 passed | 649 passed, 26 skipped |
| FX-10 | B-19 | `636965f` | 683 passed | 655 passed, 28 skipped |
| FX-11 | B-19 | `2848e28` | 694 passed | 662 passed, 32 skipped |
| FX-12 | B-18 | `a3c141b` | 700 passed | 668 passed, 32 skipped |
| FX-13 | B-12 item 7 | `97b4e8c` | 701 passed | 669 passed, 32 skipped |
| FX-14 | B-20 | `e9ed928` | 719 passed | 687 passed, 32 skipped |
| FX-15 | — | `126fc59` | 720 passed | 688 passed, 32 skipped |

### FX-9 · LibreOffice converts a private copy (B-19) · `f43b9cf`

`convert_to_pdf()` copies the deck into the render's temp directory as `deck.pptx`
(`deck.pptm` for a .pptm deck), converts that, and reads `deck.pdf`. T-20's
measuring tool reuses it.
- **Test:** `test_fx9_lo_private_copy.py`. The fixed name for three odd names is
  checked in process, with no engine needed; a symlinked deck and a `deck.` name render
  with LibreOffice.

```
$ ln -s real-target.pptx link.pptx && keyline render link.pptx -o out --engine libreoffice
render engine: LibreOffice 26.8.0.3 680(Build:3), rasterized with pypdfium2
out/slide-01.png … out/slide-04.png, out/contact.png
exit 0
```

### FX-10 · The OfficeCLI copy is `.pptx` (B-19) · `636965f`

The copy is `deck-<uuid>.pptx`, or `.pptm` only for a .pptm deck, compared
case-insensitively.
- **Test:** `test_fx10_officecli_suffix.py`:
  - the suffix for six names (these fail on the old code);
  - "clean v1.2" and "deck.pptx.bak" validate as clean decks with OfficeCLI.

```
$ keyline check "clean v1.2" -o blocker          ("clean v1.2" is golden/editorial.pptx)
validate: passed
13 findings: 0 error, 7 warning, 6 advisory
```

### FX-11 · Engine hygiene (B-19) · `2848e28`

- **What changed.**
  - Every engine call goes through `keyline._proc.run`. It runs in its own process
    group, which a timeout or any interruption kills whole, and its output is decoded
    as UTF-8 with replacement.
  - The CLI turns SIGINT and SIGTERM into `Interrupted`, so every `finally` runs:
    OfficeCLI copies are closed and temp directories removed. keyline then exits 130
    or 143, and a second signal is ignored during cleanup.
  - An explicit empty `-o` is an unusable `-o`.
- **Test:** `test_fx11_engine_hygiene.py`. All 11 tests fail on the old code:
  - SIGINT (to the group, as Ctrl-C sends it) and SIGTERM, mid-validate and mid-render;
  - both with stand-in engines, which run anywhere, CI included, and with the real
    LibreOffice (a 150-slide deck) and OfficeCLI;
  - each asserts exit 130/143, no `keyline-*` directory in the private TMPDIR, and no
    process whose command line mentions it, checked through `/proc`;
  - non-UTF-8 stderr, a validate timeout, and an empty `-o`.

```
$ pytest -q tests/acceptance/m2/test_fx11_engine_hygiene.py
11 passed
$ keyline render real-target.pptx -o ''
keyline: render failed: cannot use '' as the output directory: it is empty
exit 1
```

### FX-12 · A voice's schema is closed (B-18) · `a3c141b`

Allowed keys:
- top level: `schema`, `name` (file only) and `accepted`;
- `[fonts]`: `display` and `text`;
- `[palette]` and `[why]`: palette roles.

Any other key is a schema error that names it, and `why.accepted` gets the hint that
`accepted` belongs before `[fonts]`. Evidence files keep §4.1's unknown-keys rule.
- **Test:** `test_voices.py`: one test per closed table, plus the audit's repro as a
  voice file. The voice mutation test now parses the inline form, so its mutants still
  reach past the `name` check.

```
$ keyline lint base.pptx --pack swiss --voice ./spec.toml     (the audit's repro)
keyline: voice spec.toml: why.accepted: accepted belongs before [fonts]
exit 1
```

### FX-13 · An unreadable pack or voice path (B-12 item 7) · `97b4e8c`

- **Test:** `test_fx13_unreadable_paths.py`. As a non-root user, both paths under a
  mode-000 directory give one line and exit 1. This fails on the old code.

```
$ keyline lint base.pptx --pack ./locked/pk --voice neutral
keyline: pack directory './locked/pk' cannot be read: Permission denied
exit 1
```

### FX-14 · Reasons, schema types, one-line messages (B-20) · `e9ed928`

- **What changed.**
  - A reason needs a character outside Zs, Cc and Cf.
  - `schema` is the integer 1 in all four file kinds.
  - Every one-line error the CLI prints goes through `keyline.escape.esc`.
  - The four garbled messages now name the file once, then the key.
- **Test:** `test_fx14_messages.py`:
  - invisible reasons;
  - `schema` = true, 1.0, "1" and 2 in each file kind;
  - forged lines through `--pack`, `--voice` and deck paths;
  - a brief's pack with a line break;
  - the four messages.

```
$ keyline lint real-target.pptx --pack $'swiss\nkeyline: all clear' --voice neutral
keyline: pack not found: swiss\nkeyline: all clear
exit 1
```

### FX-15 · Test, noise and a known limit · `126fc59`

- **What changed.**
  - The fallback test checks engine selection, and skips when the selected OfficeCLI
    finds no headless browser.
  - L-002 is no longer printed when OfficeCLI cannot start.
  - The `numtokens` docstring records the invisible "Source: " limit (principle VIII).
    Phase B's `check.md` task carries it.
- **Test:** `test_no_l002_note_when_officecli_cannot_start`.

```
$ PATH=<a broken officecli only> keyline render real-target.pptx -o out2
keyline: render failed: officecli could not run: env: node: No such file or directory; or install LibreOffice (…)
exit 1                                                   (no L-002 note)
```

### Deviation (round 2)

- **L-002 is still printed with the not-installed hint.**
  - The audit said: print L-002 "only when OfficeCLI actually renders".
  - Implemented: no note when OfficeCLI cannot start, but the note stays when OfficeCLI
    is not installed.
  - Why: spec 001's `test_render_without_officecli_exits_1` asserts L-002 in exactly
    that case, and AC-2 does not allow changing it.

---

# Report A2 · Spec 002 (the fit estimator and the pen)

- **Phase:** A2, tasks T-20 … T-32 of [`tasks.md`](tasks.md), with amendment B-21
  (audit 04).
- **Branch:** `002-skill-pack`, head `ad17fa9` when this report was written (the report's
  own commit follows it).
- **Status:** AC-10, AC-11, AC-12, AC-13(a), AC-15 and AC-8 (again, on a pen-built deck)
  pass locally, with LibreOffice and OfficeCLI. **AC-13(b) fails as written, at the left
  edge only.** A line that starts with a glyph whose left side bearing is negative (bold
  Gelasio's "v" or "j") puts ink up to 2.7 px left of its region box (measured), and up
  to 7.4 px in the worst case. The edges the estimator decides (right, top, bottom) hold.
  See [AC-13](#ac-13--fit-is-conservative--a-pass-b-fail-as-written-left-edge-only).
- **CI** (Python 3.11 and 3.13, no LibreOffice, no OfficeCLI) is green on every A2 push,
  the last at `ad17fa9`. That push carried `e4a2f26`, `6ed849d` and `ad17fa9` together.
- **Stop here for G-1 and the A2 audit.**
- T-20's measurement and its addendum come first, as they were written. The A2
  acceptance criteria follow from [Environment (A2)](#environment-a2).

## T-20 · B-7 measurement on LibreOffice 26.8.0.3 · STOPPED: the wrap margin differs

- **Tool:** `tools/measure_lo.py` (dev only).
  - The probe decks name the six portable families. Fontconfig resolved each to its
    twin; the script checks that first and would stop otherwise (Q-44a).
  - The decks go through keyline's own `render.convert_to_pdf` (the render engine's
    soffice command), and glyph origins are read back with pypdfium2.
- **Evidence:** `specs/002-skill-pack/evidence/lo-26.8.0.3-measurements.txt`. Every value
  in it is tagged with `LibreOffice 26.8.0.3 680(Build:3)` (Q-44b). A second run gave the
  same numbers.

```
$ python tools/measure_lo.py specs/002-skill-pack/evidence/lo-26.8.0.3-measurements.txt
version: LibreOffice 26.8.0.3 680(Build:3)
fc-match: Arial -> Liberation Sans, Times New Roman -> Liberation Serif, Courier New ->
  Liberation Mono, Georgia -> Gelasio, Calibri -> Carlito, Cambria -> Caladea (all ok)
against spec 002 §6.4 (LibreOffice 24.2):
  pitch, Arial -> Liberation Sans: 1.2000 … 1.2015 em; §6.4 says 1.20 (±0.005): MATCHES
  wrap, Arial bold 14 pt: 2 lines at 1.000x and 1.002x, 1 line at 1.005x and 1.010x: DIFFERS
exit 2
```

### Line pitch · matches §6.4

- **1.2000 em** at 24, 48 and 60 pt, regular and bold, for all six twins. This holds for
  line breaks inside one paragraph and for separate paragraphs alike.
- **1.2015 em at 13 pt,** for all six twins (15.62 pt instead of 15.60). LibreOffice
  positions text in 1/100 mm, so this is rounding, and it is inside the ±0.005 em
  tolerance.
- **Also measured:** the first baseline sits 1.000 em (±0.001) below the box top, in
  every twin. AC-13(b) will need this.

### Wrap margin · differs from §6.4's 24.2 observation

§6.4 says: a bold 14 pt label wraps to 2 lines at 1.000× and 1.002× its advance sum,
but not at 1.005×. On 26.8.0.3, the smallest box that holds each bold 14 pt label on one
line (as box width ÷ fontTools advance sum; scanned 0.9800 … 1.0100 in 0.0005 steps) is:

| family (twin) | ACTIVE KEEPERS BY MONTH | median wait for a match | Oldest tree on the waitlist |
|---|---|---|---|
| Arial (Liberation Sans) | **1.0020** | 1.0030 | 1.0030 |
| Times New Roman (Liberation Serif) | 1.0005 | 1.0010 | 1.0010 |
| Courier New (Liberation Mono) | 1.0030 | 1.0030 | 1.0030 |
| Georgia (Gelasio) | 1.0030 | 1.0030 | 1.0030 |
| Calibri (Carlito) | 0.9985 | 0.9980 | 0.9990 |
| Cambria (Caladea) | 0.9995 | 1.0000 | 1.0000 |

- **The difference.** For Arial, two of the three labels match §6.4's description
  exactly: they wrap at 1.002× and fit at 1.005×. "ACTIVE KEEPERS BY MONTH" already fits
  at 1.0020×.
- **Why this probably isn't a 24.2-vs-26.8 change.** The threshold depends on the
  string. §6.4 doesn't record which label the 24.2 reviewer measured, so these numbers
  can't be compared like for like.
- **Carlito and Caladea** fit below their advance sums. Their layout comes out narrower
  than the unkerned sum.
- **What does not change.** Every family and label fits by **1.0030×**. §6.4's 0.99
  margin accepts text only in a box at least 1/0.99 = **1.0101×** its advance sum, which
  leaves at least 0.7 % slack in every case measured.

### Proposal, for Tyler or the auditor to rule (B-7: no constant is set before that)

1. Keep §6.4's wrap margin: a line fits when its advance sum ≤ 0.99 × the available
   width. On 26.8.0.3 it is conservative for all six twins; the largest measured
   threshold is 1.0030×.
2. Set `line_pitch_em = 1.2` for all six twins, each table stored with
   `LibreOffice 26.8.0.3 680(Build:3)` (Q-44b).
3. Record in §6.4's place (as an amendment, if you want it in the spec) that on 26.8.0.3
   the one-line threshold is 0.998× … 1.003× the advance sum, depending on the string
   and the family. The 24.2 phrase "wraps at 1.002×" holds for some strings, not all.

**T-21 … T-32 have not started.** They wait for this ruling, as T-20 says.

### T-20 addendum · audit 04 and B-21 · both criteria hold

- **Audit 04** ([audit-04-t20.md](audit-04-t20.md)) ran the same tool on LibreOffice
  24.2.7.2 and got the same pitch table and the same four-factor wrap table. §6.4's
  sentence had generalised one label; nothing changed between 24.2 and 26.8.
- **The rulings (B-21):**
  - keep the 0.99 wrap margin;
  - `line_pitch_em = 1.2`;
  - the height test adds 0.01 mm per line;
  - the fit tables record each twin's missing Vietnamese letters.
- **The tool.** `tools/measure_lo.py` now also runs the auditor's stress set: seven
  strings, 9–24 pt, regular and bold, tracked caps and Vietnamese, in boxes up to
  1/0.99× §6.4's estimate. It measures pitch at every (size, line spacing) of the Swiss
  pack, and its verdict is B-21's two criteria. The output replaces the first run's file
  under the same name, and a second run was identical.

```
$ python tools/measure_lo.py specs/002-skill-pack/evidence/lo-26.8.0.3-measurements.txt
version: LibreOffice 26.8.0.3 680(Build:3)
verdict (amendment B-21):
  (a) no stress case wraps at 1/0.99 = 1.0101: 420 cases, 0 wrap: HOLDS
  (b) every pitch <= size x 1.2 x line spacing + 0.01 mm (0.0283 pt): 198 probes, smallest slack 0.0000 pt: HOLDS
exit 0
```

- **Wrap, smallest fitting factor per case:**
  - 174 cases fit at ≤ 0.995×, 207 at 1.000× and 39 at 1.003×;
  - none needs more;
  - the auditor's 24.2 run gave 182 / 201 / 37.
- **Pitch at 9 pt, the tightest case.** The pitch is exactly one LibreOffice unit over
  1.2 em: 3.82 mm = 10.8283 pt, against 10.8000.
  - So the 0.01 mm allowance is used up exactly (slack 1.8e-5 pt).
  - The per-line steps read from the PDF scatter by about 0.001 pt, the PDF's coordinate
    precision (10.8290, 10.8280, 10.8280), so the tool uses their mean.
- **The first baseline** sits 1.00 em below the box top at line spacing 1.0, and
  1.12 em at 1.1. That matches the auditor's reading.

A2 continues from T-21.

---

## Environment (A2)

As in A1 (same machine), plus the pen's and the tools' libraries:

| what | version |
|---|---|
| Python (`.venv`) | 3.11.16 |
| lxml / Pillow / python-pptx / XlsxWriter | 6.1.3 / 12.3.0 / 1.0.2 / 3.2.9 |
| pypdfium2 / fontTools (dev) | 5.13.0 / 4.66.0 |
| LibreOffice (`soffice --version`) | `LibreOffice 26.8.0.3 680(Build:3)` |
| OfficeCLI | 1.0.152 |
| metric twins (`fc-match`) | all six: Liberation Sans, Serif and Mono, Gelasio, Carlito, Caladea |

## Reproduce (A2)

```sh
python -m pip install -e '.[dev]'
pytest -q                          # 863 passed, 1 xfailed, 3 xpassed here (AC-13(b), below)
pytest -q -m officecli             # 24 passed
python tools/m1_baseline.py        # baseline: no differences
python tools/fit_ratios.py         # AC-13(a) table
python tools/fit_stress.py         # AC-13(b); needs LibreOffice; exits 1 (as written)
python tools/left_overhang.py      # the left-edge table (fontTools)
python fixtures/packs/src/build_specimens.py OUT    # the three specimens
python fixtures/briefs/src/build_drift_pen.py OUT   # AC-8's pen-built decks
```

Without the engines: the suite on a CI-like PATH (no soffice, officecli, pdftoppm, node)
gives 826 passed, 41 skipped. With an empty PATH it gives 794 passed, 73 skipped.

## Acceptance criteria (A2)

### AC-10 · Token-only pen · PASS

```
$ pytest -q tests/acceptance/m2/test_pen_skeleton.py tests/acceptance/m2/test_pen_text_verbs.py \
    tests/acceptance/m2/test_pen_figure.py tests/acceptance/m2/test_pen_table_chart_image.py
55 passed
```

| AC-10 case | error | test |
|---|---|---|
| every public signature: no colour, font, size, length, coordinate or alignment | (inspection) | `test_pen_skeleton.py::test_no_public_parameter_accepts_a_raw_value` |
| a hex string, `24pt`, `2cm` (also `CC3322`, `12 px`, `3in`, `9144emu`) | `PenError` | `test_raw_values_are_refused_as_tokens`, `test_pen_errors_on_an_evidence_slide` |
| an unknown style or region | `PenError` | `test_pen_errors_on_an_evidence_slide` (`caption`, `aside`) |
| a style or component the role does not allow | `PenError` | `test_pen_errors_on_an_evidence_slide` (`lede` in presented, `attribution`), `test_components_the_role_does_not_allow` |
| a second component in an occupied region | `PenError` | `test_pen_errors_on_an_evidence_slide` |
| a 6-word label | `PenError` | `test_pen_figure.py::test_figure_errors`, `test_a_six_word_attribution_is_refused` |
| `figure()` on a series entry | `PenError` | `test_figure_errors` |
| a second accent over `accent_budget` | `PenError` | `test_a_second_accent_over_the_budget`, `test_a_highlight_counts_against_the_accent_budget` |
| a `numerals_max + 1`-th figure | `PenError` | `test_figure_errors` ("figure 2; at most 1 per slide") |
| an unknown evidence id | `EvidenceError` | `test_figure_errors` |
| an over-long headline, naming lines needed against lines available | `DoesNotFit` | `test_an_overlong_headline_does_not_fit`, `test_text_that_does_not_fit` |

### AC-11 · Pen determinism · PASS

```
$ python fixtures/packs/src/build_specimens.py b1; sleep 1; python fixtures/packs/src/build_specimens.py b2
$ sha256sum b1/*.pptx b2/*.pptx fixtures/packs/*.pptx        (condensed: first 16 hex digits, grouped)
fffb4e887ea7739d  b1/, b2/ and fixtures/packs/ swiss-specimen-presented-neutral.pptx
8c50fcfa55c3e947  b1/, b2/ and fixtures/packs/ swiss-specimen-presented-night.pptx
b3dea4e54b7b56f4  b1/, b2/ and fixtures/packs/ swiss-specimen-read-field.pptx
$ pytest -q tests/acceptance/m2/test_ac11_ac12_specimens.py tests/acceptance/m2/test_pen_determinism.py
15 passed
```

- Each specimen builds twice to the same bytes, and here to the committed bytes.
- `test_pen_determinism.py` (T-27) builds a deck with a chart, a table and a disclosure
  note twice, a second apart. The two are byte-identical. The outer and inner zips are
  sorted with fixed timestamps, and the dates come from the template.
- **Across machines,** the committed-deck test compares every XML part byte for byte, and
  the grid picture by its pixels. It skips the embedded chart workbook. The PNG's bytes
  come from Pillow's zlib and the workbook's from XlsxWriter, and neither is pinned
  (Deviation 5).

### AC-12 · Specimens pass · PASS

```
$ keyline brief fixtures/packs/swiss-specimen-{presented-neutral,presented-night,read-field}.brief.toml
0 findings: 0 error, 0 warning, 0 advisory       (each; exit 0)
$ keyline check fixtures/packs/swiss-specimen-presented-neutral.pptx \
    --brief fixtures/packs/swiss-specimen-presented-neutral.brief.toml -o $SCRATCH/g1-presented-neutral
validate: passed
slide 6 · unsupported-content · advisory · main-table · table text is not read in M1
1 finding: 0 error, 0 warning, 1 advisory
note (L-010): LibreOffice re-fits stored autofit text and substitutes fonts through fontconfig, …
render engine: LibreOffice 26.8.0.3 680(Build:3), rasterized with pypdfium2
exit 0
```

- `presented-night` and `read-field` give the same four lines and exit 0.
- There is no `adapter-unresolved` and no `ooxml-invalid`: OfficeCLI validated each
  deck, the chart included.
- The one advisory is the table's. Spec 002 §3 keeps the M1 advisory "table text is not
  read".
- **What the specimens hold.**
  - Each has nine slides covering every role: cover, statement, section, four evidence
    slides, quote and close.
  - The four evidence slides use `figure`, `chart_bar`, `table`, and `image` with
    `bullets`.
  - `text`, `source`, `note`, `attribution` and `notes` (from the brief) appear
    throughout, so every verb is used.
  - Every sentence is about the pack.
  - The grid picture on slide 7 is drawn by the build script from the pack's grid, in
    the deck's voice.

### AC-13 · Fit is conservative · (a) PASS, (b) FAIL as written (left edge only)

**(a) Widths against Pillow.**

```
$ python tools/fit_ratios.py          (condensed: the largest ratio per table)
Liberation Sans    regular largest 1.0002 (narrow)       Liberation Sans    bold largest 1.0002 (wide-caps)
Liberation Serif   regular largest 1.0005 (wide-caps)    Liberation Serif   bold largest 1.0004 (wide-caps)
Liberation Mono    regular largest 1.0002 (sentence)     Liberation Mono    bold largest 1.0002 (sentence)
Gelasio            regular largest 1.0004 (narrow)       Gelasio            bold largest 1.0003 (wide-caps)
Carlito            regular largest 1.0001 (caps-tracked) Carlito            bold largest 1.0001 (wide-caps)
Caladea            regular largest 1.0000 (sentence)     Caladea            bold largest 1.0000 (sentence)
                   Caladea, both weights: skipped, missing glyphs: vietnamese, vietnamese-caps
plain-Latin strings above 1.05: none
$ pytest -q tests/acceptance/m2/test_ac13a_fit_widths.py tests/unit/test_fit.py tests/unit/test_fit_tables.py
47 passed
```

- Every ratio lies between 0.9989 and 1.0005, inside [0.995, 1.25], for all twelve
  tables.
- Caladea's two Vietnamese strings are skipped by name. Its twin lacks those letters
  (see [the coverage limit](#the-script-coverage-limit-audit-04)).

**(b) Fit stress.**

- **The tool.** `tools/fit_stress.py` builds four decks with the pen, one per mode for
  each voice font: neutral (Arial, so Liberation Sans) and field (Georgia, so Gelasio).
  `night` has neutral's fonts.
- **What the stress fills, and how far.** Every text the estimator checks sits at the
  longest the pen accepts: one more word, or for a numeral one more digit, is refused.
  - The texts: every headline; `text` in every style a role allows, in every text
    region; `bullets`; a `table` (a header and three rows, two columns); a `figure`
    (numerals of 1 … 40 digits from an evidence file the tool writes, and a label);
    the attribution; and the footer's source and note lines.
  - The tool records which bound stopped each item:
    - the estimator stopped every headline, text, bullet list, footer and numeral, and
      the body cells of every table;
    - the 5-word caption cap stopped every figure label and attribution, and the header
      cells of 8 of the 12 tables (in the other 4 the table's height ran out first).
- **How it measures.**
  - Each stress slide is written once per text region, with only that region's shapes
    kept, and once empty (the control).
  - A text's ink is every pixel that differs from the control by more than 26 of 255
    in any channel.
- **Result.** 210 texts: 68 headlines, 38 texts, 12 bullet lists, 12 tables, 16
  figures, 4 attributions and 60 footers.

```
$ python tools/fit_stress.py > specs/002-skill-pack/evidence/fit-stress-lo-26.8.0.3.txt
LibreOffice: LibreOffice 26.8.0.3 680(Build:3)
…
refused at the shortest (not built):
  presented neutral: keyline:statement main: figure refused at its shortest (fit)
  presented neutral: keyline:close main: figure refused at its shortest (fit)
  presented field: keyline:statement main: figure refused at its shortest (fit)
  presented field: keyline:close main: figure refused at its shortest (fit)

210 texts; the most outside is +2.7 px (presented field, slide 16, keyline:statement title); 0 without ink
  left   at most +2.7 px (presented field, slide 16, keyline:statement title)
  top    at most -2.3 px (read field, slide 3, keyline:cover footer)
  right  at most +0.7 px (read field, slide 21, keyline:evidence main)
  bottom at most -1.8 px (presented field, slide 2, keyline:cover main)
over 2 px: 1 text(s)
  presented field, slide 16, keyline:statement title (headline (statement)): +2.7 px left
verdict, AC-13(b) as written (every edge): FAIL (tolerance 2 px)
verdict, the estimator's edges (right, top, bottom): PASS (tolerance 2 px)
exit 1
```

| mode, voice | texts | left | top | right | bottom |
|---|---|---|---|---|---|
| presented, neutral | 48 | +1.0 | −4.3 | −0.1 | −2.8 |
| presented, field | 48 | **+2.7** | −3.3 | −0.1 | −1.8 |
| read, neutral | 57 | +1.0 | −3.3 | −0.1 | −4.4 |
| read, field | 57 | +1.7 | −2.3 | +0.7 | −2.4 |

(px past each edge of the region box at 1280 px; negative means inside)

- **The estimator's claims hold.**
  - No line wrapped where the estimator said it would not: the right edge is at most
    +0.7 px, which is anti-aliasing at a region edge that falls mid-pixel.
  - No text ran below its region: the bottom stays at least 1.8 px inside.
- **Every positive left value is a glyph reaching left of its origin.**
  - The line starts at the region's left edge, with zero insets.
  - The failing text is a 60 pt bold Gelasio headline whose first line starts with
    "visitors". Gelasio Bold's "v" has a left side bearing of −49/2048 em: 1.9 px at
    60 pt, plus a pixel of anti-aliasing.
  - `tools/left_overhang.py` (`specs/002-skill-pack/evidence/left-overhang.txt`)
    tabulates the worst case: bold Gelasio's "j" (−172/2048 em) reaches 3.1 px left at
    28 pt, 5.4 px at 48 pt and 7.4 px at 66 pt.
  - In Arial bold, only a 120 pt numeral that started with "j" would pass 2 px, and
    numerals are digits.
- **The first T-30 run (`4e74905`) passed only by chance.** It left out tables, figures
  and attributions (Deviation 6), and in its 130 texts no line started with such a glyph.
  Adding the new kinds moved the corpus offsets, and one headline began with "v".
- **Nothing was tuned.** The corpus, the 2 px tolerance and the ink threshold are the
  same as in the first run. The ruling is Tyler's (Q-47).
- **The tests.**
  - `test_no_ink_past_the_edges_the_estimator_decides` must pass. It does, in all four
    decks.
  - `test_ac13b_as_written_no_ink_past_any_edge` is an expected failure until Tyler
    rules. It is non-strict, because whether a line starts with such a glyph depends on
    the corpus: 1 xfailed, 3 xpassed here.
  - `test_every_stressed_text_is_the_longest_the_pen_accepts` checks, without
    LibreOffice, that one more word or digit in any item is refused by the recorded
    bound.

```
$ pytest -q -rxX tests/acceptance/m2/test_ac13b_fit_stress.py
XFAIL …test_ac13b_as_written_no_ink_past_any_edge[presented-field] - AC-13(b) as written: left-edge glyph overhang (report A2), awaiting a ruling
XPASS …[presented-neutral], …[read-neutral], …[read-field]
10 passed, 1 xfailed, 3 xpassed
```

A second run of each tool gave the same file byte for byte.

### AC-15 · Core purity · PASS

```
$ pytest -v tests/acceptance/m2/test_ac15_core_purity.py tests/acceptance/m2/test_import_boundary.py
test_ac15_core_purity.py::test_lint_with_a_brief_on_a_specimen_loads_neither_pptx_nor_pypdfium2[swiss-specimen-presented-neutral] PASSED
test_ac15_core_purity.py::…[swiss-specimen-presented-night] PASSED
test_ac15_core_purity.py::…[swiss-specimen-read-field] PASSED
test_import_boundary.py::test_the_lint_core_imports_no_pen_render_or_rasterizer PASSED
test_import_boundary.py::test_keyline_lint_with_a_brief_loads_neither_pptx_nor_pypdfium2 PASSED
```

- Each test runs `keyline lint --brief` in a fresh interpreter. It exits 0, and neither
  `pptx` nor `pypdfium2` is in `sys.modules`.
- `test_pen_skeleton.py::test_lint_core_still_never_imports_the_pen` and
  `test_only_the_writer_imports_python_pptx` keep the pen's side of the boundary.

### AC-8 · Deck vs brief, on a pen-built deck (B-3) · PASS

```
$ keyline check fixtures/briefs/drift-pen/base.pptx --brief fixtures/briefs/drift/base.brief.toml -o $SCRATCH/ac8p
validate: passed
0 findings: 0 error, 0 warning, 0 advisory
…
exit 0
$ keyline lint fixtures/briefs/drift-pen/<drift>.pptx --brief fixtures/briefs/drift/base.brief.toml --json
drift-headline: [(3, 'brief-headline', 'warning')]
drift-slide-count: [(0, 'brief-slide-count', 'error')]
drift-unsourced: [(3, 'unsourced-number', 'warning')]
drift-source-missing: [(4, 'source-missing', 'warning')]
drift-undisclosed: [(0, 'fiction-undisclosed', 'warning')]
drift-role: [(2, 'brief-role', 'warning')]
$ pytest -q tests/acceptance/m2/test_ac08_drift_pen.py
9 passed
```

- `fixtures/briefs/src/build_drift_pen.py` writes the base with `Deck.from_brief` from
  the A1 brief, then re-applies A1's six drift functions (`build_drift.DRIFTS`) to it.
- A test checks that the pen base has the A1 base's layouts and texts, slide by slide.
  Another checks that a rebuild is byte-identical to the committed decks.
- The findings are exactly those of A1.

### M1 baseline, the import boundary and the README

```
$ python tools/m1_baseline.py
baseline: no differences
```

- It prints the same after every A2 task.
- The README gains "The pen": what it takes, `DoesNotFit`, the `pen` extra, and an
  example.
  - The example runs from the repository root, and its deck passes `check --brief`.
  - `test_readme_pen_example.py` runs the example as written.
- CHANGELOG records A2.

## The three contact sheets (G-1)

Rendered by `keyline check … --brief … -o …` with LibreOffice 26.8.0.3 at 1280 px, from
the committed decks:

- [`evidence/g1/swiss-specimen-presented-neutral-contact.png`](evidence/g1/swiss-specimen-presented-neutral-contact.png)
- [`evidence/g1/swiss-specimen-presented-night-contact.png`](evidence/g1/swiss-specimen-presented-night-contact.png)
- [`evidence/g1/swiss-specimen-read-field-contact.png`](evidence/g1/swiss-specimen-read-field-contact.png)

What to look at:

- **The section slide inverts the deck.** It uses the ink surface: dark in `neutral`
  and `field`, light in `night`.
- **The highlighted bar** of the type-size chart is the one accent on its slide: red,
  amber or blue by voice.
- **The grid picture** on slide 7 is cropped to the content area, so its left edge
  lines up with the text column.
- **`read-field`'s type is small on a projected contact sheet,** by design. Read mode
  is set for reading on a screen, and the lede is 16 pt.

## The script-coverage limit (audit 04)

- **The gap.** Caladea 1.001, the twin for Cambria, lacks 88 of the 134 Vietnamese
  letters. The other five twins lack none. Each fit table records its twin's gaps, and
  `tests/unit/test_fit_tables.py` checks them.
- **The warning.** When a deck's text uses letters its voice's twin lacks, the pen
  prints one warning per deck on save. The build goes ahead, and the warning is not a
  registry entry (the registry still has 35).

```
$ python -c "…Deck(pack='swiss', mode='read', voice='cambria.toml'), two slides of Vietnamese…"
keyline pen: warning: Caladea (for Cambria) lacks: ảờưữởạợồơủừ; LibreOffice renders them in a fallback font, so the check render is not faithful
$ pytest -q tests/acceptance/m2/test_pen_coverage_warning.py
3 passed
```

- **Carried to Phase B.** `tasks.md`'s Phase B outline puts the limit in
  `references/check.md` (since `ef05c36`) and, with this report, in the voice step
  (B-8.15):
  - for a subject whose text is Vietnamese, the skill does not pick Cambria;
  - when the pen's coverage warning appears, the skill changes the voice's font rather
    than accepting the check render.

## Findings

1. **A presented statement or close slide cannot hold a figure.**
   - The pack allows `figure` on both roles in presented mode. But their `main` region is
     23 rows, and a presented figure needs 24: 21 rows for the 120 pt numeral (144.03 pt
     pitch at 7.09 pt a row) and one 16.83 pt label line.
   - So `figure()` there always raises `DoesNotFit`, which names both parts. Read mode
     fits: the figure needs 13 rows there.
   - One more row (`main = { row = 34, rows = 24 }`) would end at row 58, where the
     footer starts, so the regions would touch without overlapping. Q-48.
2. **The estimator re-read the config for every width** (fixed in `4e74905`).
   - `load_table` parsed `thresholds.toml` before it looked in its cache. So each
     `width()` call cost one TOML parse, and a pen verb on a long read-mode text took
     about 0.1 s.
   - A profile of the stress planner put 97% of its time there. With the fix and
     coarser steps in the planner, planning went from about 430 s to 3 s.
   - `tests/unit/test_fit.py::test_a_long_fit_reads_the_config_once` fails without the
     fix.
3. **Glyph overhang at the left edge** (AC-13(b) above). Nothing in keyline measures it:
   the lint rules compare boxes, and the estimator measures advances.
4. **Stand-in engine tests needed a `sleep` binary** (fixed in `e4a2f26`).
   - The FX-3 timeout test and FX-11's stand-in tests failed when run with an empty PATH.
     They were written in the A1 fix rounds, and CI (which has `sleep`) stayed green.
   - They now skip by name without `sleep`, and still run wherever it exists.

## Tasks and commits (A2)

| task | commits |
|---|---|
| T-20 · B-7 measurement; audit 04; B-21 | `2c3dbf3`, `cf567ee`, `e93fa4a`, `ef05c36` |
| T-21 · fit tables | `452a480` |
| T-22 · estimator, AC-13(a) | `384c695`; the coverage warning's pen-level test `ad17fa9` |
| T-23 · pen skeleton | `c204ee2` |
| T-24 · text verbs | `8c0f946` |
| T-25 · figure | `3428126` |
| T-26 · table, chart_bar, image | `4508af4` |
| T-27 · determinism | `b411a92` |
| T-28 · specimens | `a30a754` |
| T-29 · AC-8 on the pen, AC-15 | `5cb9db7` |
| T-30 · fit stress | `4e74905`, `6ed849d` |
| T-31 · sweep, README, CHANGELOG | `658962c` |
| T-32 · this report | `e4a2f26` (sleep skips), `ad17fa9`, and the report's commit |

## Deviations (A2)

1. **Specimen names.**
   - Spec said: AC-12 and AC-15 name `swiss-specimen-presented.pptx` and
     `swiss-specimen-presented.brief.toml` (and a `read` specimen).
   - Implemented: three stems that name their voice. They are
     `swiss-specimen-presented-neutral`, `swiss-specimen-presented-night` and
     `swiss-specimen-read-field`.
   - Because: B-8.13 asks for presented in two voices, and audit 03 ruled Q-42 this way.
     AC-12 and AC-15 run on all three.
2. **Where the pen-built drift decks live.**
   - Spec said (T-29): the drift base is rebuilt with the pen.
   - Implemented: a second set, `fixtures/briefs/drift-pen/`, next to A1's
     `fixtures/briefs/drift/`.
   - Because: A1's test, report and two audits point at the A1 files. Both sets use the
     same brief and the same six drift functions.
3. **How AC-13(b) is measured.**
   - Spec said: a fit-stress deck, and no text ink outside its region by more than 2 px.
   - Implemented: four decks (mode × voice font) with each text on its own copy of its
     slide, and ink counted against an empty control copy at 26 of 255.
   - Because: some region boxes are only one grid row apart (`main` ends at row 57, the
     footer starts at 58), so on a shared slide a stray pixel could belong to either.
   - Charts are not stressed: their text is laid out by the chart engine, not the
     estimator. The corpus is Latin; B-21's measurement already covered Vietnamese
     wrapping.
4. **AC-13(b)'s test.**
   - Spec said: one criterion, every edge.
   - Implemented: a test that must pass for the estimator's edges (right, top, bottom),
     and a non-strict expected failure for every edge.
   - Because: as written it fails at the left edge for a reason outside the estimator,
     and the suite should stay green while Tyler rules (Q-47). The report states the
     FAIL.
5. **What "the committed specimen equals a fresh build" compares.**
   - Spec said: AC-11 asks for two builds to be byte-identical, which holds.
   - Implemented: the extra check against the committed decks compares XML parts byte
     for byte and the picture by pixels, and skips the embedded workbook.
   - Because: Pillow (zlib) and XlsxWriter set those bytes, and neither is pinned. On
     this machine all three committed decks are byte-identical to a fresh build.
6. **T-30's first commit claimed too much.**
   - `4e74905`'s tool said table and chart text are not fit-checked. For tables that is
     wrong, and figures are checked too.
   - `6ed849d` extended the stress to both, and the extension exposed the left-edge
     failure.

## Open questions (A2)

- **Q-47 · AC-13(b)'s left edge.** Options:
  - **(a) Amend AC-13(b)** to judge the right, top and bottom edges, the ones the
    estimator decides. Record left-edge glyph overhang as a known limit in
    `references/check.md`.
  - **(b) Keep the AC and move the text.** The pen would inset each text box by its
    style's worst negative side bearing. That breaks the flush-left line the grid, the
    keyline rule and the headlines share.
  - **(c) Keep the AC with a left-edge allowance** taken from each twin's side bearings.
    That needs `lsb` in the fit tables.
  - **Recommendation: (a).** Overhanging "v", "w" and "j" is ordinary typesetting, and
    PowerPoint draws it the same way.
- **Q-48 · a figure on a presented statement or close** (Finding 1). Options:
  - **(a)** give both `main` regions 24 rows;
  - **(b)** drop `figure` from those roles' presented components, so the pen refuses
    with a `PenError` that names the role;
  - **(c)** a smaller presented numeral;
  - **(d)** keep it, and document that it raises `DoesNotFit`.
  - (a) changes `pack.toml` and both presented templates. A1's template tests would see
    the change.
- **Q-49 · the `unsupported-content` advisory's wording.** It still says "in M1" on
  every table. §3 keeps the advisory, but the wording is now dated. Should it change,
  keeping the rule id?

## G-1 (Tyler)

1. Review the three contact sheets above.
2. Open both presented and read templates (`src/keyline/packs/swiss/swiss-neutral-*.pptx`)
   and the three specimens (`fixtures/packs/*.pptx`) in PowerPoint. Note any repair
   prompt (B-6).
3. In the `night` specimen, add a new text box and type in it. Is the text readable
   (Q-33)?

The A2 audit can run in parallel with G-1.

---

# A2 fixes (audit 05)

- **Audit 05** ([audit-05-a2.md](audit-05-a2.md), verdict FIX): FX-16 … FX-23,
  amendments B-22 … B-24, and rulings on Q-47 … Q-49. Tyler accepts the rulings and added
  FX-24 (a vertical anchor per region). The repro scripts are in
  [`evidence/audit05-repros/`](evidence/audit05-repros/).
- **Branch:** `002-skill-pack`, from `9813345` (report A2) to `0b8802a`; this section's
  commit follows.
- **Status:** every fix is in, each with its tests, and each repro is a test in the repo's
  style (the ones that need LibreOffice skip without it).
  - AC-13(b) as amended by B-24 passes on LibreOffice 26.8.0.3 for all six portable
    families: 642 texts, none past a limit.
  - `tools/measure_lo.py` holds B-21's two criteria and B-22's two new ones on 26.8.0.3.
  - The M1 baseline shows no differences after every fix.
  - CI is green on every push except `352a750` (see *Process notes*).
- **Stop here for the auditor,** who re-runs `fit_stress` and `measure_lo` on 24.2.7.2
  (B-22 item 7, B-24). Phase B's tasks are written after that audit.

## Reproduce (A2 fixes)

```sh
python -m pip install -e '.[dev]'
pytest -q                          # 1111 passed here (LibreOffice, OfficeCLI, all six twins)
python tools/m1_baseline.py        # baseline: no differences
python tools/measure_lo.py OUT     # B-21 (a) (b) and B-22 (c) (d); needs LibreOffice
python tools/fit_stress.py         # AC-13(b) per B-24, six families; needs LibreOffice
```

Without the engines, the suite gives 1021 passed and 90 skipped, both on a CI-like PATH
and on an empty PATH.

## FX-16 · The estimator and the writer see the same text · `792902e`

- **The change:** `keyline/fit/text.py` holds one normalization (B-22 item 1): NFC, each
  run of Zs space separators except U+00A0, U+202F and U+2007 becomes one U+0020, and
  leading and trailing spaces are removed.
  - `fit.wrap` measures the normalized text, split at U+0020 only, so a no-break-joined
    run is one word.
  - The writer passes every `<a:t>`, the notes, the alt text and the chart categories
    through the same function.
- **Refused at the verb** as `PenError`, naming the code point (B-22 item 3):
  - every control, tab included;
  - B-17's line breaks;
  - U+FFFE, U+FFFF and lone surrogates;
  - U+00AD, U+200B, U+2060 and U+FEFF.

  `\n` separates paragraphs only in `text()` and `notes()` (item 2).
- **Tests:** `tests/acceptance/m2/test_fx16_normalization.py`, 99 passed. They cover the
  audit's headlines (tabs, `\n`, `\r`, U+2028, U+2029, NEL, space runs, leading spaces, an
  NBSP-joined run), every verb against six refused characters, `text()` with `\r\n`, and
  the written text equal to the normalized input for every verb.
- **LibreOffice** (`attack_dblspace.py`): text with two spaces after each full stop,
  filled to the pen's limit, 12 random decks per mode.
  - Before the fix, 3 of 12 presented decks and 6 of 12 read decks overflowed the region.
  - After the fix, none did. The test keeps four seeds, which include failing ones for
    both modes.

## FX-17 · No line break before closing punctuation · `fa6c30b`, `2b85812`

- **The change:** `fit.text.break_units` keeps a piece that starts with
  `) ] } , . : ; ! ? / % ‰ » ” ’` with the piece before it, even after a space (B-22
  item 4).
- **The audit's headlines** (`attack_uax14.py`'s search, seed 7, rerun with the wrap from
  before the fix):
  - All three are refused now: "headline needs 3 lines, region holds 2".
  - With the old wrap, LibreOffice 26.8 set one of them in 3 lines, 53 pt below the title
    region. The other two fit, because LibreOffice's own threshold is looser than the 0.99
    margin.
- **What LibreOffice does,** per character (`tools/measure_lo.py`, bold Arial 48 pt):
  - With room on the line for the space after the last word, it keeps
    `) ] } , . : ; ! ? /` with that word (UAX #14 LB13's classes) and breaks before
    `% ‰ » ” ’`.
  - Without that room, it breaks before all fifteen.

  The estimator's rule is exact for the ten and conservative for the five: fewer break
  points can only add lines to a greedy wrap.
- **A correction:** `fa6c30b`'s message says LibreOffice "keeps ) : ; ! / and breaks
  before the other ten". That is wrong. The split came from random cases that mixed the
  two conditions above. `18f80ba` and `2b85812` correct it.
- **Tests:** `test_fx17_line_breaks.py`, 10 passed. They check the break units; that no
  estimated line starts with one of the fifteen; the three refused headlines; and, in
  LibreOffice under both conditions, that it never sets more lines than the estimate and
  keeps the ten when the space fits.

## Measurements for FX-18 and FX-19 · `18f80ba`

`tools/measure_lo.py` gained three probes. They write `lang="en-US"` on their runs, as the
pen does, while B-21's probes are unchanged.

```
$ python tools/measure_lo.py specs/002-skill-pack/evidence/lo-26.8.0.3-measurements.txt
table cells: … rows = 1 line a row, rows2 = 2, br = 4 in one cell, LibreOffice 26.8.0.3 680(Build:3)
  Georgia          regular    24 1.10 rows   1.2695   31.6913  1.2004   33.5723    1.8810
  Georgia          regular    24 1.10 br     1.2695   31.6630  1.1994   33.5440    1.8810
  Arial            regular    13 1.00 rows   1.1499   15.6473  1.2036   15.6567    0.0094
fallback advances: 10 characters at 24 pt; estimate = max(twin's maximum advance, missing_glyph_em = 1.49)
  Arial            cjk    run     1.0479 em  …   Arial  cjk  mixed  1.4794 em
  Courier New      emoji  run     1.2454 em  …   Courier New  thai  run  0.5700 em
  widest fallback advance: 1.4805 em
verdict (amendment B-21):
  (a) no stress case wraps at 1/0.99 = 1.0101: 420 cases, 0 wrap: HOLDS
  (b) every pitch <= size x 1.2 x line spacing + 0.01 mm (0.0283 pt): 198 probes, smallest slack 0.0000 pt: HOLDS
verdict (amendment B-22):
  (c) every table line <= size x max(1.2, hhea) x line spacing + 0.01 mm, every row <= its lines + 0.01 mm: 180 probes, smallest slack 0.0093 pt: HOLDS
  (d) every fallback advance <= max(maximum advance, missing_glyph_em): 36 probes, widest 1.4805 em: HOLDS
exit 0
```

- **Table cells on 26.8.0.3 are set at 1.2 em for every twin,** Gelasio and Carlito
  included. The auditor's 24.2.7.2 used hhea. B-22 item 7 takes the larger, so the
  estimator uses max(1.2, hhea).
- **Each table row is one 0.01 mm unit taller than its lines,** including a two-line
  row. Hence the row allowance (Deviation A).
- **A CJK glyph between Latin letters costs 1.48 em;** in a run it costs 1.05 em.
  LibreOffice adds space where Asian text meets Latin. So `missing_glyph_em = 1.49`, the
  widest measurement rounded up, recorded in `thresholds.toml` with the version.
- A second run gave the same bytes.

## FX-18 · Table cells at max(1.2, hhea), and 0.01 mm more per row · `36a1bf6`

- **The fit tables** store each twin's `hhea_line_em`: Gelasio 1.26953125 and Carlito
  1.220703125; the other four are 1.15 or under.
- **The estimate:** `Setting.cell_pitch` is size × max(1.2, hhea) × line spacing +
  0.01 mm. A table row is its lines at that pitch, plus `ROW_ALLOWANCE_PT` (0.01 mm), plus
  the cell margins.
- **Tests:** `test_fx18_table_pitch.py`, 16 passed. They check the stored hhea values,
  `cell_pitch`, the row heights the pen writes, and (in LibreOffice) that the longest table
  the pen accepts stays in its region. That last check runs for all six families through
  test-only voices, in both modes (`attack_table2.py`).
- The specimens were rebuilt; only their table slide changed.

## FX-19 · A missing glyph counts as missing_glyph_em at least · `cfec9e0`

- **The change:** `Table.missing_advance` = max(the twin's maximum advance,
  `missing_glyph_em` × units per em).
- **Tests:** `test_fx19_missing_glyphs.py`, 14 passed.
  - In LibreOffice, the longest text the pen accepts stays in its region for the audit's
    cases: CJK and emoji in a Courier New voice; CJK, Thai and emoji headlines in Arial;
    CJK in Calibri and Georgia. It also holds for Latin and CJK alternating.
  - With the rule from before the fix, the Courier CJK case fails.

## FX-20 · Inputs checked at the verb; images read once; save() atomic and typed · `4e879a6`

- **Images:** `image()` reads the file once and keeps the bytes. It takes PNG, JPEG, GIF,
  BMP or TIFF, and refuses any other format Pillow opens, naming it.
- **`save()`:**
  - it checks `author`: text, no refused character, at most 255 characters;
  - it turns any writer failure into a `PenError`;
  - it writes to a temporary file beside the target that then replaces it, with the mode a
    new file gets.
- **Tests:** `test_fx20_inputs_and_save.py`, 45 passed; 10 of them fail on the pen from
  before this commit.
  - They include `attack_ctrl.py`'s seven characters in a headline, notes, text and a
    table, each refused at the verb.
  - They include `attack_img.py`'s formats and the file swapped after `image()`.
  - A missing directory and a failing writer both leave nothing behind.

## FX-21 · A style below the body minimum sets captions only · `352a750`, `9f63c65`

- **The change:** each paragraph in a style below the mode's `body_min_pt` has at most
  `caption_exempt_words` words, as lint exempts such paragraphs. Footer source and note
  lines stay exempt, as in lint.
- **Tests:** `test_fx21_legal_calls_lint_clean.py`, 8 passed.
  - A generated sweep covers every role × layout × region × allowed component × allowed
    style, in both modes and the three stock voices, linted with
    `--pack swiss --voice <voice>`.
  - It asserts no error-level finding (B-23's invariant) and no `body-too-small`.
  - It fails on the pen from before the fix.
- **A note on severity:** `body-too-small` is a *warning* in the registry; audit 05 called
  it error-level. B-23's invariant (no error-level finding) held even before the fix. The
  sweep is stricter.

## FX-22 and FX-23 · Refused verbs change nothing; footer, flags, next(), bullets · `e7c8f49`

- **Transactions:** every verb keeps the builder's state before it runs and puts it back
  if it raises. A refused headline in `add()` leaves the deck's coverage record as it was.
- **The footer region** takes only `source()` and `note()`.
- **Flags:** `accent` and `header` must be `bool`.
- **`next()`:** on a deck made from a brief, `next()` after an `add()` is a `PenError`.
- **Bullets:** `bullets_max` counts per slide.
- **One commit for both fixes,** because FX-23's bullet count is part of the state FX-22
  keeps.
- **Tests:** `test_fx22_fx23_state.py`, 19 passed; all 19 fail before the commit. They
  cover `attack_state.py` (b)–(e), `attack_next.py`, and ten refusals across every verb
  with the builder's state unchanged.

## Q-48 · The numeral box is one numeral line · `a7ae6c1`

- **The change:** `figure()` no longer rounds the numeral's box to whole grid rows. A
  presented statement or close now holds a figure: 144.03 + 16.83 = 160.86 pt in 163.0 pt.
- **The refusal** is tested on a region patched to 22 rows, and names both lines in
  points.
- **The fit stress** refuses no component at its shortest in any mode or family; its
  refusal test now asserts exactly that.
- The specimens were rebuilt; only their figure slide changed.

## FX-24 · A vertical anchor per region · `224ad9d` (with `4a992d9`)

- **The data:** `pack.toml` gives every region an anchor, `"t"` or `"b"`. The Swiss
  cover, evidence (both layouts) and close titles are `"b"`; everything else is `"t"`.
- **What gets written:** the pen writes each text box with its region's anchor, and the
  templates' placeholders carry the same.
- **Rebuilt from the new templates:** the neutral templates; the specimens; the A1 and
  pen-built drift decks (AC-8 unchanged: each drift gives exactly its one finding); the
  one-mode pack fixture; and the ten rule fixtures built on the Swiss template. The rule
  fixtures were rebuilt with `build_rules.py --only NAME` and only their layouts changed.
  The G-1 contact sheets are regenerated.
- **Tests:** `test_fx24_anchor.py`, 7 passed. They check the anchors, the anchor's
  schema, what the pen and the templates write, and (in LibreOffice) that a one-line
  evidence title sits on the bottom of its region with its descenders inside.
- **The descent room (`4a992d9`, see Deviation B).** Bottom anchoring exposed a gap in
  the estimator. LibreOffice sets a line's baseline 0.2 em above the line's bottom, and
  the twins' descenders reach further: Gelasio up to 0.294 em. So the estimator now keeps
  that much room under a region's last line. A bottom-anchored box also gets it as a
  bottom inset, so its descenders stay inside the region.

## Q-47 · AC-13(b) as amended by B-24 · `0b8802a`

```
$ python tools/fit_stress.py > specs/002-skill-pack/evidence/fit-stress-lo-26.8.0.3.txt
refused at the shortest (not built):
  none

642 texts, 0 without ink; per edge, the most outside:
  left   +2.7 px (presented Georgia, slide 16, keyline:statement title, left allowance 1.9 px)
  top    -2.3 px (read Georgia, slide 3, keyline:cover footer)
  right  +0.7 px (read Courier New, slide 38, keyline:evidence footer)
  bottom +0.7 px (presented Cambria, slide 24, keyline:evidence title)
closest to a limit: -1.0 px from it (presented Arial, slide 48, keyline:evidence:figure side, left)
past a limit: 0 text(s)
verdict, AC-13(b) as amended by B-24 (right, top, bottom at 2 px; left at 2 px + the left allowance): PASS
exit 0
```

- **Families:** all six portable families, each through a test-only voice with Swiss
  neutral's palette, in both modes.
- **The left allowance** is the most negative left side bearing among the text's
  characters × size. Caps styles are upper-cased and bullet markers included. It is read
  from the twin with fontTools, for each style the region uses.
- **The test:** `test_ac13b_fit_stress.py`, 38 passed. The xfail is gone; one test per
  (mode, family) asserts B-24, and a unit test checks the allowance.
- A second run of the tool gave the same bytes.

## Q-49

Kept as ruled. The advisory still reads "table text is not read in M1"; spec 004 changes
it.

## Process notes

- **A red push, `352a750` (FX-21).** Its suite run had one failure: a T-24 test that used
  a 14-word label, which FX-21 now refuses. I misread the run, because my chain was
  `pytest | tail -1 && git commit`, and `tail` returned 0. `9f63c65` fixed the test.
  Every chain since starts with `set -o pipefail`.
- **Invisible characters.** The tool I write files with turns `\uXXXX` escapes into the
  characters themselves. That had put literal U+200B, U+FEFF, U+3000, U+2060 and U+2028
  into `test_fx14_messages.py` (round 2). `0f8cc5a` escapes them. New sources build such
  characters with `chr()`, and are checked before each commit.

## Deviations (A2 fixes)

A. **A row allowance.**
   - Spec said: B-22 item 5 gives a table cell's line pitch.
   - Implemented: the same pitch per line, plus 0.01 mm per row.
   - Because: on 26.8.0.3 every row is one LibreOffice unit taller than its lines
     (`measure_lo`, criterion (c)).

B. **A descent room under the last line (`4a992d9`).**
   - Spec said: B-21's height test (lines × pitch + spacing).
   - Implemented: the same plus size × max(0, descent_em − 0.2). The twin's deepest
     descent (`descent_em`) is taken over Basic Latin, Latin-1, Latin Extended-A, the
     Vietnamese letters, digits and punctuation, and stored in the fit tables. A
     bottom-anchored box gets it as its bottom inset.
   - Because: B-24 judges the bottom edge at 2 px, and bottom-anchored titles put
     descenders up to +2.7 px past it (Gelasio at 48 pt).
   - A figure's numeral box takes no room, because its label box follows in the same
     region.

C. **Refused one-line separators in `text()` and `notes()`.**
   - Spec said: B-22 item 2 lets `\n` separate paragraphs in `text()` and `notes()`.
   - Implemented: `\n` separates paragraphs, and U+2028 and U+2029 are refused there too,
     as in one-line texts.
   - Because: a second paragraph separator would need its own estimate.

D. **FX-22 and FX-23 share one commit.** The reason is given in that section above.

E. **`missing_glyph_em` covers CJK between Latin letters (1.48 em).** A CJK run costs
   1.05 em, emoji 1.25 em and Thai 0.57 em, so the value is conservative for those.

## Open questions (A2 fixes)

- **Q-50 · `missing_glyph_em` as one value.** 1.49 em covers the widest case measured,
  CJK between Latin letters. Emoji, Thai and CJK runs are over-counted. Should the value
  split by script, or stay one number?
- **Q-51 · The descent set.** `descent_em` spans Latin-1 and Latin Extended-A. Its
  deepest glyph in Gelasio is a comma-below letter, at 0.294 em; English text descends at
  most 0.23 em. Should the set be narrower (Basic Latin and Vietnamese), or stay as is?

---

# A2 fixes, round 2 (audit 06)

- **Audit 06** ([audit-06-a2fix.md](audit-06-a2fix.md)): FX-16 … FX-24 accepted. A last,
  bounded fit round followed: FX-25 … FX-31 and amendment B-25 (the measured set). The
  rulings on Q-50 and Q-51 came with it. The repro scripts are in
  [`evidence/audit06-repros/`](evidence/audit06-repros/).
- **Ruling on Q-52** (Tyler, 2026-10-08, amendment B-26): FX-25's pack invariant failed for
  the numeral style only. Option (a) was chosen, with the numeral set derived from the
  invariant.
- **Branch:** `002-skill-pack`, from `1dd6216` (A2 fixes) to `d758589`; this section's
  commit follows.
- **Status:**
  - Every fix is in, each with its tests, and each repro is a test in the repo's style
    (the ones that need LibreOffice skip without it).
  - On LibreOffice 26.8.0.3, `fit_stress` passes (1177 texts, English and Vietnamese)
    and `measure_lo` holds criteria (a) to (e).
  - The M1 baseline shows no differences after every fix, and CI is green on every
    push.
  - Phase B's tasks are in [`tasks.md`](tasks.md) (T-33 … T-49), and its questions are in
    plan §9 (Q-53 … Q-59).
- **Stop here for one audit,** which covers the fixes and the Phase B tasks.

## Reproduce (round 2)

```sh
python -m pip install -e '.[dev]'
pytest -q                          # 1233 passed here (LibreOffice, OfficeCLI, all six twins)
python tools/m1_baseline.py        # baseline: no differences
python tools/measure_lo.py OUT     # B-21 (a) (b), B-22 and B-25 (c) (d) (e)
python tools/fit_stress.py         # AC-13(b) per B-24 and B-25
python tools/gen_fit_tables.py     # the fit tables and numerals.json, byte-identical
```

Without the engines, the suite gives 1119 passed and 114 skipped, both on a CI-like PATH
and on an empty PATH. The round's own test files:

```
$ pytest -q tests/acceptance/m2/test_{b25_measured_set,fx25_overhang,b26_numeral_set,fx26_kerning,fx27_opening_punctuation,fx28_fx31_cells,fx29_complex_scripts,fx30_series_and_invisible,ac13b_fit_stress,fx17_line_breaks}.py
170 passed in 509.92s (0:08:29)
```

## B-25 item 1 · The measured set, and one warning · `dce55ad`

- **The set.** `keyline.fit.text.MEASURED` has 922 characters:
  - the blocks are Basic Latin, Latin-1, Latin Extended-A and -B, Latin Extended
    Additional, General Punctuation and Currency Symbols;
  - it leaves out what B-22 refuses and unassigned code points.
- **The fit tables take three extents over it,** from each twin's outlines, rounded
  outward to whole font units:
  - `descent_em` (per Q-51, the descent room now uses this set);
  - `top_em` and `left_em`, for items 2 and 3.
- **The warning.** The pen prints one warning per deck. It names the letters of the set
  a twin lacks and every character outside the set, and says the pen promises nothing
  for them.
- **Rebuilt fixtures.** The descent room grew for some twins: Liberation Sans bold to
  0.25 em, Carlito to 0.258 em, Gelasio to 0.306 em. Bottom-anchored titles' insets
  moved, so these were rebuilt:
  - the templates, the specimens and the drift decks;
  - the ten rule fixtures on the Swiss template, by name, with layouts only changing.
- **Tests:** `test_b25_measured_set.py`, 15.

## FX-25 · Tall capitals: the top allowance, and the numeral set · `51fe28f`, `b6ef63a`

- **The top allowance (B-25 item 2, `51fe28f`).** AC-13(b)'s top edge allows size × (the
  highest glyph top among the text's characters − the first baseline), when positive.
  - **The first baseline** is `Setting.first_baseline`: size × (1.2 × line spacing −
    0.2 em).
  - **It matches the measurements.** `test_the_first_baseline_is_measured` reads the
    198 pitch probes of `measure_lo` on each version (the auditor's 24.2.7.2 file and
    ours). Each probe lies within 0.06 pt of the model, at 1.00 em (line spacing 1.0)
    and 1.12 em (1.1).
- **Vietnamese in the stress.** `fit_stress` gains a title-case Vietnamese corpus with
  stacked capitals (Ẩ, Ẳ, Ấ) opening many words.
  - It runs in the five families whose twin has every letter of the corpus. Caladea
    lacks 88 of them, and B-25 item 1 promises nothing there.
  - The report lists the family it skips.
- **The pack invariant (B-25 item 3)** failed for the numeral style only (Q-52):
  - at the top: Gelasio's Ẩ at 120 pt, 26.8 pt above the box against 7.1 pt free;
  - on the left: U+2044 in the side region, up to 22.1 pt against a 14.2 pt gutter.

  Every other style passes.
- **The numeral set (B-26, `b6ef63a`).**
  - **The data.** `tools/gen_fit_tables.py` writes `fit/tables/numerals.json`:
    - per measured character that a twin draws, its largest top and left reach over
      the twins, from the outlines, with the twins' versions and SHA-256;
    - per bundled pack, the excluded characters.
  - **The rule.** `keyline.fit.numerals.derive` excludes every character whose reach,
    at either mode's numeral size, is not smaller than the smallest free space above
    (7.09 pt) or beside (14.17 pt) a region that allows a figure.
  - **Swiss: 37 excluded.**
    - 33 capitals with stacked marks, at the top: ǕǗǙǛǞǠȪȬȰḔḖḮṌṎṐṒṤṦṸṺẤẨẪẮẰẲẴẾỂỄỐỔỖ;
    - Ɲ, Ȉ, ȉ and U+2044 FRACTION SLASH, at the left.
  - Lowercase Vietnamese stays: "12 tỷ ₫", "3 đồng" and "năm 2026" are numerals.
  - **The geometry.** `Pack.free_space` and `Pack.rule_box` hold the regions' gaps; the
    pen draws the rule from the same box. So a pack directory gets its own set,
    derived at run time from the reach data.
  - **The refusals.** The evidence loader refuses any other character in a `value`,
    under `keyline brief` and the pen alike, and so does `figure()` again. The message
    names the character and suggests the label:

    ```
    evidence file numerals.toml: evidence[1].value: contains U+1EA8 (LATIN CAPITAL LETTER A WITH CIRCUMFLEX AND HOOK ABOVE), which a numeral cannot hold: it reaches above the figure's region (B-26); put it in the label
    ```
- **Tests:**
  - **`test_fx25_overhang.py`, 9:**
    - the first baseline on both versions and the overhangs;
    - the free space;
    - the invariant in both modes, the numeral over the numeral set (6.9 pt top
      overhang against 7.09 pt);
    - in LibreOffice, the audit's titles and ledes (`t_top.py`, `t_top2.py`) in the
      five covering families, within the allowance + 1.5 pt.

    Without the allowance, Georgia's "Ẩn số" sits 13.4 pt above its box and the test
    fails.
  - **`test_b26_numeral_set.py`, 17:**
    - the committed list is re-derived from the reach and the pack;
    - the rebuild is byte-identical from the installed twins (it skips, naming them,
      where the twins differ);
    - the reach agrees with the tables;
    - the refusals, the Vietnamese numerals, the label and the verb's re-check;
    - a pack directory;
    - in LibreOffice, Ầ (the tallest kept, 6.86 pt) and ƒ (the leftmost kept, 11.1 pt)
      stay clear. Ầ ends 0.35 pt below the statement's title box.
  - **`test_ac13b_fit_stress.py`, 70:** both corpora, and the top allowance; the strict
    xfail is gone.

## FX-26 · Positive kerning widens the estimate · `98483bc`

- **The pairs.** The fit tables store the positive kerning pairs inside the measured
  set:
  - per pair, the largest positive x-advance adjustment of each GPOS pair lookup
    (formats 1 and 2, extension lookups included), summed over lookups;
  - the legacy `kern` table's value where it is larger.
- **Counts:** Carlito about 4,200 pairs; Caladea 139 (regular) and 660 (bold); the
  Liberation twins 2; Gelasio none.
- **The width.** `fit.width` adds the pairs between adjacent characters as set.
  Negative pairs stay ignored.
- **Tests:** `test_fx26_kerning.py`, 15.
  - Carlito V+ĩ is +130/2048 em and Caladea f+’ is +83/1000 em.
  - In LibreOffice, the longest "Vĩ Tĩ" texts (Calibri) and "staff’s" texts (Cambria)
    stay inside their regions, in both modes.

## FX-27 · No line break after opening punctuation · `f9c9453`

- **The rule.** A piece that ends in an opening punctuation mark joins the next piece,
  even across a space: UAX #14 class OP, which is category Ps plus ¡ and ¿.
- **The closers.** The fullwidth closers ！？，。」） join the no-break-before list.
- **LibreOffice 26.8.0.3, per character:**
  - with room for the space after an opener, it keeps the opener with the next word;
    without room, it leaves the opener at the line's end;
  - it never sets more lines than the estimate.
- **Tests:**
  - `test_fx27_opening_punctuation.py`, 3;
  - the fullwidth closers in `test_fx17_line_breaks.py`.

## FX-28 and FX-31 · Measured cell data, per version · `fa0e8c0`

- **`cell_line_allowance_mm` = 0.05.** It is the largest excess per table-cell line,
  rounded up to 0.01 mm:
  - 24.2.7.2: 0.0499 mm (the audit's file);
  - 26.8.0.3: 0.0167 mm.
- **`missing_line_em` = 1.52.** On 24.2.7.2, a cell line with a fallback glyph is set at
  max(1.2, the fallback font's hhea). The fallback fonts' hhea values are:
  - Noto Sans CJK, 1.448;
  - Noto Sans Thai, 1.511;
  - Noto Color Emoji, 1.172.

  26.8.0.3 sets such a line at 1.2.
- **Data.** Both values are in `thresholds.toml` with their versions.
- **`measure_lo`** gains criterion (e) and a fallback-cell probe.
- **Tests:** `test_fx28_fx31_cells.py`, 7.
  - The allowance covers both versions' measurements.
  - In LibreOffice, the longest CJK, Thai and mixed tables stay in their region.
- **See Deviation J:** the fallback pitch applies per row.

## FX-29 · Complex scripts in the voice's family · `9c31d5c`

- **The fonts.** The theme's `cs` fonts are the voice's display and text families. Every
  run and template style names `+mj-cs` / `+mn-cs`.
- **Why runs and styles too.** The theme alone did not move LibreOffice, which set
  Hebrew in FreeSans. Now Hebrew is set in the twin.
- **Rebuilt:** the templates, the specimens, the drift decks and the ten rule fixtures,
  by name.
- **Tests:** `test_fx29_complex_scripts.py`, 6.

## FX-30 · Chart series, and text with no visible character · `b74c0ae`

- **Series.** A series needs at least one pair, and every value must be finite and fit
  in a float.
  - The evidence loader checks this, and `chart_bar()` checks again, raising
    `PenError`.
  - Before, `nan`, `inf` and `[]` reached `save()`, and 10**400 raised a raw
    `OverflowError`.
- **Invisible text.** A headline, text, source or table cell with no visible character
  is refused. Empty cells stay allowed.
- **Tests:** `test_fx30_series_and_invisible.py`, 18 (`t_chart.py` and the audit's
  invisible-text cases).
- **See Deviation F.**

## Measurements on 26.8.0.3 · `d758589`

```
$ python tools/measure_lo.py specs/002-skill-pack/evidence/lo-26.8.0.3-measurements.txt
verdict (amendment B-21):
  (a) no stress case wraps at 1/0.99 = 1.0101: 420 cases, 0 wrap: HOLDS
  (b) every pitch <= size x 1.2 x line spacing + 0.01 mm (0.0283 pt): 198 probes, smallest slack 0.0000 pt: HOLDS
verdict (amendments B-22, B-25):
  (c) every table line <= size x max(1.2, hhea) x line spacing + 0.05 mm, every row <= its lines + 0.01 mm: 180 probes, smallest slack 0.1227 pt: HOLDS
  (d) every fallback advance <= max(maximum advance, missing_glyph_em): 36 probes, widest 1.4805 em: HOLDS
  (e) every cell line with fallback glyphs <= size x max(1.2, hhea, missing_line_em) + cell allowance: 72 probes, widest 1.2036 em: HOLDS
exit 0

$ python tools/fit_stress.py > specs/002-skill-pack/evidence/fit-stress-lo-26.8.0.3.txt
not stressed (the twin lacks letters of the corpus; B-25 item 1):
  Vietnamese: Cambria
refused at the shortest (not built):
  none
1177 texts, 0 without ink; per edge, the most outside:
  left   +2.7 px (presented Georgia English, slide 16, keyline:statement title, left allowance 1.9 px)
  top    +18.5 px (presented Georgia Vietnamese, slide 16, keyline:statement title, top allowance 17.9 px)
  right  +1.7 px (read Courier New Vietnamese, slide 63, keyline:evidence:figure footer)
  bottom +0.7 px (presented Cambria English, slide 24, keyline:evidence title)
closest to a limit: -0.3 px from it (read Courier New Vietnamese, slide 63, keyline:evidence:figure footer, right)
past a limit: 0 text(s)
verdict, AC-13(b) as amended by B-24 and B-25 (right, bottom at 2 px; left and top at 2 px + their allowances): PASS
exit 0
```

- **`measure_lo`'s output** is byte-identical to the file committed with `fa0e8c0`.
- **`fit_stress`'s output** is byte-identical to a run made before B-26: its numerals
  are digits only, so the numeral set does not change it.

## Process notes (round 2)

- **The pack invariant waited for Tyler.** It failed for the numeral style, so it was
  committed as a strict xfail (`51fe28f`) and reported. B-26 replaced it with a passing
  test (`b6ef63a`).
- **A measuring trap (L-017).** pdfium's character box gives a composite glyph's stored
  bounds, not its outline: Gelasio Bold's Ầ is 0.46 pt too high at 120 pt. The B-26 edge
  test measures ink from a raster instead, comparing each slide with a control.

## Deviations (round 2)

F. **Default-ignorable characters count as invisible** (FX-30; accepted in advance).
   - Spec said (audit 06): a text needs a character of category L, M, N, P or S.
   - Implemented: the same, minus Unicode's default-ignorable letters and marks:
     variation selectors, the grapheme joiner, the Hangul fillers.
   - Because: VS16 is category Mn, so the stated test let through a case the finding
     lists as invisible.

G. **`fit_stress` tries every item again after any growth** (FX-25; accepted in
   advance).
   - Spec said: B-24's stress, each text at the longest length the pen accepts.
   - Implemented: `longest()` re-checks every item after any item grows.
   - Because: a grown item moves the words of the items after it. With the Vietnamese
     corpus, an item already marked full could take one more word.

H. **"Exceeds" is read as "is not smaller than"** (B-26).
   - Spec said: exclude the characters whose reach exceeds the smallest free space.
   - Implemented: exclude those whose reach is not smaller than it.
   - Because: B-25 item 3 requires every overhang to be smaller than the free space.
     No character falls exactly on the limit, so the list is the same either way.

I. **Every evidence value is checked as a numeral** (B-26).
   - Spec said: `keyline brief` refuses any other character in a figure's value.
   - Implemented: the evidence loader checks every entry's `value`, under
     `keyline brief` and the pen, and `figure()` checks again. `load_evidence` without
     a pack has no figure region to measure, so it does not check.
   - Because: a brief does not say which entries become figures, and any `value` can.

J. **Missing glyphs in a cell: per row, not per line** (FX-31, B-25 item 6).
   - Spec said: a line that contains a missing glyph uses `missing_line_em`.
   - Implemented: when any cell of a row has a glyph its twin lacks, every line of that
     row uses `missing_line_em`.
   - Because: a row is as tall as its tallest cell, and the estimator does not track
     which wrapped line holds the glyph. This is conservative: it can only refuse more.

## Open questions (round 2)

- **None for the fixes.** Q-53 (U+2212 in a numeral, found with B-26) and the Phase B
  questions Q-54 … Q-59 are in plan §9, each with a proposal.

---

# Phase B prelude: B-27 (audit 07)

- **Audit 07** ([audit-07-b-plan.md](audit-07-b-plan.md)): fix round 2 accepted, with
  deviations F … J. Phase B is GO, with task changes. Four estimator fixes come first:
  FX-32 … FX-35, under amendment B-27. The repro scripts are in
  [`evidence/audit07-repros/`](evidence/audit07-repros/).
- **G-1 passed, and B-28** (Tyler, 2026-10-13): see *G-1* below.
- **Branch:** `002-skill-pack`, from `6ba6487` (round 2) to `53a579d`; this
  section's commit follows.
- **Status:**
  - The five B-27 items are in, each as its own commit with its tests. Each repro is a
    test (the ones that need LibreOffice skip without it).
  - **This machine's LibreOffice is now 26.8.1.1,** not 26.8.0.3 (Deviation K). On
    26.8.1.1, `measure_lo` holds criteria (a) to (f) and `fit_stress` passes (1177
    texts).
  - The M1 baseline shows no differences after every fix.
- **No stop here.** Phase B continues from T-33; the Phase B audit re-checks these fixes.
- **One request to the auditor:** run the new `tools/measure_lo.py` on 24.2.7.2 and send
  its output. It replaces the listed break sets for that version (see FX-33).

## Reproduce (prelude)

```sh
python -m pip install -e '.[dev]'
pytest -q                          # 1275 passed here (LibreOffice 26.8.1.1, OfficeCLI, all six twins)
python tools/m1_baseline.py        # baseline: no differences
python tools/measure_lo.py OUT     # criteria (a) to (f); needs LibreOffice
python tools/fit_stress.py         # AC-13(b) per B-24 and B-25; needs LibreOffice
python tools/gen_fit_tables.py     # the fit tables and numerals.json, byte-identical
python tools/gen_measured.py       # breaks.json and environments.json, from committed outputs
```

Without the engines, the suite gives 1154 passed and 121 skipped on an empty PATH, and
1190 passed and 85 skipped on a CI-like PATH (LibreOffice, OfficeCLI, pdftoppm and node
removed; `fc-match` kept).

## B-27 item 1 · U+2212 joins the measured set · `e6d3a77`

- **The set** has 923 characters. MINUS SIGN is the only Mathematical Operator in it; the
  pen still refuses the others in a numeral.
- **Regenerated:** the twin tables are byte-identical, because no extent and no positive
  kerning pair depends on it. `numerals.json` gains its reach.
- **The numeral set keeps it,** so "−0.4%" is a figure. The 37 excluded characters are
  unchanged.
- **Tests:** `test_b25_measured_set.py` (15) and `test_b26_numeral_set.py` (18).

## FX-32 · The last glyph's right reach · `2e4d38d`

- **The data.** Each fit table gains `right`: per glyph that draws past its advance, how
  far, from the outline, rounded outward. Caladea Bold "f" is 78/1000 em and Carlito Bold
  "ế" is 0.096 em, as the audit measured.
- **The width.** `fit.width` adds the reach of a line's last drawn glyph. A trailing
  joiner or variation selector draws nothing, so the glyph before it counts.
- **Before the fix,** Cambria "7,1 kf" at 120 pt ended 6.6 pt past the side region here
  (the audit: +7.7 px over the 2 px limit on 24.2). The pen now refuses that value.
- **Tests:** `test_fx32_right_reach.py`, 21. In LibreOffice (`f1_right.py`), the audit's
  six numerals, and the longest numeral the pen accepts before each one's tail, end
  within 2 px of the side region's right edge. With the reach removed, the test fails.

## FX-34 · Kerning across default-ignorable code points · `4cc267c`

- **The change.** `fit.width` looks its positive pairs up between the characters a
  shaper sees. A joiner between two characters no longer splits their pair.
- **LRM.** LibreOffice does split the pair at U+200E. Counting it there only adds width.
- **Tests:** `test_fx34_kerning_across_ignorables.py`, 6. In LibreOffice
  (`f3_ignorable.py`), the longest joined bodies and ledes in a Calibri voice stay in
  their region in both modes. Without the fix, the presented ZWNJ body leaves it.

## FX-33 · Measured break sets · `172903e`

- **The probe.** `tools/measure_lo.py` probes every non-letter character of the measured
  set that normalization keeps: 202 characters.
  - For each, it tests the space before it and the space after it.
  - The character stands alone (when it is drawn) and attached to a word.
  - Each is set with and without room for the space at the break.
  - It runs in every family whose twin has the character: 5,936 probes here, 150
    characters. The other 52 are in no twin.
- **26.8.1.1, measured:**
  - no break before, after a space (11): `) ] } , . : ; ! ? /` and U+2044;
  - no break after, before a space (7): `( [ {` and U+00A1, U+00BF, U+201A, U+201E;
  - it **does** break before a backslash, alone and attached. So the audit's finding is
    specific to 24.2.7.2.
- **The data.** `tools/gen_measured.py` reads the committed outputs and writes
  `fit/tables/breaks.json`: the sets per version, and their union, which `break_units`
  uses. It needs neither LibreOffice nor fonts.
- **Versions without the full probe** (26.8.0.3 and 24.2.7.2, whose outputs predate it)
  keep the lists of B-22 item 4 and B-25 item 5, plus what audit 07 found on 24.2.7.2:
  the backslash and U+2044. See Deviation L.
- **The union** is the old lists plus the backslash and U+2044.
- **A new criterion, (f),** in `measure_lo`: every character a version keeps must be in
  the committed sets. If it fails, the output names the missing characters and says to
  regenerate.
- **Tests:** `test_fx33_measured_breaks.py`, 8.
  - `breaks.json` is re-derived from the outputs.
  - The full probe's entry matches its output and covers every character.
  - The probe's outcome logic is tested on synthetic glyph positions.
  - In LibreOffice (`f2_backslash.py`), LaTeX-style text at the pen's limit stays in its
    region in Arial, Courier New and Calibri, in both modes. On 26.8.1.1 this passes with
    or without the fix; 24.2.7.2 is the version that needs it.
  - `test_fx17_line_breaks.py` (12) now checks only the line count for the backslash
    and U+2044, because their handling differs by version.

## FX-35 · `missing_*` over every environment · `73e577e`

- **`missing_line_em` = 1.59** (was 1.52). In the auditor's environment the Thai
  fallback font is Loma, at 1.5894 em; on Tyler's machine it is Noto Sans Thai, at
  1.511 em.
- **The data.** `gen_measured.py` writes `fit/tables/environments.json` from the same
  outputs. Per environment it records who ran it, the LibreOffice version, the platform,
  the fallback fonts and what was measured.
- **Three thresholds are derived,** each the largest over the environments, rounded up
  to 0.01: `missing_glyph_em` 1.49, `missing_line_em` 1.59, `cell_line_allowance_mm`
  0.05. `thresholds.toml` holds the same values and a test compares them.
- **Tests:** `test_fx35_environments.py`, 4. The fallback-font test in
  `test_fx28_fx31_cells.py` now says what to do on a machine with a taller fallback
  font.

## Measurements on 26.8.1.1 · `53a579d`

```
$ python tools/measure_lo.py specs/002-skill-pack/evidence/lo-26.8.1.1-measurements.txt
verdict (amendment B-21):
  (a) no stress case wraps at 1/0.99 = 1.0101: 420 cases, 0 wrap: HOLDS
  (b) every pitch <= size x 1.2 x line spacing + 0.01 mm (0.0283 pt): 198 probes, smallest slack 0.0000 pt: HOLDS
verdict (amendments B-22, B-25):
  (c) every table line <= size x max(1.2, hhea) x line spacing + 0.05 mm, every row <= its lines + 0.01 mm: 180 probes, smallest slack 0.1227 pt: HOLDS
  (d) every fallback advance <= max(maximum advance, missing_glyph_em): 36 probes, widest 1.4805 em: HOLDS
  (e) every cell line with fallback glyphs <= size x max(1.2, hhea, missing_line_em) + cell allowance: 72 probes, widest 1.2036 em: HOLDS
verdict (amendment B-27):
  (f) every character this version will not break before or after is in the estimator's sets: 11 before, 7 after: HOLDS
exit 0

$ python tools/fit_stress.py > specs/002-skill-pack/evidence/fit-stress-lo-26.8.1.1.txt
1177 texts, 0 without ink; per edge, the most outside:
  left   +2.7 px (presented Georgia English, slide 16, keyline:statement title, left allowance 1.9 px)
  top    +18.5 px (presented Georgia Vietnamese, slide 16, keyline:statement title, top allowance 17.9 px)
  right  +1.7 px (read Courier New Vietnamese, slide 63, keyline:evidence:figure footer)
  bottom +0.7 px (presented Cambria English, slide 24, keyline:evidence title)
closest to a limit: -0.3 px from it (read Courier New Vietnamese, slide 63, keyline:evidence:figure footer, right)
past a limit: 0 text(s)
verdict, AC-13(b) as amended by B-24 and B-25 (right, bottom at 2 px; left and top at 2 px + their allowances): PASS
exit 0
```

- The numbers equal 26.8.0.3's on every criterion and every edge.
- The 26.8.0.3 outputs stay committed, unchanged.
- The fit tables' `measured_on` gains 26.8.1.1.

## G-1 (Tyler, 2026-10-13) · passed

- **Where:** PowerPoint for the web.
- **Repair prompts:** none, in the two templates and the three specimens.
- **Verdict on Swiss:** readable, not yet "wow".
- **Fix items:** none.
- **The text box in `night`** (Q-33; Q-61, closed): "Tyler, 2026-10-13: text typed into
  a new text box is readable on night, and on the section slide."
- **B-28** follows from it, and is in `spec.md`, `plan.md` and `tasks.md` (`9856b27`):
  - the BonsaiHub demo stays in Phase B on the Swiss pack, as the end-to-end proof of
    the skill;
  - G-2 judges whether both decks are correct and tailored to their briefs;
  - the soul verdict moves to spec 003, and the Swiss demo decks are its baseline.

## Deviations (prelude)

K. **LibreOffice 26.8.1.1, not 26.8.0.3.**
   - Handoff said: re-run `measure_lo.py` and `fit_stress.py` on 26.8.0.3.
   - Implemented: both ran on 26.8.1.1, into new files; the 26.8.0.3 files are
     unchanged.
   - Because: the system updated LibreOffice on 2026-10-09 (`libreoffice-fresh`
     26.8.0-2 to 26.8.1-1), so 26.8.0.3 is no longer installed here. Every LibreOffice
     test in the suite now runs on 26.8.1.1.

L. **Versions without the full probe keep the listed break sets.**
   - Spec said (B-27 item 3): the sets are measured, as the union over the versions.
   - Implemented: 26.8.1.1's sets are measured. For 26.8.0.3 and 24.2.7.2, the data
     holds the earlier lists, plus the backslash and U+2044 for 24.2.7.2.
   - Because: their outputs predate the full probe, and 24.2.7.2 already differs from
     26.8.1.1 on the backslash. Dropping `% ‰ » ” ’` (never kept in any probe so far)
     before 24.2.7.2 has run the full probe could make the estimate too short there.
   - Effect: the estimator refuses a few breaks LibreOffice allows. That can only
     refuse more text.

M. **The probe's scope.**
   - Spec said: every non-letter character of the measured set, in both line
     conditions.
   - Implemented: that, at regular 48 pt between words of letters, alone and attached.
     52 characters are in no twin and are not probed.
   - Because: a probe needs the twin's advance to size its box.

N. **`right` covers every glyph of the twin,** not only the measured set. A line can end
   in any character, and the data costs little.

O. **Criterion (f) was not asked for.** It makes `measure_lo` fail when a version keeps
   a character the committed sets lack.

## Open questions (prelude)

- **Q-60 · The 26.8.0.3 entry.** That version can no longer be measured here, so its
  listed sets would stay for good. *Proposal:* once the auditor's 24.2.7.2 output is
  in, drop the 26.8.0.3 entry from `breaks.json`: 26.8.1.1 supersedes it on this machine.
- **Q-61 · G-1's text box in `night`.** B-28 says G-1 passed but does not state this
  check (Q-33). *Proposal:* Tyler confirms it in one line, and it is recorded here.

---

# Report B · the skill (in progress)

- **Phase:** B, tasks T-33 … T-49 of [`tasks.md`](tasks.md), as revised by audit 07 and
  B-28.
- **Branch:** `002-skill-pack`, from `b3e6ab1` (the B-27 prelude) to `d5c90f9`; this
  section's commit follows.
- **Status:**
  - **Done:** T-33 … T-45, T-48 and T-50. AC-17, AC-18, AC-19, AC-20 and AC-23 pass.
  - **Waiting for Tyler:** T-46 (the demo, in a fresh session) and T-47 (the surfaces).
    AC-21 passes for `product.toml`; its deck tests skip until the demo exists. AC-22 is
    manual.
  - **Then:** this report is completed (T-49), and G-2 follows.
- **A rehearsal** of the skill's loop on BonsaiHub, from the packaged zip, found four
  things to fix before the real demo. They are fixed; see *The rehearsal* below.

## Reproduce (Phase B)

```sh
python -m pip install -e '.[dev]'
pytest -q                          # 1347 passed, 11 skipped here (LibreOffice 26.8.1.1, OfficeCLI, all six twins)
python tools/gen_docs.py --check   # the skill's generated tables are current
python tools/build_skill.py        # dist/keyline.zip
python tools/ngram_overlap.py skill docs
```

The gate ran at `f793a0e`: 1343 passed and 11 skipped; 1222 passed and 132 skipped on an
empty PATH; 1258 passed and 96 skipped on a CI-like PATH. The M1 baseline shows no
differences. `d5c90f9` adds the demo tool's 4 tests, run in the same three ways. The 11
skips are AC-21's deck tests, which wait for the demo.

## AC-17 · SKILL.md · PASS

```
$ pytest -q tests/acceptance/m2/test_ac17_skill_md.py
9 passed
```

- **Frontmatter:** `name: keyline`, matching the folder and the name pattern; a
  185-character description; `license: Apache-2.0`; a 241-character compatibility line.
- **Body:** 128 lines of at most 200. No `${`, no `` !` ``, no absolute path.
- **Audit 07 §4.4:**
  - it says how to find the skill folder on each surface;
  - each of the 18 tokens `doctor` can print has an action;
  - without python-pptx and without network it routes to "check a deck" and says why;
  - the voice step is step 4 of the loop, a step of its own.

## AC-18 · Docs integrity · PASS

```
$ pytest -q tests/acceptance/m2/test_ac18_docs.py tests/acceptance/m2/test_gen_docs.py
34 passed
$ python tools/gen_docs.py --check; echo $?
0
```

- **Anchors:** every `<!-- rule:ID -->` resolves to a registry id.
- **`anti-tells.md`:** the 27 rows of Appendix A, plus `one-look-for-everything`. Every
  enforcement is valid: `rule:` and `brief:` ids are registry ids of the right kind,
  and `backlog:` ids are in §13 or B-8.16.
- **`pen.md`:** all 15 public verbs, each heading naming every parameter. Its example
  script is built by a test, and the result passes `check --brief`.
- **`check.md`:** 31 recipes, one per rule at warning or error level, each under its own
  heading; the pen's refusals; the known limits.
- **`brief.md`:** every field with its test. Its two examples load as a valid brief.
- **Generated tables** (`tools/gen_docs.py`, seven): the type scale, the budgets, the
  roles, the layouts, the title capacities, the numeral set's excluded characters and
  the per-twin coverage.
- **Line caps** (audit 07 §4.9): craft-floor 96 of 110, anti-tells 48 of 60, brief 207
  of 210, pen 204 of 220, check 264 of 290.

## AC-19 · Package · PASS

```
$ python tools/build_skill.py
dist/keyline.zip (955 KiB)
$ pytest -q tests/acceptance/m2/test_ac19_package.py
4 passed
```

- Two builds are byte-identical.
- One top folder, `keyline/`, with `SKILL.md`, `references/`, `scripts/`,
  `lib/keyline/`, `LICENSE` and `NOTICE`. `lib/keyline` equals `src/keyline` file for
  file, without caches.
- The zip is under 3 MB.

## AC-20 · Sandbox smoke · PASS

```
$ pytest -q -rP tests/acceptance/m2/test_ac20_sandbox.py
AC-20 sandbox: python-pptx, lxml, Pillow = 1.0.2 6.1.3 12.3.0
4 passed
```

- A fresh venv with only lxml, Pillow and python-pptx, pinned to 1.0.2 by
  `constraints.txt`. keyline is not installed there.
- The zip is unpacked outside the repository; `PYTHONPATH` is scrubbed.
- `kl.py doctor` exits 0 and prints "python-pptx 1.0.2".
- `kl.py run` imports keyline from the skill's `lib/`.
- The three specimens build from a copy of the `fixtures/packs/` layout, and
  `kl.py check` exits 0 on each with its brief.
- Without network the test skips locally and fails in CI.

## AC-21 · BonsaiHub · PASS (T-46 run 2)

```
$ pytest -q -rs tests/acceptance/m2/test_ac21_bonsaihub.py
12 passed
```

- **`product.toml` matches its hash:** PASS.
- **The deck checks** run on run 2's decks, collected into `examples/bonsaihub/`: every
  demo file is committed; both briefs pass `kl.py brief` and carry an inline voice; both
  decks pass `kl.py check --brief` with exit 0; two builds equal each other and the
  committed deck; the disclosure is present, and the slide counts are within §10 (11
  and 7). G-2a is recorded in "T-46 run 2" below.
- Before run 2, these checks skipped while no demo file existed (1 passed, 11 skipped).

### What Tyler runs for T-46

Run 1 followed these steps (see "T-46 run 1" below). Under B-29 item 4, run 2 runs
headless, under the protocol at the end of this report.

The decks must come from a fresh Claude Code session, in a folder outside this checkout
(audit 07 §4.7). `tools/demo.py` prepares that folder: the skill unpacked from the zip,
`product.toml` where the prompts expect it, and a venv with lxml, Pillow, python-pptx
1.0.2 and pypdfium2, without keyline.

```sh
# 1. in the keyline checkout
git pull
python tools/build_skill.py
python tools/demo.py setup ~/keyline-demo     # any empty folder outside the checkout

# 2. the fresh session
cd ~/keyline-demo && source .venv/bin/activate && claude
```

In that session:

1. Send **P-1** word for word (spec §10, with B-29 item 3's last sentence):

   > Use the keyline skill. Make the demo-day pitch deck for BonsaiHub from
   > examples/bonsaihub/product.toml (audience `demo-day`). It will be presented live.
   > Work in examples/bonsaihub/ and name the files pitch.brief.toml, build_pitch.py and
   > pitch.pptx. Put the render in render/pitch/. Pass author="Tyler" when saving. If you
   > need numbers that product.toml lacks, put them in pitch.evidence.toml with a
   > source. Never edit product.toml. Keep it to 8 to 12 slides.

2. When the skill shows the spine, approve it or ask for changes. That approval is
   **G-2a** for the pitch.
3. Send **P-2**, which is P-1 with the spec's substitutions and B-29 item 3's range:

   > Use the keyline skill. Make the Q4 pre-read for the BonsaiHub team from
   > examples/bonsaihub/product.toml (audience `team-preread`). They will read it on
   > their own. Work in examples/bonsaihub/ and name the files preread.brief.toml,
   > build_preread.py and preread.pptx. Put the render in render/preread/. Pass
   > author="Tyler" when saving. If you need numbers that product.toml lacks, put them
   > in preread.evidence.toml with a source. Never edit product.toml. Keep it to 4 to 8
   > slides.

4. Approve its spine: **G-2a** for the pre-read.

Then, back in the checkout:

```sh
python tools/demo.py record ~/keyline-demo    # paste its output into this session
```

This session then copies the outputs into `examples/bonsaihub/` with
`tools/demo.py collect`, records G-2a and the hashes here, and runs AC-21. It builds
none of the files and edits none (plan Q-58 as ruled).

## AC-22 · Surfaces · (b) Claude Code PASS; (a) claude.ai waits for Tyler; (c) not run

P-3 is: "Use the keyline skill to make a 6-slide deck for BonsaiHub's demo day from this
file. It will be presented live."

- **(a) claude.ai:** upload `dist/keyline.zip` under Customize → Skills, attach
  `examples/bonsaihub/product.toml`, send P-3.
- **(b) Claude Code:** unzip `dist/keyline.zip` into your skills folder, start a session
  in an empty folder that holds `product.toml`, send P-3.
- **(c) Claude desktop:** optional.

For each, record the `doctor` output, whether a preview was rendered, the last `check`
exit code, and the deck. Read the deck's slide text for a name before it is committed
(audit 07 §4.8): the agent on claude.ai knows the account holder's name. The decks go
under `examples/bonsaihub/surfaces/`.

### (b) Claude Code · PASS (T-47, 2026-10-31, headless)

Run under the headless protocol (B-29 item 4), from `0356e58` with `dist/keyline.zip`
`bf40df0f…b9c6ce`, in `~/keyline-p3` (`demo.py setup`). The checks before setup were
the same as run 2's, with the same results. Deviations U and V apply.

- **The prompt:** P-3, then "The file is examples/bonsaihub/product.toml." in place of an
  attachment:

  > Use the keyline skill to make a 6-slide deck for BonsaiHub's demo day from this
  > file. It will be presented live. The file is examples/bonsaihub/product.toml.

- **One session for both turns:** `646487bd-cae9-456b-abf7-c008537cdc7a`, model
  `claude-opus-5-5`, permission mode `acceptEdits`, the keyline skill listed. Each turn
  exited 0 with an empty stderr.

  | Turn | Input, verbatim | Log in `~/keyline-p3-logs/` | SHA-256 | Time | It ended |
  |---|---|---|---|---|---|
  | 1 | the prompt above | `turn1-p3.jsonl` | `1dfd9393c4bc539b50bf50012114030db3bfbc4a0a046823d7e60746c2788769` | 2 min 30 s | at the spine (6 slides), with no deck |
  | 2 | Tyler's reply, below | `turn2-reply1.jsonl` | `46d2ef953fd8fc8cdda8fbffe102781413d406e09209df7bc1b9098947ce649c` | 54 s | with the deck built and `check` exit 0 |

- **The spine went to Tyler verbatim.** Its slide 5 put the 41-day median wait beside
  slide 3's "a match takes a season". Tyler's reply, passed back word for word:
  > Approved, with one change: take the 41-day median wait off slide 5, because it
  > contradicts slide 3's "a match takes a season". Keep 71% and 0.4%, and make the
  > headline say that keepers who wait stay, not that the wait is why.

  The session changed slide 5's headline to "Keepers who wait for a match stay",
  removed the 41 days from the slide and its notes, and changed the brief's thesis to
  match. Then it built. An approval with a change is an approval, so it did not show
  the spine again.
- **`doctor`** (turn 1, `kl.py doctor`), every line OK: `PYTHON_OK` 3.11.16, `LXML_OK`
  6.1.3, `PILLOW_OK` 13.0.0, `PPTX_OK` 1.0.2, `RENDER_LIBREOFFICE`, `RASTER_PDFIUM`,
  `VALIDATE_OFFICECLI`, and `FONT_OK` for the six portable families, each resolved to its
  twin.
- **The preview** was rendered with LibreOffice 26.8.1.1 and rasterized with pypdfium2:
  six slides and a contact sheet. OfficeCLI validated the schema.
- **The last `check`:** exit 0, 0 findings. Run here on the committed copy, it also exits 0.
- **The deck:** `examples/bonsaihub/surfaces/claude-code/bonsaihub_demo_day.pptx`, SHA-256
  `e78974116e5c12528c06c30da5e68ec78f138979eedbb10fcba8bc7210fdbcee`.
  - 6 slides, presented mode, the Swiss pack, and a voice drawn from bonsai materials:
    Georgia and Arial, a deadwood-grey ground, stoneware text, copper rules and a moss
    accent.
  - The disclosure is on the cover; the creator and last-modified-by are empty.
  - Its slide text and notes, read before the commit, name no one.
  - Only the deck is committed, as AC-22 asks. The session's brief, build script and
    preview are in the record below.
- **The record:**

  ```
  $ python tools/demo.py record ~/keyline-p3      # the home folder is shortened to ~ here
  - working directory: `~/keyline-p3`
  - skill: `~/keyline-p3/.claude/skills/keyline`
  - `dist/keyline.zip` SHA-256: `bf40df0f55858a0c998bbb405249382b97f0748fa0cb917b60c2688da3b9c6ce`
  - `keyline` imports from: `~/keyline-p3/.claude/skills/keyline/lib/keyline/__init__.py`
  - files the session wrote:
    - `bonsaihub_demo_day/bonsaihub_demo_day.brief.toml` `dc799c4eab3ca7fd5c2bcac015f1d9aecab9eacde23845fccef8dbedacef5e00`
    - `bonsaihub_demo_day/bonsaihub_demo_day.pptx` `e78974116e5c12528c06c30da5e68ec78f138979eedbb10fcba8bc7210fdbcee`
    - `bonsaihub_demo_day/build_bonsaihub_demo_day.py` `b0cb3a0a12750875e7c5877247ceb4e936d578f9d77b0326b8d96851e7efaf22`
    - `bonsaihub_demo_day/preview/contact.png` `3b0a8af422ce36b24c9e9df1bc81434c72b6b10d867c9d24056f02c5be23cfa4`
    - `bonsaihub_demo_day/preview/slide-01.png` `6207dca9e7f9341988b76d06e5a2b01ffb2c2dc458a31ff6ea944a725bcf585b`
    - `bonsaihub_demo_day/preview/slide-02.png` `f64edb19f7b9b384bc9d914be2c1c8f52550737314de53c847ae3d9dcc2db10a`
    - `bonsaihub_demo_day/preview/slide-03.png` `575387011d798675fbac34dbde85b9315b15418f8a4b0c65dee5a1499f288f68`
    - `bonsaihub_demo_day/preview/slide-04.png` `edb10f07ecd936537624420bd37b69e4cc8663b098fa11089aa09d2ece89709c`
    - `bonsaihub_demo_day/preview/slide-05.png` `55c0a948a64e8237893f46ce5ed4666b67f7520032e5f5a977fe140390e89975`
    - `bonsaihub_demo_day/preview/slide-06.png` `8877031abea575c842229209f6e84526c9bac5b1e76adda07a4fabbd2ffdd523`
  ```

### (a) claude.ai · waits for Tyler

Tyler runs it (upload `dist/keyline.zip`, attach `product.toml`, send P-3). His result
is recorded here when he sends it.

## AC-23 · Hygiene and CI · PASS

```
$ pytest -q tests/acceptance/test_ac12_hygiene.py tests/acceptance/m2/test_ngram_overlap.py
11 passed
$ python tools/ngram_overlap.py skill docs
14 shared sequences of 8 words between skill and docs
```

- **Identity:** commit authors and trailers follow D-014.
- **Decks keyline ships or shows** (under `examples/`, `skill/` and the bundled packs)
  have a creator and a lastModifiedBy from an allow-list.
- **Text under `skill/` and `examples/`** has no other e-mail address or handle.
- **`NOTICE`** carries every fit table's source.
- **No copied text.** The skill's docs were written from the spec, `docs/research.md`
  and keyline's own code. I did not open the anthropics/skills repository or any other
  skill's text while writing them. `tools/ngram_overlap.py` is there for the auditor to
  run against a clone. Run on `skill/` and `docs/`, it finds only the three research
  headings `anti-tells.md` cites.
- **CI** runs on 3.11 and 3.13 with the font packages, ruff, `gen_docs.py --check` and
  the suite.

## The rehearsal

Before handing T-46 to Tyler, I ran the skill's loop myself on BonsaiHub, from
`dist/keyline.zip` unpacked in a scratch folder, to find problems first. Its files are
not committed and are not the demo.

- **Result:** a 10-slide pitch and a 5-slide pre-read, each with an inline voice drawn
  from `[product.world]`. Both pass `kl.py brief` and `kl.py check --brief` with exit 0.
- **Found and fixed:**
  1. **A headline inside the word limit can be too wide for its title.** Two of ten
     were refused at build, after the spine would have been approved. `SKILL.md` now
     checks headlines against their titles before it shows the spine (`f793a0e`).
  2. **The refusal did not say which slide.** `next()` now names it (`66b7af5`).
  3. **The refusal sat under a 20-line traceback.** `kl.py run` now prints one line
     with the script's line (`66b7af5`).
  4. **Nothing said how much a title holds.** `brief.md` has a generated table: a
     presented cover or close title holds 2 lines of 18 to 25 characters (`f793a0e`).
- **Not fixed, a question:** see Q-62.

## Deviations (Phase B)

P. **`next()` and `kl.py run` changed after the rehearsal.**
   - Spec said: §6.1 and §8.1 do not describe how a refusal is worded.
   - Implemented: `next()` prefixes a refused headline with its slide, and `kl.py run`
     prints a keyline refusal as one line.
   - Because: the skill has to know which headline to shorten.

Q. **T-35 and T-39 share `brief.md`.** T-35 committed its voice section; T-39 added the
   rest around it.

R. **A seventh generated table, `titles`.** Q-57 as ruled lists the type scale, the
   budgets, the numeral characters and the coverage. `roles`, `layouts` and `titles`
   are added, because the docs would otherwise restate pack data by hand.

S. **`tools/demo.py`** is not in the tasks. It sets up the folder for the fresh session
   and prints the record audit 07 §4.7 asks for, so the demo's setup is one command.

T. **`ruff.toml` excludes the demo's build scripts** (`examples/bonsaihub/build_*.py`).
   - Spec said: CI runs `ruff check .` and `ruff format --check .` over the repository.
   - Implemented: the two scripts run 2's fresh session wrote are excluded, as the
     auditor's evidence already is.
   - Because: they have lines over 100 characters, and T-46 forbids editing them. Their
     hashes are recorded, and any edit needs a fresh-session re-run.

U. **P-3 on the Claude Code surface names the file.**
   - Spec said: AC-22 attaches `product.toml` and sends P-3.
   - Implemented: P-3 followed by "The file is examples/bonsaihub/product.toml.".
   - Because: a headless Claude Code session has no attachment; the auditor asked for
     this sentence in its place.

V. **The skill sits in the run's folder, not in `~/.claude/skills/`.**
   - Spec said: AC-22 (b) installs the skill into `~/.claude/skills/`.
   - Implemented: `demo.py setup` unpacks it into `~/keyline-p3/.claude/skills/keyline`,
     a project skill.
   - Because: the protocol requires that no keyline skill is in `~/.claude/skills`, so
     that the run sees only the zip under test. Claude Code loads project skills the same
     way: the session's init event lists `keyline`.

## Open questions (Phase B)

- **Q-62 · `brief` cannot tell that a headline will not fit.** It counts words; only the
  pen measures. Today the skill runs a build skeleton to find out. *Proposal:* in spec
  003, `keyline brief` runs the fit on each headline and reports a finding, which adds
  a registry entry. **Ruled at the checkpoint below: accepted, deferred to spec 003.**
- **Q-60 and Q-61** (from the prelude) are ruled at the checkpoint below.
- **For G-2 (Tyler judges both; the auditor's notes at `0356e58`):**
  - **Pre-read slide 5** says "We have 3,180 active keepers: almost four waiting trees
    for each one." That is a number derived in prose (12,400 / 3,180 = 3.9; the
    arithmetic is right) with no evidence entry.
  - **Pitch slide 7** says "Ninety days is about one season." It equates the 90-day
    retention window with a season.
  - Both touch the fixture's known inconsistency (a "full season of visits" against a
    41-day median wait), which Tyler ruled on for the Claude Code surface deck: no 41
    days beside "a season".

## Checkpoint (the auditor, at `3566cb4`) · accepted

The auditor re-ran the Phase B work on LibreOffice 24.2.7.2 and accepted it. T-46 and
T-47 go ahead from the head that holds this section.

- **The auditor's results:**
  - ruff clean;
  - the Phase B acceptance subset: 74 passed, 11 skipped;
  - `gen_docs.py --check` passes, and the M1 baseline is unchanged;
  - `measure_lo.py` holds criteria (a) to (f);
  - `ngram_overlap.py` against a fresh clone of anthropics/skills finds 0 shared
    sequences (its positive control finds 441);
  - a dry run of `demo.py setup` works, and the packaged `kl.py doctor` exits 0;
  - P-1 and P-2 as written above match spec §10.
- **Q-60, accepted.** The auditor's 24.2.7.2 output with the full probe is committed as
  [`evidence/lo-24.2.7.2-measurements.txt`](evidence/lo-24.2.7.2-measurements.txt).
  `breaks.json` is regenerated from it:

  ```
  $ python tools/gen_measured.py      # rewrites breaks.json and environments.json
  $ grep "^  no break" specs/002-skill-pack/evidence/lo-26.8.1.1-measurements.txt
    no break before (11): U+0021 U+0029 U+002C U+002E U+002F U+003A U+003B U+003F U+005D U+007D U+2044
    no break after (7): U+0028 U+005B U+007B U+00A1 U+00BF U+201A U+201E
  $ grep "^  no break" specs/002-skill-pack/evidence/lo-24.2.7.2-measurements.txt
    no break before (12): U+0021 U+0029 U+002C U+002E U+002F U+003A U+003B U+003F U+005C U+005D U+007D U+2044
    no break after (7): U+0028 U+005B U+007B U+00A1 U+00BF U+201A U+201E
  ```

  `breaks.json` holds each pair and their union: 12 characters before, 7 after.
  `test_fx33_measured_breaks.py` re-derives it.

  - The 24.2.7.2 entry is now measured. It differs from 26.8.1.1 by one character: it
    keeps the backslash with the word before.
  - The 26.8.0.3 entry is dropped; its output predates the full probe.
  - The union loses U+0025, U+00BB, U+2019, U+201D and U+2030 (before) and U+2045
    (after). Both full probes break at the first five, so the estimator does too.
    U+2045 was not probed: no twin has it. FX-36 below corrects this.
  - Deviation L no longer applies: no version keeps a listed set.
  - `environments.json` takes the auditor's environment from the same new output. The
    three thresholds are unchanged (1.49, 1.59, 0.05).
- **Checked on 26.8.1.1 after the change:**

  ```
  $ pytest -q tests/acceptance/m2/test_fx33_measured_breaks.py tests/acceptance/m2/test_fx17_line_breaks.py tests/acceptance/m2/test_fx27_opening_punctuation.py tests/acceptance/m2/test_fx35_environments.py
  28 passed
  $ python tools/measure_lo.py OUT; echo $?      # byte-identical to lo-26.8.1.1-measurements.txt
  0
  $ python tools/fit_stress.py > OUT; echo $?    # byte-identical to fit-stress-lo-26.8.1.1.txt
  0
  ```

  The gate with this change: 1348 passed and 11 skipped on the full suite; 1227 passed
  and 132 skipped on an empty PATH; 1263 passed and 96 skipped on a CI-like PATH. The M1
  baseline shows no differences, and `gen_docs.py --check` passes.
- **Q-61, closed.** Tyler's line is recorded under *G-1* above.
- **Q-62, accepted and deferred to spec 003:** `keyline brief` will run the fit on each
  headline, with a new registry entry. Until then, the skill's step 5 runs the headline
  dry-run.
- **`dist/keyline.zip` changes,** because `breaks.json` ships in it. T-46 builds the zip
  from this head.

## FX-36 · The characters no twin has · checkpoint at `f523a1a`

The auditor accepted `f523a1a` (re-run on 24.2.7.2: the evidence file byte-identical,
both tables regenerated byte-identically, `tests/acceptance/m2` 887 passed and 14
skipped, and `dist/keyline.zip` the same bytes, `619eee58…ea22a`). It found one gap,
FX-36 (low). The repro is in [`evidence/fx36-repros/`](evidence/fx36-repros/).

- **The gap.** B-27 item 3 says `measure_lo.py` probes every non-letter character of the
  measured set. It skipped the 52 that no twin has. Probed in fonts that have them, on
  24.2.7.2, U+2045 is kept with the word after and U+2046 with the word before, as
  ( and ) are. The estimator broke at both, so it could count one line fewer than
  LibreOffice sets: FX-33's mechanism.
- **The fix.** A character no twin has is probed in an installed font that has it.
  `fallback_fonts` asks `fc-list ':charset=<hex>'` and checks the face fontconfig picks.
  It takes the family with the most of the characters left first, ties by name. The
  output names the font. A character no installed font has is listed as not probed.
- **26.8.1.1, re-run:**

  ```
  $ python tools/measure_lo.py specs/002-skill-pack/evidence/lo-26.8.1.1-measurements.txt; echo $?
    no break before (12): U+0021 U+0029 U+002C U+002E U+002F U+003A U+003B U+003F U+005D U+007D U+2044 U+2046
    no break after (8): U+0028 U+005B U+007B U+00A1 U+00BF U+201A U+201E U+2045
    no twin has these; probed in Noto Sans (52): U+2023 U+2024 … U+20C0    (abbreviated here)
    probed: 202 characters in 6320 probes; in no installed font, not probed (0):
    (f) every character this version will not break before or after is in the estimator's sets: 12 before, 8 after: HOLDS
  0
  ```

  - Here Noto Sans has all 52, U+20C0 included. U+20C0 breaks.
  - No character stays unprobed on every version, so there is no Q-63. U+20C0 had no font
    only in the auditor's environment.
- **The union** gains U+2046 (no break before) and U+2045 (no break after).
  `breaks.json` is regenerated, and a second run of `measure_lo.py` gives the same sets.
- **The 24.2.7.2 entry** still comes from the output that predates FX-36. The auditor
  re-runs it at the Phase B audit.
- **Tests:**
  - `test_fx36_unprobed.py`, 4: the font choice; the committed output; the estimator;
    and in LibreOffice, `probe_unprobed.py`'s probe on U+2045, U+2046, U+203B and
    U+2042, with ( and ) as controls.
  - `test_fx33_measured_breaks.py` now requires every character to be probed on some
    version, except those no installed font has.
  - `test_fx27`'s check on U+2045 flips: it opens. `test_fx17` checks only the line count
    for U+2046, which its headline's twin lacks.
- **Q-60's line in `plan.md`** is corrected: U+2045 was not probed, not measured as
  breaking.

## Checkpoint (the auditor, at `432ca4a`) · FX-36 accepted

- **The auditor's results:** `test_fx36`, `test_fx33` and `test_fx27` re-run on 24.2.7.2,
  17 passed. Its rebuild of `dist/keyline.zip` at `432ca4a` has the SHA-256
  `1cb44f99…a4c452c1`, which is the zip of the demo's run 1. The full re-check is part
  of the Phase B audit.
- **CI failed at `432ca4a`,** on both Pythons, in one test:

  ```
  E       AssertionError: assert (27 == 52)
  tests/acceptance/m2/test_fx36_unprobed.py:59: AssertionError
  1 failed, 1253 passed, 110 skipped
  ```

  - **Cause:** the runner's fontconfig resolves the portable families to other fonts,
    which have more of the characters, so only 27 fall outside them. The 52 are the
    characters the twins lack. My CI-like PATH run hides programs, not fonts, so it
    passed here.
  - **Fix (`9816baf`):** the test skips unless every portable family resolves to its
    twin. The check is split out of `_lo.unready` as `_lo.untwinned`. With a stand-in
    `fc-match` that answers DejaVu Sans, as on the runner:

    ```
    SKIPPED [1] tests/acceptance/m2/test_fx36_unprobed.py:56: the twins: Arial resolves to DejaVu Sans, not its twin Liberation Sans
    ```

## T-46 run 1 · recorded, not collected (B-29 item 1)

Tyler ran the demo on 2026-10-15, in a fresh interactive session in `~/keyline-demo`, with
the zip built at `432ca4a`. The transcript stays outside the repository, because it holds
local paths. The model it names is `claude-opus-5-5`.

```
$ python tools/demo.py record ~/keyline-demo      # the home folder is shortened to ~ here
- working directory: `~/keyline-demo`
- skill: `~/keyline-demo/.claude/skills/keyline`
- `dist/keyline.zip` SHA-256: `1cb44f994f4ba483914d22d1d7c456716c832b85244e4c6abcccc2a8a4c452c1`
- `keyline` imports from: `~/keyline-demo/.claude/skills/keyline/lib/keyline/__init__.py`
- files the session wrote:
  - `examples/bonsaihub/build_pitch.py` `e5125632475fe9eccad1ca6e77505e9ba3563e01f3eae8fb331ba5de376ed804`
  - `examples/bonsaihub/build_preread.py` `17046d7c2ad89c4a81899201d6f02daaf69286c454c52a88f3b6f3e575e5c0f4`
  - `examples/bonsaihub/pitch.brief.toml` `e5e65933a6b95ab0c686645169b5cec16c106fc10c0cfd5c537957ecfe5df29b`
  - `examples/bonsaihub/pitch.pptx` `e08151018d42e8524afaf038ae656e78b872d41f298f145485446028407c3090`
  - `examples/bonsaihub/preread.brief.toml` `c69d8fc61e1ae5914f8d61ab5cc8295cafde8eacca0df51660a57d8c620544ba`
  - `examples/bonsaihub/preread.evidence.toml` `29a4f2d2ac742031dd9a342c47da7d29049add46017054047dafd6c85b85577d`
  - `examples/bonsaihub/preread.pptx` `72373ab59a86f25b883271003ef2eb005d5295b635444ebf547a3d8677610bf8`
  - `examples/bonsaihub/render/pitch/contact.png` `091624fbf5abef0b2f6f8e225852c5be7d2ba50c600e95b3bd159dd81e43e2b4`
  - `examples/bonsaihub/render/pitch/slide-01.png` `2a968ffffe555f3458f52e954586bb1c7b728b74528562f8513845ddadd9e44f`
  - `examples/bonsaihub/render/pitch/slide-02.png` `545b91b9f3458c1f17a78f683d3469a59ce9d29ad1198ee06d3a8f5640791415`
  - `examples/bonsaihub/render/pitch/slide-03.png` `20fca2fd2e43893bc894dd5759ccbd31c278281d2db4bfc5d92ffc20324fadec`
  - `examples/bonsaihub/render/pitch/slide-04.png` `c114ef722d8f7f9d21cf554849dbcb4d3cb8307080026dec56dd8399d6adc23c`
  - `examples/bonsaihub/render/pitch/slide-05.png` `d0685bc4e854823fced7e34d9f8e403bb6f35fb9e1a9e4c22136b757ccead3d6`
  - `examples/bonsaihub/render/pitch/slide-06.png` `7d4f42c67581ec2497c04141b77333557e82bc4c6490273808a779ffdaf7f5f8`
  - `examples/bonsaihub/render/pitch/slide-07.png` `f1f45525f9e111bd228775ed9d6c0308280fd8f5dd8dadeb2b423a059b190488`
  - `examples/bonsaihub/render/pitch/slide-08.png` `07c3eaccddf704640078173c951fbc23e484f8719a19a786ac84ff1579464457`
  - `examples/bonsaihub/render/pitch/slide-09.png` `9165aacf95ef078e039cce617cd8d3d1fadbb00cf7986bbba534305bcb70800f`
  - `examples/bonsaihub/render/pitch/slide-10.png` `392a474df365677694fb20147d77e23f24f7d2a553a823323724fefac0a5b6fb`
  - `examples/bonsaihub/render/preread/contact.png` `4a44cdf7e002396b89db57c5ea35e240920b41fc9df4857b4c45e4f5c041d0d9`
  - `examples/bonsaihub/render/preread/slide-01.png` `3c82700128c91e0bf0c4311a7568e7c95f888b5bbabcc7f51a510afcc2d08f5f`
  - `examples/bonsaihub/render/preread/slide-02.png` `edb65a842ee879199004897cbef382358aa6816253fac2b82625ff91ca1e8c0f`
  - `examples/bonsaihub/render/preread/slide-03.png` `dd4a7367c3102180fa125557e4ff62b7ebac187945054bae7c71d8f67bea5004`
  - `examples/bonsaihub/render/preread/slide-04.png` `ea3849c68be725e2c488c34ea1a02b1570019b419f9c94f626418a4b49da0675`
  - `examples/bonsaihub/render/preread/slide-05.png` `a8620e4204bbd33ffcc9e84492e5632582a3623d4f8df625498ce5a8b07f808e`
  - `examples/bonsaihub/render/preread/slide-06.png` `6d5256ef8ec738c1ca1f786089ec2f1358a40953e37c01bd578e9c9d7243bd84`
  - `examples/bonsaihub/render/preread/slide-07.png` `b7479fa6f602fb2495e73da68ec5a893016ff769d479cb910ab4711ac4137926`
  - `examples/bonsaihub/render/preread/slide-08.png` `5ec1a05e4041d85ba1f7b95185e74b81604187a7290ed6771f2ab3b0f275eedf`
  - `examples/bonsaihub/render/preread/slide-09.png` `710711200a0d82088ca3c42e08960425f67458522df15c22278d928fc755b9e7`
```

I re-hashed the 28 files in `~/keyline-demo`; all match the record.

- **Not collected.** The auditor found two failures in the transcript:
  1. **G-2a did not happen.** In both decks the session went on to build without
     stopping at the spine:
     - the pitch: "Spine passes both checks. The request was complete as given, so I'm
       going ahead without stopping for spine approval. Building the slides now."
     - the pre-read: "Both checks pass. I'm going ahead without stopping for spine
       approval, as with the pitch."

     `SKILL.md` step 6 ("If the user is present, wait … If they are not, go on") let it
     decide that. Spec §10 says Tyler approves each spine before the build. FX-37 fixes
     the step (B-29 item 2).
  2. **AC-21 would fail.** `preread.pptx` has 9 slides; §10 says 4 to 8. P-2 never
     stated the range. B-29 item 3 adds it to each prompt.
- **Left as it is.** `~/keyline-demo` is unchanged, and none of its files is committed.
- **A known inconsistency in the fixture.**
  - `product.toml` says Slow Match unlocks "only after a full season of visits", but
    its `days_to_first_match` is 41 days.
  - The auditor confirms it is an error in the fixture, not a planted test.
    `product.toml` stays frozen (§10: its hash).
  - Run 1 handled it as constitution VI asks. It left the file unchanged and named the
    conflict in the pre-read's slide 7 headline: "Open question: the median match
    arrives in 41 days, before a full season of visits".

## FX-37 · The approval step stops for the user (B-29 item 2) · `fe60fd9`

- **`SKILL.md` step 6** now reads:

  > 6. **Approval.** Show the user the spine, then stop: end your turn and wait for
  >    their reply. Build only after they approve it. Skip this stop only when the user
  >    has told you, in this conversation, not to wait; then say in the report that the
  >    spine was not approved.

- **The test:** `test_ac17_skill_md.py::test_the_approval_step_stops_for_the_user`
  compares the step's text. With the old step restored, it fails:

  ```
  $ pytest -q tests/acceptance/m2/test_ac17_skill_md.py
  10 passed
  $ git stash -- skill/keyline/SKILL.md && pytest -q tests/acceptance/m2/test_ac17_skill_md.py; git stash pop
  1 failed, 9 passed
  ```

- **P-1 and P-2** in "What Tyler runs for T-46" end with B-29 item 3's sentence: "Keep it
  to 8 to 12 slides." and "Keep it to 4 to 8 slides."
- **`dist/keyline.zip`** was rebuilt from the FX-37 tree, before the move:

  ```
  $ python tools/build_skill.py && sha256sum dist/keyline.zip
  1ec25c6bedd1de3cad0a04c9cbc3eac47044448a731a09e36d847bcb51d2db4c  dist/keyline.zip
  ```

  A second build gave the same bytes. The move changed the zip; run 2 uses the zip at
  `fe60fd9` (see "The move to tyler-void" below).

## T-46 run 2 and T-47's Claude Code surface · the headless protocol (B-29 item 4)

This session runs the fresh session as a subprocess, `claude -p`. G-2a stays Tyler's.

1. **Setup.** Run `python tools/demo.py setup ~/keyline-demo-2`. Before it, check:
   - `PYTHONPATH` is empty;
   - neither `~/.claude/skills` nor `~/.claude/CLAUDE.md` holds keyline.
2. **The environment.**
   - The subprocess starts in `~/keyline-demo-2`, with its `.venv/bin` first on PATH.
   - It does not inherit this session's `CLAUDE*` variables (`CLAUDECODE`, the session
     id, `CLAUDE_CODE_CHILD_SESSION`, `CLAUDE_EFFORT` and the rest). They would mark it
     as this session's child, so they are removed with `env -u`. The rest of the
     environment is the user's.
3. **Each turn** runs this command:

   ```sh
   claude -p "<P-1, verbatim>" --output-format stream-json --verbose \
     --permission-mode acceptEdits --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Skill" \
     --disallowedTools "AskUserQuestion,WebFetch,WebSearch"
   ```

   - The flag names were checked with `claude --help`, on Claude Code 2.1.295.
   - The command uses no `--bare`, `--append-system-prompt`, `--system-prompt` or
     `--model`.
   - P-1 and P-2 are those above, as B-29 item 3 words them.
4. **Logs.** Each turn's stream goes to `~/keyline-demo-2-logs/`, outside the demo
   folder. The report records each file's SHA-256 and the model named in its
   `system`/`init` event.
5. **The spine stop.**
   - When a turn ends with the spine, this session stops and shows Tyler the spine
     exactly as the subprocess printed it, then waits.
   - Tyler's reply goes back verbatim, with the same flags, from the same folder:
     `claude -p "<Tyler's reply>" --resume <session_id>`.
   - This session never approves for him, and adds no words to a prompt or a reply.
6. **Failure.** If a turn builds a deck without stopping at its spine, run 2 has
   failed. This session stops and reports; it does not retry on its own.
7. **P-2** goes into the same session with `--resume`, as in run 1, with the same spine
   stop.
8. **Hands off.** This session writes, edits and runs nothing in `~/keyline-demo-2`
   except `tools/demo.py`.
9. **Afterwards:**
   - run `demo.py record` and show the output to Tyler;
   - run `demo.py collect`;
   - record G-2a here, with Tyler's verbatim replies and the hashes;
   - run AC-21 and the gate;
   - commit "docs: BonsaiHub demo (fresh session, run 2)".

**T-47, the Claude Code surface,** follows the same protocol in `~/keyline-p3`
(`demo.py setup`). It uses P-3 plus the sentence "The file is
examples/bonsaihub/product.toml.", in place of an attachment. That is a deviation, and
it is recorded with the run. claude.ai stays with Tyler.

## The move to tyler-void (2026-10-26)

The repository moved to `tyler-void/keyline`. Every commit was rewritten to D-014's
identity, `Tyler <code@tyler-void.dev>`, so every hash changed.

- **The hashes in this report** and the other docs written before the move no longer
  resolve.
  - [`docs/commit-map.md`](../../docs/commit-map.md) maps each cited hash to its commit
    now: 115 rows, and one hash (`4b991fa`, in spec 001's report) undetermined.
  - The CI runs cited before the move belonged to the old repository and are not in the
    new one.
- **FX-37 landed in the snapshot,** "Snapshot of the working tree before the move", not in
  a commit of its own. The snapshot was `322e706`; it is now `fe60fd9` (next item).
- **Five files that stay untracked** were committed with the snapshot:
  `HANDOFF-A1fix2.md`, `audit05.zip`, `audit06.zip`, `audit07.zip` and
  `fx36-repros.zip`. The three audit zips hold the old work e-mail.
  - On the auditor's instruction (2026-10-29), the snapshot is amended without them,
    `322e706` → `fe60fd9`, and the branch is force-pushed. No commit on `002-skill-pack`
    holds them now. The local copies stay, listed in `.git/info/exclude`.
  - An earlier push of this commit, `2f2b3d8`, had removed them at the tip only, which
    left them in the public history. It is replaced by this one, with the same tree
    except for this text.
  - **The check:** a scan of every blob and every commit reachable from the new head,
    with zip and pptx members, PDF streams and PNG text chunks unpacked, finds neither
    the old work e-mail nor the old handle. On the old head, the same scan finds the
    e-mail in the three audit notes inside the zips, and nothing else:

    ```
    old head (2f2b3d8): 1281 blobs and 182 commits scanned; 3 hits
      audit05.zip!audit-05-a2.md, audit06.zip!audit-06-a2fix.md, audit07.zip!audit-07-b-plan.md
    new head:           1276 blobs and 182 commits scanned; 0 hits
    ```

    The scan script stays outside the repository, because it holds the patterns.
  - `322e706` stays readable on GitHub by its hash until GitHub collects it, for example
    from the page of the CI run that tested it.
- **`dist/keyline.zip` changed with the move.** `keyline/NOTICE` in it now names
  tyler-void:

  ```
  $ git switch 002-skill-pack && python tools/build_skill.py && sha256sum dist/keyline.zip
  bf40df0f55858a0c998bbb405249382b97f0748fa0cb917b60c2688da3b9c6ce  dist/keyline.zip
  ```

  Run 2 uses the zip built at its head.
- **The gate at `322e706`,** whose tree is `fe60fd9`'s plus the five files, on
  LibreOffice 26.8.1.1:

  ```
  $ pytest -q                                   1354 passed, 11 skipped
  $ env PATH= python -m pytest -q               1231 passed, 134 skipped
  $ env PATH=<CI-like> python -m pytest -q      1268 passed, 97 skipped
  $ python tools/m1_baseline.py                 baseline: no differences
  $ python tools/gen_docs.py --check            exit 0
  ```

  CI passed on `322e706`.
- **Q-63** (ruled at the checkpoint below): D-014 says "There is no history rewrite and
  no repo recreation". The move did both. *Proposal:* a new decision records the move,
  the rewrite, and `docs/commit-map.md` as the key to the hashes cited before it.
  `decisions.md` is append-only, so D-014 stays as written (plan, §9).

## Checkpoint (the auditor, at `322e706`) · status agreed

The auditor agrees with the status table at `322e706`. Its items, in its order:

1. **Privacy.** The audit zips the snapshot committed hold the old work e-mail. The
   snapshot is amended without them and the branch force-pushed (see "The move to
   tyler-void" above, which has the scan).
   - The auditor's steps assumed origin at `322e706`. It was at `2f2b3d8`, which had
     removed the files at the tip only. So `2f2b3d8` was re-applied on the amended
     snapshot, and the lease was `002-skill-pack:2f2b3d8`.
2. **Q-63: accepted.** D-021 in `docs/decisions.md` records the move. D-014 is not
   edited again.
3. **Tyler's verdict on the look** is recorded below, as input for spec 003. B-28 stands:
   run 2 goes ahead, headless, under the protocol above, and the Swiss pack does not
   change.
4. **A reference study for spec 003** (`docs/reference-study.md`), research only, done
   during run 2's spine waits or after it.
5. **For the Phase B round, not now:** two failures that depend on the environment,
   seen on the auditor's LibreOffice 24.2.
   - `test_fixture_repro` compares PNG bytes, which differ under zlib-ng. It should
     compare decoded pixels.
   - `test_fx17` asserts the glyph order for U+2046, a character no twin has, set in a
     fallback font. It should skip that assertion for `NO_TWIN` and keep the line count.

## Tyler's verdict on the look (2026-10-29) · input for spec 003

> also the current keyline style looks bad :)
> looks like boomer word 2003 era :)

It came after Tyler saw run 1's pitch. That deck is not committed; its contact sheet is
`render/pitch/contact.png` in run 1's record (SHA-256 `091624fb…`).

My reading of that contact sheet, offered as the causes spec 003 has to close:

1. **The fonts.** A heavy Georgia-like serif for headlines over an Arial-like sans, the
   Office pairing of the early 2000s. Fonts are not embedded, so a voice can only use
   families with installed metric twins (D-020's `portable_fonts`), in practice the
   Office core fonts. This is the largest single cause.
2. **One slide, ten times.** Headline top left, a rule under it, one big number, a
   short paragraph to its right, and the same flat grey ground on every slide. No dark
   slide, no full-bleed slide, no change of pace.
3. **The rule under each title** reads as Word's heading with a bottom border.
4. **The lower half of most slides is empty.** The content hugs the top.
5. **The chart** looks like a spreadsheet default: gridlines, grey bars, one in colour.
6. **No pictures,** in a deck about bonsai trees.

B-28 already places the look in spec 003. In spec 002, G-2 judges correctness, and the
Swiss demo decks are kept as spec 003's baseline.

## T-46 run 2 · collected, G-2a recorded (2026-10-30)

Run 2 followed the headless protocol above (B-29 item 4), from `b30dff4`.

- **Before setup:** `PYTHONPATH` empty; no `~/.claude/CLAUDE.md`; no folder or `SKILL.md`
  named keyline under `~/.claude/skills`.
- **Setup:** `python tools/demo.py setup ~/keyline-demo-2`, with `dist/keyline.zip`
  `bf40df0f…b9c6ce` built at `b30dff4`.
- **Each turn:** `claude -p` (Claude Code 2.1.295) with the protocol's flags, started in
  `~/keyline-demo-2` with its `.venv/bin` first on PATH. These variables of this session
  were removed: `CLAUDECODE`, `CLAUDE_CODE_CHILD_SESSION`, `CLAUDE_CODE_ENTRYPOINT`,
  `CLAUDE_CODE_EXECPATH`, `CLAUDE_CODE_MESSAGING_SOCKET`, `CLAUDE_CODE_MESSAGING_TOKEN`,
  `CLAUDE_CODE_SESSION_ATTENDED`, `CLAUDE_CODE_SESSION_ID`, `CLAUDE_EFFORT` and
  `CLAUDE_PID`. `VIRTUAL_ENV` pointed at the demo's venv, as `source .venv/bin/activate`
  does in run 1.
- **One session for all four turns:** `dfe1a98b-82d5-4723-8f20-1617010669a7`. Every
  `system`/`init` event names the model `claude-opus-5-5`, the folder `~/keyline-demo-2`
  and the permission mode `acceptEdits`, and lists the `keyline` skill. Each turn exited
  0 with an empty stderr.

| Turn | Input, verbatim | Log in `~/keyline-demo-2-logs/` | SHA-256 | Time | It ended |
|---|---|---|---|---|---|
| 1 | P-1 (above) | `turn1-p1.jsonl` | `3f774e1af5fffca942103c15501b55252ac4bd4ff1dc94d35fc2ec53cd13a3ad` | 3 min 38 s | at the pitch's spine, with no deck |
| 2 | "approved, build it as is" | `turn2-reply1.jsonl` | `bdb7bd0083bfe6998bdf6fd22f18344c7045be7c86866698288ad8317e298794` | 1 min 27 s | with `pitch.pptx` built and `check` exit 0 |
| 3 | P-2 (above) | `turn3-p2.jsonl` | `e7dd445200430078826cd6bac751d11e58f91d5ab7e4c01ab535c0368290a02e` | 1 min 29 s | at the pre-read's spine, with no deck |
| 4 | "approved, build it as is" | `turn4-reply2.jsonl` | `ce980f8d03bd278de020dde9e49fd3cc1805d81f121401d74e43bdffa5afc66e` | 1 min 13 s | with `preread.pptx` built and `check` exit 0 |

The logs stay outside the repository, because they hold local paths.

### G-2a

Each spine went to Tyler exactly as the session printed it, and each reply went back
word for word.

- **The pitch** (2026-10-30, after turn 1): 11 slides, `kl.py brief` 0 findings, every
  headline fits its title. Direction: angel investors at demo day; the decision, a second
  meeting about the $1.2M seed round; the thesis, that a season-long wait is why
  adoptions last; the motif, a visit. Voice: Georgia and Calibri, stoneware grey,
  pruning-shear black, copper-wire rules, moss accent.
  - **Tyler:** "approved, build it as is"
- **The pre-read** (2026-10-30, after turn 3): 7 slides, `kl.py brief` 0 findings, every
  headline fits its title. Direction: the BonsaiHub team, reading alone before the Q4
  meeting; the decision, Slow Match in Da Lat and Kyoto before any new feature; the
  motif, a season. The pitch's voice.
  - **Tyler:** "approved, build it as is"
- **The approved headlines are the committed briefs' headlines,** slide for slide
  (`examples/bonsaihub/pitch.brief.toml`, `preread.brief.toml`).
- **What the session raised at each spine,** and left open after the build:
  - the fixture's inconsistency (a "full season of visits" against a 41-day median
    wait). The session left the 41 days out of both decks;
  - Seasonal Boost has a price but no description;
  - the pre-read's retention claim is a correlation, since `product.toml` has no
    comparison without Slow Match;
  - the Hub has no number.

### The record

```
$ python tools/demo.py record ~/keyline-demo-2      # the home folder is shortened to ~ here
- working directory: `~/keyline-demo-2`
- skill: `~/keyline-demo-2/.claude/skills/keyline`
- `dist/keyline.zip` SHA-256: `bf40df0f55858a0c998bbb405249382b97f0748fa0cb917b60c2688da3b9c6ce`
- `keyline` imports from: `~/keyline-demo-2/.claude/skills/keyline/lib/keyline/__init__.py`
- files the session wrote:
  - `examples/bonsaihub/build_pitch.py` `2d03d0a0fd21af5e0e8c75ebf4e33ae7bbafef1e87ae1f7fcf49506499700e78`
  - `examples/bonsaihub/build_preread.py` `db3525b087859c01d4e1c39494034fc7370c5047775ea52c19169bb2c1e2d49e`
  - `examples/bonsaihub/pitch.brief.toml` `9bdd4d38a1578ec96cddc5d902cb7d098502ef6ed3b5fc2459706c0246419aca`
  - `examples/bonsaihub/pitch.pptx` `88c075546b98665e461e232b4b541d18a76880b2bb79fb76ab26db96fc5a0727`
  - `examples/bonsaihub/preread.brief.toml` `574cb19d4b2e7bc286827d48a01a8448062477aa6c549e136f0e6ad365164380`
  - `examples/bonsaihub/preread.pptx` `66086ceb4c918a4224709d7759d21b933d5b131fed4ac65550059d996d84838c`
  - `examples/bonsaihub/render/pitch/contact.png` `c2557824b3e6d5d2e89f18edbc301da1ca3362aa9ae2dcabdf9dacb2075fd6cb`
  - `examples/bonsaihub/render/pitch/slide-01.png` `ab5c19551ee62b12aa4e04435ada86f4a92c1a54abd0153dd1abb29f51f3a638`
  - `examples/bonsaihub/render/pitch/slide-02.png` `07561c6bf47069da4cdfb3561bb514b57a6736e2bfaf36a1da4b0fbfccdd0ab5`
  - `examples/bonsaihub/render/pitch/slide-03.png` `34c238d90c55515864c0b92361b1996776f14caadff43b7a908ba1ce641719d4`
  - `examples/bonsaihub/render/pitch/slide-04.png` `c3f8cb1ea790e562b79cf7d0cfbd52bd6765b1070018805fe7b5340afa12b50d`
  - `examples/bonsaihub/render/pitch/slide-05.png` `884422a40e29f6a2ccdb11151c1115991291742fc7180db1404602a58b9cbf02`
  - `examples/bonsaihub/render/pitch/slide-06.png` `9df36c5a9b7793138ab195584910957759f1adb50d713b4e549bfb6d8efe671d`
  - `examples/bonsaihub/render/pitch/slide-07.png` `0e86a99b0e760c15c1712093d0ee16604f92cfdc6da74b03728d55a0342244b8`
  - `examples/bonsaihub/render/pitch/slide-08.png` `b4774ab80f8a7b83e3dc9fb20d8464eddfef7e6cda0f12382300aef86b007822`
  - `examples/bonsaihub/render/pitch/slide-09.png` `eb408dac2eb4a4122ad5b5ce1c705a6936715188e9287fdcd6cd7cf2bb0384a8`
  - `examples/bonsaihub/render/pitch/slide-10.png` `f2d31e85748616170dd7b8959af0313b3f7062c7b8d55515e9c6de8c2d8432e2`
  - `examples/bonsaihub/render/pitch/slide-11.png` `97c276e37b29fcb506ee72adeb1a94fc8e5c2e57196eafe08d15c9c93c2c47e9`
  - `examples/bonsaihub/render/preread/contact.png` `917a6a62b6cf888060110bd67ea418ef72081959606f77cb21f2b12e5805766d`
  - `examples/bonsaihub/render/preread/slide-01.png` `98a1011d4cc9ebfd069197602cbeaaac347ca83acebc6680acf2086b205a1f55`
  - `examples/bonsaihub/render/preread/slide-02.png` `b0a9faf3bd708d376521a5b0aec57ece0307efabb6ce5c4cbb57d60fdaa21e3b`
  - `examples/bonsaihub/render/preread/slide-03.png` `9ac1940d18bf3b5845cbf7b9e28c847096ed131d588af850ce05eebd50b9ad57`
  - `examples/bonsaihub/render/preread/slide-04.png` `07383db76707dfa9fb80d69935e80a487a7417068bac3e6b6c60142b355db3a7`
  - `examples/bonsaihub/render/preread/slide-05.png` `970d178152270b1085febc2932f6f601fccea64aa09c933d4e605f54d07aed15`
  - `examples/bonsaihub/render/preread/slide-06.png` `84234d42087648e246f9d7a864d95fd5ae9e726c802f05fa18151e57f61f4f47`
  - `examples/bonsaihub/render/preread/slide-07.png` `352d66e37b4ab33440f9b0cc8058202e646dcde0763a57365b4a870f74467e61`
```

- **`demo.py collect`** copied these 26 files into `examples/bonsaihub/`. Each copy has
  the SHA-256 the record lists, and nothing else was copied.
- No file the session wrote names anyone but Tyler or holds a local path. Both decks
  have creator and last-modified-by `Tyler`.
- This session wrote, edited and ran nothing in `~/keyline-demo-2` except
  `tools/demo.py`.
- **Lint:** the two build scripts fail CI's `ruff check .` on line length. They are not
  edited; `ruff.toml` excludes them (deviation T).
- **AC-21** passes (above), and so does the hygiene test.

## Report B (T-49, 2026-10-31) · ready for G-2 and the Phase B audit

Each criterion re-run at the commit that holds this section (LibreOffice 26.8.1.1,
OfficeCLI, all six twins). The sections above hold the detail.

| Criterion | Command | Output | Verdict |
|---|---|---|---|
| AC-17 · SKILL.md | `pytest -q tests/acceptance/m2/test_ac17_skill_md.py` | 10 passed | PASS |
| AC-18 · Docs integrity | `pytest -q tests/acceptance/m2/test_ac18_docs.py tests/acceptance/m2/test_gen_docs.py`; `python tools/gen_docs.py --check` | 34 passed; exit 0 | PASS |
| AC-19 · Package | `python tools/build_skill.py`; `pytest -q tests/acceptance/m2/test_ac19_package.py` | `bf40df0f…b9c6ce`, the same on a second build; 4 passed | PASS |
| AC-20 · Sandbox smoke | `pytest -q tests/acceptance/m2/test_ac20_sandbox.py` | 4 passed | PASS |
| AC-21 · BonsaiHub | `pytest -q tests/acceptance/m2/test_ac21_bonsaihub.py` | 12 passed | PASS (run 2; G-2a recorded) |
| AC-22 · Surfaces | see AC-22 | (b) Claude Code: `check` exit 0, deck committed; (a) claude.ai: waits for Tyler; (c) desktop: optional, not run | PARTLY |
| AC-23 · Hygiene and CI | `pytest -q tests/acceptance/test_ac12_hygiene.py tests/acceptance/m2/test_ngram_overlap.py`; `python tools/ngram_overlap.py skill docs` | 11 passed; 14 shared sequences, the research headings `anti-tells.md` cites, as before | PASS |

- **Deviations:** P to V, in "Deviations (Phase B)". T (the demo's build scripts
  excluded from ruff), U (P-3 names the file) and V (the skill as a project skill) are
  new since the checkpoint at `3566cb4`.
- **Open questions:** in "Open questions (Phase B)": Q-62 (deferred to spec 003), and the
  auditor's two notes for G-2.
- **Not done in Phase B, by plan:**
  - AC-22 (a), claude.ai, which is Tyler's;
  - the two fixes for tests that depend on the environment, for the Phase B round:
    `test_fixture_repro` compares PNG bytes (it should compare decoded pixels), and
    `test_fx17` asserts a glyph order for U+2046 (it should skip that for `NO_TWIN`).
- **Next, after the stop:** the spike for spec 003 (approved), as
  `docs/reference-study.md` plans it with the auditor's additions, recorded in
  `docs/spike-003.md`.

**STOP** for G-2 (Tyler, as B-28 scopes it: whether both demo decks are correct and
tailored to their briefs: the spine, the voice drawn from `[product.world]`, the
disclosure) and for the Phase B audit.
