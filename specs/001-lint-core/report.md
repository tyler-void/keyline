# Report 001: lint core

- **Spec:** [`spec.md`](spec.md), with amendments A-1…A-10 · **Plan:** [`plan.md`](plan.md) ·
  **Audit:** [`audit-01-plan.md`](audit-01-plan.md)
- **Branch:** `001-lint-core` · tasks T-01…T-24, one or more commits each, all pushed
- **Environment (local):** Python 3.11.16 (uv venv), lxml 6.1.3, Pillow 12.3.0,
  python-pptx 1.0.2, OfficeCLI 1.0.152, Linux
- **CI:** GitHub Actions `ci` on ubuntu-latest, Python 3.11 and 3.13, green on every
  task commit. Run 36034370655 (T-24): `172 passed, 2 skipped` on both versions; the
  two skips are the OfficeCLI render tests (`officecli is not installed`).

## Reproduce

```sh
git clone https://github.com/tyler-void/keyline && cd keyline && git checkout 001-lint-core
python3.11 -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/ruff check . && .venv/bin/ruff format --check .
.venv/bin/pytest -q                       # 172 passed, 2 skipped without OfficeCLI
                                          # 174 passed with OfficeCLI 1.0.152 on PATH
```

Each acceptance criterion has its own test file, `tests/acceptance/test_acNN_*.py`.
The commands below are the same checks run by hand.

## Acceptance criteria

| AC | result |
|---|---|
| AC-1 | PASS |
| AC-2 | PASS |
| AC-3 | PASS |
| AC-4 | PASS |
| AC-5 | PASS |
| AC-6 | PASS |
| AC-7 | PASS |
| AC-8 | PASS |
| AC-9 | PASS |
| AC-10 | PASS (local, OfficeCLI 1.0.152); skipped in CI by design |
| AC-11 | PASS |
| AC-12 | PASS |

### AC-1 · `kpi-recipe.pptx`, presented mode — PASS

```
$ keyline lint fixtures/golden/kpi-recipe.pptx ; echo $?
slide 2 · dead-band · warning · 7.05 cm empty bottom band from 12.00 to 19.05 cm (37% of slide height)
slide 2 · edge-margin · warning · T2 · 1.20 cm from the top edge (min 1.27 cm)
slide 2 · equal-card-row · warning · TextBox 2 · 3 equal cards in a row (9.78 × 7.00 cm, gaps 0.76 cm), each with text
slide 3 · edge-margin · warning · T3 · 1.20 cm from the top edge (min 1.27 cm)
slide 4 · dead-band · warning · 4.80 cm empty middle band from 3.20 to 8.00 cm (25% of slide height)
slide 4 · dead-band · warning · 8.05 cm empty bottom band from 11.00 to 19.05 cm (42% of slide height)
slide 4 · edge-margin · warning · T4 · 1.20 cm from the top edge (min 1.27 cm)
7 findings: 0 error, 7 warning, 0 advisory
2
```

- **Required, all present:**
  - `dead-band` on the bottom band of slides 2 and 4;
  - `edge-margin` on T2, T3 and T4 (1.20 cm);
  - `equal-card-row` on slide 2. "TextBox 2" is the name OfficeCLI gave the first card.
- **Forbidden, all absent:**
  - no overlap finding on slide 3;
  - no `equal-card-row` on slide 4, because its boxes are joined by connectors;
  - no `dead-band` on slide 1;
  - no `title-not-dominant` on slide 2.
- The slide 4 middle band (25.2%) fires as audit Q18 ruled.
- Test: `tests/acceptance/test_ac01_kpi.py` (12 tests). It also pins the exact list of
  warning-level findings.

### AC-2 · `editorial.pptx`, read mode — PASS

```
$ keyline lint fixtures/golden/editorial.pptx --mode read ; echo $?
slide 1 · box-overlap · advisory · n1 · box overlaps d1 by 8.60 × 0.30 cm (boxes, not ink)
  … 5 more box-overlap advisories (n2/d2, n3/d3, r1a/r1b, r2a/r2b, r3a/r3b)
slide 1 · edge-margin · warning · verdict · 0.88 cm from the bottom edge (min 1.27 cm)
slide 1 · edge-margin · warning · verdicttx · 0.54 cm from the bottom edge (min 1.27 cm)
slide 1 · text-contrast · warning · l3 · E8422E on F2F2F0 (slide background) is 3.57:1 at 9.5 pt (needs 4.5:1)
9 findings: 0 error, 3 warning, 6 advisory
2
```

- **Required, all present:** `edge-margin` on `verdict` (0.88) and `verdicttx` (0.54),
  and `text-contrast` on `l3` (3.57).
