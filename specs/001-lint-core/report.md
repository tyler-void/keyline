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