- **Forbidden, all absent:**
  - no `edge-margin` on `mark` (1.25 cm);
  - no `body-too-small`;
  - no `text-contrast` on `n3`;
  - no `title-underline` on `rule2`;
  - overlap findings are advisory only.
- The 6 box overlaps are exactly the prototype's 6 false positives from L-005. They
  are now advisory.
- Test: `tests/acceptance/test_ac02_editorial_read.py`.

### AC-3 · `editorial.pptx`, presented mode — PASS

```
$ keyline lint fixtures/golden/editorial.pptx
slide 1 · body-too-small · warning · d1 · 12.5 pt text in a 9-word paragraph (min 18 pt in presented mode)
slide 1 · body-too-small · warning · d2 · 12.5 pt text in a 13-word paragraph (min 18 pt in presented mode)
slide 1 · body-too-small · warning · d3 · 12.5 pt text in a 12-word paragraph (min 18 pt in presented mode)
slide 1 · body-too-small · warning · verdicttx · 11 pt text in a 10-word paragraph (min 18 pt in presented mode)
```

Test: `tests/acceptance/test_ac03_editorial_presented.py`.

### AC-4 · `editorial-fixed.pptx`, read mode — PASS

```
$ keyline lint fixtures/golden/editorial-fixed.pptx --mode read ; echo $?
  … 6 box-overlap advisories (unchanged from editorial.pptx)
6 findings: 0 error, 0 warning, 6 advisory
0
```

- **Build.** `fixtures/golden/src/editorial-fixed.sh` was run with OfficeCLI 1.0.152.
  OfficeCLI reported `Validation passed` and `Found 0 issue(s)`.
- **Diff.** `diff editorial.sh editorial-fixed.sh` shows 20 changed lines:
  - 16 are the `y` values of `rule3 … verdicttx`;
  - 1 is the `l3` color (`E8422E → CC3322`);
  - 2 are the header comment and the default output name (see Deviations).
- **Final positions:** `rule3` 12.85, `ftlab` 13.15, rows at 14.00 / 15.00 / 16.00,
  `hr1` 14.80, `hr2` 15.80, `verdicttx` 16.90 (bottom margin 1.30 cm), `verdict` 16.99.
- **Tests:** `tests/acceptance/test_ac04_editorial_fixed.py`. It checks exit 0, that
  there is no new warning compared with `editorial.pptx` in read mode (audit Q27), and
  that the three true defects are gone.
- **Render:** [`evidence/editorial-fixed.png`](evidence/editorial-fixed.png).

### AC-5 · python-pptx placeholder deck — PASS

- **Deck.** `fixtures/foreign/pptx-default-placeholders.pptx` uses python-pptx 1.0.2's
  default template and layout "Title and Content". Its slide XML contains no `a:xfrm`
  (asserted).
- **Geometry.** It resolves from the layout:
  - title 457200 / 274638 / 8229600 / 1143000;
  - body 457200 / 1600200 / 8229600 / 4525963.
  - These match audit 01's values and python-pptx's own `placeholder.left/top/…`
    (asserted in `test_python_pptx_oracle_agrees`).
- **Sizes** resolve from the master `txStyles`: 44 pt and 32 pt.
- **Background** resolves through `bgRef idx=1001` to `#FFFFFF`.
- No `adapter-unresolved` is emitted for either placeholder.
- Test: `tests/acceptance/test_ac05_placeholders.py` (6 tests).

### AC-6 · nested-group deck — PASS

- **Deck.** `fixtures/foreign/nested-groups.pptx` has three levels:
  - G1 at scale 0.5;
  - G2 inside G1 at scale 2, with a non-zero `chOff`;
  - G3 inside G1, rotated 90° (audit Q17).
- **Expected values.** They were derived by hand in the builder's docstring. Every
  leaf (A, B, C, D) matches within 1 EMU, for its unrotated rectangle, its rotation
  and its bounding box.
- Test: `tests/acceptance/test_ac06_groups.py` (5 tests).

### AC-7 · invalid input — PASS

```
$ head -c 4096 /dev/urandom > noise.pptx; keyline lint noise.pptx ; echo $?
keyline: cannot scan …/noise.pptx: not a zip file: noise.pptx
1
$ keyline lint letter.docx ; echo $?
keyline: cannot scan …/letter.docx: not a pptx: main part is word/document.xml (application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml)
1
```

- Each case prints exactly one stderr line, and stdout stays empty (asserted).
- The same test file also covers a missing file.
- `tests/adapter/test_package.py` covers XXE, billion-laughs, zip-bomb (size cap),
  member-count cap and malformed XML.

### AC-8 · determinism — PASS

```
$ for d in kpi-recipe editorial; do for m in presented read; do
    for i in 1 2 3; do keyline lint fixtures/golden/$d.pptx --mode $m --json 2>/dev/null | sha256sum; done | sort -u | wc -l; done; done
1  1  1  1        (one distinct hash per deck × mode)
```

- The test runs 3 subprocesses for each golden deck in each mode and asserts that
  stdout and stderr are both byte-identical: `tests/acceptance/test_ac08_determinism.py`.
- `tests/acceptance/test_snapshots.py` also compares every golden deck in both modes
  with reviewed JSON in `fixtures/expected/`. That includes `editorial-fixed`.

### AC-9 · speed — PASS

```
$ pytest -q -s tests/acceptance/test_ac09_speed.py
kpi-recipe lint wall times: 0.057s, 0.058s, 0.058s
```

- The timing covers the whole process, interpreter start included (audit Q30), and
  asserts the maximum of 3 runs is < 1.0 s.
- The test also passes in CI on both Python versions (run 36034370655).

### AC-10 · render — PASS (local), skipped in CI

```
$ keyline check fixtures/golden/kpi-recipe.pptx -o OUT ; echo $?
  … lint findings as in AC-1 …
note (L-002): OfficeCLI renders fall back to sans-serif for any font that is not installed, so these PNGs cannot verify typography.
OUT/slide-01.png
OUT/slide-02.png
OUT/slide-03.png
OUT/slide-04.png
OUT/contact.png
2
```

- **Tests.** `tests/acceptance/test_ac10_render.py`: 7 tests, all passing locally.
  - The 2 OfficeCLI tests skip in CI (`officecli is not installed`).
  - The paths without OfficeCLI run everywhere:
    - `render` exits 1 with the install command;
    - `check` keeps lint's exit code and prints `render: skipped (…)` (A-10);
    - `--require-render` turns a render failure into exit 1.
- **Contact sheet:** [`evidence/kpi-recipe-contact.png`](evidence/kpi-recipe-contact.png).
  Its Georgia titles render in sans-serif, which shows L-002 in practice.

### AC-11 · CI — PASS

- Every commit from T-02 onward ran green on Python 3.11 and 3.13. List them with
  `gh run list --branch 001-lint-core`.
- Last run 36034370655:
  - `ruff check`: All checks passed!
  - `ruff format --check`: 88 files already formatted
  - `pytest`: 172 passed, 2 skipped

### AC-12 · hygiene — PASS

```
$ git log --all --format='%an <%ae> | %cn <%ce>' | sort | uniq -c
     29 Tyler <code@tyler-void.dev> | Tyler <code@tyler-void.dev>
$ git log --all --format='%B' | grep -i '^co-authored-by' | sort | uniq -c
     28 Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
```

(Counts as of T-24. This report's own commit adds one of each.)

- **Automated checks** (`tests/acceptance/test_ac12_hygiene.py`, 4 tests):
  - authors and committers against the D-014 allowlist;
  - trailers against D-013;
  - `creator`/`lastModifiedBy` of all 27 fixture decks, including their embedded
    workbooks;
  - the `NOTICE` line.
- **python-pptx template metadata.** The template ships `lastModifiedBy = "Steve
  Canny"`. Every builder overwrites it with `Tyler` (risk R-5, confirmed and handled).
- **No file copied from `anthropics/skills`.** This is a manual check, because it
  needs the network.
  - Command: `gh api 'repos/anthropics/skills/git/trees/main?recursive=1'` returned
    419 blobs (tree not truncated). Their SHAs were compared with `git ls-files -s` at T-24
    (136 files).
  - The only matches are the 5 empty `tests/**/__init__.py` files. Every empty file in
    git has blob `e69de29…` (`git hash-object /dev/null`), so these are not copies.
  - Three file names are shared (`.gitignore`, `README.md`, `__init__.py`), but the
    contents differ: no blob match.

## Deviations

1. **Python version.** Spec §1 said Python ≥ 3.10 and CI on 3.10 and 3.12.
   Implemented ≥ 3.11 and CI on 3.11 and 3.13, with stdlib `tomllib`, because of
   D-012.
2. **Extra config keys.** Spec §5 lists 9 threshold keys. `thresholds.toml` also holds
   the fixed numbers from the §6 rule table, in a `[common]` table: 0.05 cm off-slide,
   95% background coverage, 0.1 cm overlap, the KPI 48 pt / 5 words, the underline
   window, and the card tolerances. Reason: constitution V says thresholds are data.
   `large_text` is split into `large_text_pt` and `large_text_bold_pt`, as audit Q24
   accepted.
3. **`box-overlap` exemption.** Spec §6 exempted "a text shape inside a non-text
   backing shape". It is not implemented: the exemption could never apply (audit Q19).
4. **`editorial-fixed.sh`.** Spec §8 said "change nothing else". Two more lines
   changed:
   - The default output name is now `editorial-fixed.pptx`. Kept as `editorial.pptx`,
     running the script with no argument would overwrite the provided golden.
   - The header comment was updated to describe the fixed file.
5. **Rule tests.** Plan §1 listed one `tests/rules/test_<id>.py` per rule. Instead,
   one data-driven test (`tests/rules/test_rule_fixtures.py`) reads
   `fixtures/rules/expect.toml`. Reason: the same assertions, without 11 near-identical
   files.
   - Another test checks that every rule has at least one positive and one negative
     case.
   - Advisory-only rules use an `absent` key for their negatives, because `must_not`
     ignores advisories by design.
6. **`render.py` imports.** Plan §1 said `render` imports nothing from `ooxml`. It
   imports `ooxml.package` to count slides, rather than probing OfficeCLI page by page.
7. **Model details.**
   - Spec §2 listed `size_pt`. `Run.size` stores the integer `sz` (1/100 pt), and
     `size_pt` is a derived property. Reason: exact comparisons.
   - Additions: `Run.hidden` (`a:noFill` text draws nothing, so it is skipped),
     `Shape.z`, and `Shape.box` next to the unrotated `x y w h`.
8. **Adapter rationale.** `adapter-unresolved` and `unsupported-content` use rationale
   `L-001`. The spec requires a lesson id or a research section, and no lesson is
   specifically about adapter coverage.
9. **`check` output directory.** It defaults to `<deck>-render/` when `-o` is not
   given. The spec gives no default.
10. **No command.** `keyline` with no subcommand prints help to stderr and exits 1.
    The spec doesn't say what should happen.
11. **`measured` choices.** P-12 left these to the rule.
    - `title-underline`: `measured` is the bar's width as a fraction of the content
      width, compared with the 0.5 threshold.
    - `notes-missing`, `font-count`, and the advisories: see
      `fixtures/expected/*.json`.

No amendment turned out to be wrong. Every one of A-1 to A-10 was implemented as
written, and the golden acceptance criteria pass under them.

## Open questions

1. **Ratio precision.**
   - P-12 fixed ratios at 2 decimals. The kpi slide 4 middle band is 25.2%, so it shows
     `"measured": 0.25` against `"threshold": 0.25`, and the finding looks as if it
     shouldn't fire. The message ("4.80 cm … 25%") has the same problem.
   - Proposal: 3 decimals for ratios, or report the band in cm against a cm threshold.
2. **Layout and master shapes are not linted.** The slide model contains only the
   slide's own spTree (spec §2). So a logo or footer bar drawn on the layout or master
   doesn't count as content for `dead-band`, and isn't checked by `edge-margin`.
   - Proposal for a later spec: include non-placeholder layout/master shapes, and
     honor `showMasterSp`.
3. **The Office default template fails two defaults.** With python-pptx's default
   template, the title placeholder sits 0.76 cm from the top (`edge-margin`). Its
   44 pt title over a 32 pt body is 1.38× (`title-not-dominant` in read mode, which
   needs 1.6×).
   - Command: `keyline lint fixtures/foreign/pptx-default-placeholders.pptx --mode read`.
   - The measurements are correct. This is a calibration data point (constitution V):
     every stock-template deck will get these warnings.
4. **Unverified against PowerPoint.** Three behaviors have only been checked by
   reasoning and unit tests, never in real PowerPoint:
   - A-4's cascade, which drops `pPr/defRPr`;
   - the `tint`/`shade` formulas (R-4);
   - ignoring autofit `fontScale` (R-2).
   `docs/adapter.md` records all three.
5. **P-11 (`mc:AlternateContent`).** The audit gave no separate ruling on it. It is
   implemented as proposed: the adapter reads `mc:Fallback` and emits an
   `unsupported-content` advisory.
6. **`editorial-fixed` spacing.** It passes lint, but the verdict line sits tight
   under the last table row: the gap between their boxes is 0.05 cm (see the render).
   Constitution VIII says the linter doesn't judge that; a designer might.
7. **CLAUDE.md is out of date.** It still says "Pure Python >= 3.10". D-012 supersedes
   it, but I changed only the Identity bullet (F-1), as instructed. Should that line
   be updated?
8. **Duplicate `research.md`.** The untracked copy in the repo root is still there.
   Audit F-4 says it can be deleted; I left it because nobody asked me to delete it.

---

# Round 2: audit 02 fix items

- **Audit:** [`audit-02-implementation.md`](audit-02-implementation.md), verdict "FIX, then
  merge". Amendments A-11…A-18 and criteria AC-13…AC-20 are in the spec's amendment
  log (commit `564cd05`, "docs: apply audit 02").
- **Tasks:** T-26…T-33 in [`tasks.md`](tasks.md), one fix item each, all pushed.
- **Decks:** `fixtures/foreign/stress/`, the 13 decks the new ACs use, byte-identical to
  audit 02's `stress-corpus/decks/`, with their builders
  ([README](../../fixtures/foreign/stress/README.md)).
- **CI:** green on Python 3.11 and 3.13 for every Round 2 commit from T-26 to T-32,
  and again after T-33's second perf commit. The last run, 36244873259 (`4b991fa`),
  gave `213 passed, 2 skipped` on both versions (the 2 skips are the OfficeCLI render
  tests).
- **Local:** `pytest -q` gives 215 passed (OfficeCLI 1.0.152 on PATH).

## Acceptance criteria, round 2

| AC | result |
|---|---|
| AC-1 … AC-12 | PASS (unchanged tests; snapshot changes explained below) |
| AC-13 | PASS |
| AC-14 | PASS |
| AC-15 | PASS |
| AC-16 | PASS |
| AC-17 | PASS |
| AC-18 | PASS |
| AC-19 | PASS |
| AC-20 | PASS, with the tightest margin of any AC (see below) |

### AC-13 · encoding and precision (A-16) — PASS

```
$ PYTHONIOENCODING=cp1252 keyline lint fixtures/foreign/stress/d25_ppx_localized_names.pptx --json > cp.json; echo $?
2
$ PYTHONIOENCODING=utf-8 keyline lint …/d25_ppx_localized_names.pptx --json > u8.json; cmp cp.json u8.json && echo equal
equal
$ python -c "import json; print(sorted({f['shape_name'] for f in json.load(open('cp.json','rb'))}))"
['Box 🚀 4', 'Textfeld 3 – Übersicht', 'Tiêu đề 1', 'タイトル 2']
$ keyline lint fixtures/golden/kpi-recipe.pptx --json | … dead-band on slide 4
4 0.252 4.80 cm empty middle band from 3.20 to 8.00 cm (25.2% of slide height)
4 0.423 8.05 cm empty bottom band from 11.00 to 19.05 cm (42.3% of slide height)
```

- The cp1252 run writes no traceback. On a cp1252 stream, stderr shows the names as
  backslash escapes (`タイ…`); see Deviation R2-1.
- Test: `tests/acceptance/test_ac13_encoding.py` (3 tests, including an `ascii` stream).

### AC-14 · no tracebacks (A-17) — PASS

```
$ for f in fixtures/foreign/stress/o5*.pptx fixtures/foreign/stress/d27*.pptx; do keyline lint $f >/dev/null 2>&1; echo "$(basename $f) $?"; done
o51_lummod_percent_string.pptx 2      o54_lumoff_float.pptx 2
o52_alpha_percent_string.pptx 2       o55_cxn_id_word.pptx 2
o53_tint_percent_in_master_bg.pptx 2  o56_ext_40_digits.pptx 2
d27_strict_from_ppx.pptx 1
$ keyline lint fixtures/foreign/stress/d27_strict_from_ppx.pptx
keyline: cannot scan fixtures/foreign/stress/d27_strict_from_ppx.pptx: Strict Open XML (ISO/IEC 29500 Strict) is not supported yet
$ keyline lint fixtures/foreign/stress/o55_cxn_id_word.pptx 2>&1 | grep unresolved
slide 2 · adapter-unresolved · advisory · Connector 6 · could not parse stCxn@id="first"; the value was dropped (A-17)
```

- **Parsed now.** `75%`, `50%`, `95%` and `25000.0` parse, so o51, o53 and o54 are
  linted normally.
- **o52.** Its `alpha 50%` gives the existing "alpha is not supported" advisory (P-9).
- **Injected exception.**
  - `test_injected_rule_exception_is_one_line` replaces `dead-band`'s check with one
    that raises `ZeroDivisionError`. It asserts exit 1 and exactly one stderr line:
    `keyline: internal error while reading rule dead-band: ZeroDivisionError; rerun
    with --traceback and report it`.
  - `test_traceback_flag_prints_the_trace` checks that `--traceback` adds the full
    trace.
- Tests: `tests/acceptance/test_ac14_no_traceback.py` (11 tests) and
  `tests/unit/test_numbers.py`.

### AC-15 · fontRef in the color cascade (A-11) — PASS

```
$ keyline lint fixtures/foreign/stress/d15_ppx_style_fontref.pptx 2>&1 | grep text-contrast
slide 3 · text-contrast · warning · Rectangle 2 · FFFFFF on FFF2CC (Rectangle 2) is 1.12:1 at 24 pt (needs 3:1)
```

- Slide 2 (white on navy) no longer reports the false `000000 on 1F3864 1.81:1`.
- Slide 4 (the explicit-black control) is clean.
- Test: `tests/acceptance/test_ac15_fontref.py`.
- The unit test `test_a11_fontref_comes_after_shape_lststyle_and_before_inherited_styles`
  pins the new order. The shape's own `lstStyle` still wins over `fontRef`, and size
  keeps the A-4 order.

### AC-16 · hidden shapes (A-12) — PASS

```
$ keyline lint fixtures/foreign/stress/d17_raw_geometry.pptx 2>&1 | grep "slide 4"
slide 4 · dead-band · warning · 11.05 cm empty bottom band from 8.00 to 19.05 cm (58.0% of slide height)
slide 4 · title-not-dominant · warning · Title · title 40 pt is 1.67× the largest body text (24 pt); needs 2×
slide 4 · unsupported-content · advisory · 3 hidden shapes not linted (A-12)
```

- There is no `off-slide` or `text-contrast` on the hidden shapes.
- The `title-not-dominant` is a true finding (40 pt title over 24 pt visible body).
- A hidden group removes all 4 of its descendants
  (`test_hidden_group_drops_its_children`).
- Test: `tests/acceptance/test_ac16_hidden.py`.

### AC-17 · tables and charts off the slide (A-13) — PASS

```
$ keyline lint fixtures/foreign/stress/d20_pgx_slop.pptx 2>&1 | grep "slide 6"
slide 6 · off-slide · error · Chart 0 · runs 2.54 cm past the bottom edge
slide 6 · off-slide · error · Table 0 · runs 5.00 cm past the right edge
slide 6 · unsupported-content · advisory · Table 0 · table text is not read in M1
```

- The chart now errors too, as A-13 says.
- Test: `tests/acceptance/test_ac17_table_off_slide.py`.

### AC-18 · autofit (A-14) — PASS

```
$ keyline lint fixtures/foreign/stress/d18_lo_autofit.pptx 2>&1 | grep "slide 2"
slide 2 · body-too-small · warning · PlaceHolder 2 · 9 pt (autofit 28.1%) text in a 11-word paragraph (min 18 pt in presented mode)
slide 2 · edge-margin · warning · PlaceHolder 1 · 0.76 cm from the top edge (min 1.27 cm)
```

- 32 pt × 28.122% = 8.999 pt, rounded to 9.00 pt (`"measured": 9.0`).
- There is no `title-not-dominant` in either mode.
- The `edge-margin` is the stock-template finding recorded as L-009.
- Test: `tests/acceptance/test_ac18_autofit.py`.

### AC-19 · contrast backing coverage (A-15) — PASS

```
$ keyline lint fixtures/foreign/stress/d16_raw_color.pptx 2>&1 | grep text-contrast
slide 3 · text-contrast · warning · TextBox 2 · 222222 on 000000 (slide background) is 1.32:1 at 24 pt (needs 3:1)
slide 4 · text-contrast · warning · Title 1 · FFFFFF on FFFFFF (slide background) is 1:1 at 40 pt (needs 3:1)
slide 5 · text-contrast · advisory · … background is the unknown fill of Rectangle 2   (alpha card)
slide 5 · text-contrast · advisory · … background is the unknown fill of Rectangle 4
slide 7 · text-contrast · advisory · … runs whose color could not be resolved      (run alpha)
```

- Slide 6 has no `text-contrast`: the navy card covers about 93% of the text box, above
  `backing_coverage_min = 0.90`.
- Slide 4 is FP-2 (a navy panel drawn on the layout), which audit 02 deferred as P1.
- AC-1 … AC-4 still pass, and their only snapshot changes are the precision changes
  from T-26.
- Tests: `tests/acceptance/test_ac19_backing.py` and `tests/unit/test_geom.py::test_coverage_of_inner_box`.

### AC-20 · scale (A-18) — PASS, tight margin

Whole-process wall times: median of 3 runs of `python -m keyline lint <deck> --json`.
The decks are generated by the test with `fixtures/foreign/stress/src/perf_shapes.py`.

| where | perf_1000 (< 1.0 s) | perf_150_x60 (< 2.0 s) |
|---|---|---|
| before T-33, local | 0.85 s | 3.62 s |
| local, final (Python 3.11) | 0.18 s | 1.05–1.37 s (this machine is noisy) |
| CI run 36244793649 | 0.24 s (3.11), 0.26 s (3.13) | 1.50 s (3.11), **1.62 s (3.13)** |
| CI run 36244873259 | 0.25 s (3.11), 0.19 s (3.13) | 1.53 s (3.11), 1.13 s (3.13) |

- The first T-33 commit (`e1a3113`) **failed** CI on both versions: perf_150_x60 took
  2.07–2.17 s. The auditor's own figure for the old code was 6.03 s.
- The second perf commit (`ec7ff14`) **failed** on 3.13 only, at 2.01 s.
- Two more rounds of optimization brought the worst CI time seen to 1.62 s.
- The threshold was never changed.
- **Integrity check.** After each optimization, lint JSON and stderr were
  byte-identical to the previous commit on all 40 fixture decks in both modes (80
  runs). The old code ran from a `git worktree`, and a check confirmed it was the old
  code that ran.
- **What changed:**
  - `box-overlap` uses an integer sort-and-sweep over x;
  - integer fast paths in rounding and number parsing;
  - integer cross-multiplication for the coverage tests;
  - Clark-notation lxml finds, and each element's children indexed once;
  - `text-contrast` walks down the z-order without re-sorting;
  - cached per-level styles and a cached text-bearing flag.
- **Media and the size cap.** The uncompressed-size cap now counts only XML and rels
  parts. `test_large_stored_media_member_passes_the_cap` lowers the cap to 1 MB and
  lints a deck carrying a 3 MB stored `ppt/media/video1.mp4`: it exits 2 as usual. The
  same deck with a 3 MB XML part still hits the cap.
- Test: `tests/acceptance/test_ac20_scale.py`. CI now runs pytest with `-rP`, so every
  CI log prints the AC-9 and AC-20 timings.

## Golden snapshot changes (all from T-26, A-16)

No other Round 2 task changed any golden output: `test_snapshots.py` passed unchanged
after T-27 to T-33.

| snapshot | field | before | after | why |
|---|---|---|---|---|
| `kpi-recipe.{presented,read}` | `dead-band` messages | `37%`, `25%`, `42%` | `37.0%`, `25.2%`, `42.3%` | percentages with 1 decimal |
| `kpi-recipe.{presented,read}` | `dead-band` slide 4 `measured` | `0.25`, `0.42` | `0.252`, `0.423` | ratios with 3 decimals (the 0.370 band still prints as `0.37`) |
| `editorial.{presented,read}` | `text-contrast` `l3` `measured` | `3.57` | `3.569` | ratios with 3 decimals; the message still says `3.57:1` |

`tests/acceptance/test_ac02_editorial_read.py` now expects `3.569`. That is the only
change to an AC-1 … AC-12 test.

## Deviations, round 2

- **R2-1 · A-16 stderr.**
  - **Spec said** `--json` writes UTF-8 bytes to stdout.
  - **Implemented**, and in addition the human-readable text streams use
    `errors="backslashreplace"`.
  - **Because** AC-13 also prints the same shape names to stderr; without this, stderr
    raises `UnicodeEncodeError` under cp1252.
- **R2-2 · A-12 advisory id.**
  - **Spec said** "the slide gets one advisory with the count of hidden shapes", naming
    no rule id.
  - **Implemented** as `unsupported-content`, with the message "3 hidden shapes not
    linted (A-12)".
  - **Because** that id already means "content the model does not read", and adding a
    new id is a spec decision.
- **R2-3 · A-17 range.**
  - **Spec said** drop values that cannot be parsed.
  - **Implemented:** values outside ST_Coordinate (±27273042316900 EMU) are dropped
    as well.
  - **Because** o56's 40-digit length parses as a number but broke the rounding.
- **R2-4 · A-17 `<part>`.**
  - **Implemented:** the internal-error line names the slide part while the adapter
    runs, and `rule <id>` while a rule runs.
  - **Because** a failure inside a rule has no part.
- **R2-5 · A-14 scope.**
  - **Implemented:** `normAutofit` is read from the shape's own `bodyPr` only, not
    inherited from the layout.
  - The effective size also sets the large-text threshold in `text-contrast`, because
    that is the rendered size.
- **R2-6 · AC-20 method.** The perf decks are generated by the test, not committed.
  The budget is judged on the median of 3 whole-process runs.
- **R2-7 · Stress builders.**
  - **Adapted from the audit's scripts**, only for output paths, the test photo, and
    the `Tyler` author (`_stress.py`).
  - `raw_oddities.py` builds only o51–o56 by default.
  - The copied builders are excluded from ruff, to keep them close to the auditor's
    text.
- **R2-8 · AC-12 allowlist.** Fixture metadata may also say `PptxGenJS`. d20's embedded
  chart workbook has `creator = PptxGenJS`; it is a tool name, like `OfficeCLI` (R-5).
- **R2-9 · `measured` for ratios.** P-12's "ratios with 2 decimals" is superseded by
  A-16's 3 decimals, for every ratio field: contrast, title ratio, dead-band, and
  underline width.

## Reproducing the stress decks

LibreOffice 26.8.0.3, node 26.10.0 and pptxgenjs 4.0.1 were installed for this round.

| decks | result |
|---|---|
| d15, d16, d17, d25, d27, o51–o56 (python-pptx) | rebuild part-for-part identical, `docProps` excluded; now a test: `test_stress_decks_reproduce`, `test_stress_strict_and_oddities_reproduce` |
| d20 (pptxgenjs 4.0.1) | rebuilds part-for-part identical (checked by hand; node is not in CI) |
| d18 (LibreOffice) | **does not reproduce**: LibreOffice 26.8.0.3 writes `fontScale="40000" lnSpcReduction="19999"`, where the committed deck (LibreOffice 24.2.7.2) has `fontScale="28122"`. The committed auditor deck is kept, and AC-18 refers to it |

## Open questions, round 2

1. **AC-20 margin.** The worst CI time seen is 1.62 s against 2.0 s, a 19% margin, and
   the runners vary by about ±20% between runs. If a slow runner flakes, the choices
   are Tyler's: raise the budget, or measure best-of-N instead of the median. Not
   changed here, because thresholds are not tuned to pass.
2. **d18 depends on the LibreOffice version** (see above). Should AC-18 name the
   LibreOffice version?
3. **FP-2 is still open** (d16 slide 4). It is audit 02's P1 backlog item: layout and
   master shapes as content and as contrast backing.
4. **Strict OOXML** (d27) exits 1 with an accurate reason. Supporting it is P2 backlog.
5. **Local files, not in the repo.** `stress-corpus/`, `keyline-audit-02.zip` and
   `research.md` sit untracked in the working-tree root. None was committed or deleted.

---

# Round 3: audit 03

- **Audit:** [`audit-03-round2.md`](audit-03-round2.md), verdict "SHIP after A-19". The
  stress tester's notes are kept as
  [`evidence/stress-notes-2026-09-25.md`](evidence/stress-notes-2026-09-25.md)
  (byte-identical copy of `stress-corpus/NOTES.md`).
- **A-19** (commit `24cb91e`, "docs: apply audit 03"):
  - AC-9 (`tests/acceptance/test_ac09_speed.py`) was judged on the maximum of 3 runs,
    and AC-20 (`test_ac20_scale.py`) on the median.
  - Both now use the minimum of 3 whole-process runs. Budgets are unchanged, and all
    three times are still printed.
- **Other changes in the same commit:**
  - L-010 appended to `docs/lessons-learned.md`: a stored autofit scale is trusted,
    which explains d17 slide 6's `body-too-small` at 11 pt.
  - `fixtures/foreign/stress/README.md` records d18's SHA-256
    (`b61e0580…c5b296f`, equal to `stress-corpus/decks/d18_lo_autofit.pptx`), and
    that it was built with LibreOffice 24.2.7.2 and is not reproducible on 26.8.

CI run 36245821572 (`24cb91e`), `pytest -q -rP`:

```
test (3.11)  kpi-recipe lint wall times: 0.094s, 0.094s, 0.095s     (AC-9, < 1.0 s)
test (3.11)  perf_1000 wall times: 0.24s, 0.24s, 0.24s              (AC-20, < 1.0 s)
test (3.11)  perf_150_x60 wall times: 1.47s, 1.49s, 1.50s           (AC-20, < 2.0 s)
test (3.11)  213 passed, 2 skipped in 20.32s
test (3.13)  kpi-recipe lint wall times: 0.081s, 0.081s, 0.083s
test (3.13)  perf_1000 wall times: 0.19s, 0.19s, 0.19s
test (3.13)  perf_150_x60 wall times: 1.15s, 1.12s, 1.14s
test (3.13)  213 passed, 2 skipped in 15.99s
```

The three runs agree to within 0.03 s on each runner, so the minimum and the median
give the same verdict here. The worst perf_150_x60 minimum in this run is 1.47 s,
against 2.0 s.
