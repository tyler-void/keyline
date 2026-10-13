# Audit 07 of spec 002: fix round 2 (FX-25 … FX-31, B-26) and the Phase B tasks

- **Audited:** branch `002-skill-pack` at `6ba6487`, fresh clone, 2026-10-09, on
  LibreOffice 24.2.7.2 with all six metric twins installed.
- **Auditor:** the external session. **Decides:** Tyler.
- **Verdict:**
  - **Round 2: ACCEPTED.**
    - Every audit 06 repro is fixed.
    - `measure_lo` holds all five criteria on 24.2.
    - `fit_stress` passes on 24.2 (1,177 texts, English and Vietnamese).
  - **Phase B: GO, with task changes.** A bounded in-set pass found three small
    estimator gaps (FX-32 … FX-34), and this sandbox showed one environment gap
    (FX-35). They land as the first commits of Phase B, before T-33, without a
    separate stop. The Phase B audit re-checks them.
  - **G-1 can run now,** on this head. FX-32 … FX-35 change the estimator, not the
    templates.

## 1. Round 2, checked

| check | result |
|---|---|
| Identity | 12 commits, all `Tyler <code@tyler-void.dev>`, one Claude trailer each |
| Docs | spec: +40 lines; B-25 and B-26 verbatim; lessons: +L-017 (pdfium character boxes against ink), 0 removed |
| Hashes | product `9b0fea6e…`, oracle `af534e21…`; audit 06 and its repro folder identical to the auditor's |
| Fixtures | 27 rebuilt, all spec 002 fixtures, plus the two templates; goldens untouched. Per part: only `<a:cs typeface=…>` additions in the theme, master, layouts and `presentation.xml`, plus slides where the pen writes runs (FX-29) |
| ruff | clean, 202 files |
| pytest (24.2) | **1223 passed, 9 skipped, 1 failed:** `test_missing_line_em_covers_the_installed_fallback_fonts` (FX-35) |
| M1 baseline | no differences |
| Regression | main vs branch: 308 pairs, 0 differing, 0 tracebacks |
| `measure_lo.py` (24.2) | (a) … (e) all **HOLD.** Cell allowance 0.05 mm, smallest slack 0.0285 pt; fallback line up to 1.5012 em |
| `fit_stress.py` (24.2) | **PASS:** 1,177 texts, 0 past a limit. Top +18.5 px against a 17.9 px allowance (Georgia, Vietnamese). Same maxima as 26.8 |

### Deviations

- **F and G:** accepted in advance.
- **H** ("exceeds" read as "is not smaller than"): accepted. It is conservative.
- **I** (every evidence value is checked at load): accepted.
  - An evidence value is a number with unit words.
  - The excluded characters are capitals with stacked accents, which a value almost
    never needs.
  - Failing at the brief is better than failing at the figure.
- **J** (a fallback glyph makes its whole row use the taller pitch): accepted. It is
  conservative.

## 2. New findings

A separate agent attacked the estimator **inside B-25's measured set only**, as audit
06 bounded it. It had not seen this audit's work. I re-ran every item on 24.2. The
scripts are in `audit07-repros/`.

### FX-32 · Major · Ink right of the last glyph's advance

- The estimator measures advances, but some glyphs draw past their advance. For
  example: Caladea Bold "f" by 0.078 em, Carlito Bold "ế" by 0.096 em, Gelasio "f".
- At a 120 pt numeral in the 282 pt side region, the 0.99 margin (2.8 pt) does not
  cover it.
- **Measured (`f1_right.py`, presented `evidence:figure` side, at the pen's limit):**
  - Cambria "7,1 kf": +7.7 px;
  - Calibri ",,...1ế": +10.7 px;
  - Georgia "1.21f": +2.7 px.
- B-26 measured only top and left reach, so these characters are in the numeral set.
- **Fix (B-27 item 2):** a line's width is its advances, plus its positive kerning,
  plus max(0, the last glyph's ink right − its advance). Store each glyph's right reach
  in the fit tables.

### FX-33 · Major · LibreOffice will not break before "\" after a space

- **Measured (`f2_backslash.py`, LaTeX-style text at the pen's limit):**

  | mode, family, region | estimated lines | LibreOffice lines | bottom edge |
  |---|---|---|---|
  | presented Arial, statement lede | 4 | 5 | **+25.8 px** |
  | presented Courier New, main and side body | 8 | 9 | **+24.8 px** |
  | read Arial, side body | 15 | 16 | **+15.8 px** |

- The agent's probe (`probe_b.py`) also found U+2044 in Calibri.
- B-22 item 4 and B-25 item 5 are hand-written lists, and this is the third round in
  which a list missed a character.
- **Fix (B-27 item 3):** measure the lists instead of writing them. `measure_lo.py`
  probes every non-letter character of the measured set, before and after a space, in
  both line conditions. The no-break-before and no-break-after sets become data, as
  the union over every measured version, and a test re-derives them.

### FX-34 · Minor · Kerning across ZWNJ and ZWJ

- **Measured (`f3_ignorable.py`, Calibri, V+ĩ and T+ĩ pairs split by a joiner):**
  LibreOffice still applies the pair, but the estimator drops it.
  - Presented body: 8 lines estimated, 9 set, +23.8 px.
  - Presented lede: +20.8 px.
- LRM does break the pair, so that case held.
- **Fix (B-27 item 4):** kerning pairs are looked up across default-ignorable code
  points. That only adds width, so it stays conservative where LibreOffice does break
  the pair.

### FX-35 · Minor · `missing_line_em` is machine-dependent

- Here, fontconfig's Thai fallback is Loma, at hhea 1.589 em. The repo's own test
  fails against `missing_line_em = 1.52`, which was measured on Tyler's machine
  (Noto Sans Thai).
- Thai is outside the measured set, so nothing is promised there. But the value is
  meant to be conservative, and the test is a good guard.
- **Fix (B-27 item 5):** `missing_glyph_em` and `missing_line_em` take the largest
  value measured in any environment Tyler or the auditor has run. That makes
  `missing_line_em` 1.59 now. Record each environment in the data.

### Held under attack

- **B-26 boundary** (`b26_boundary.py`): the tallest and leftmost characters still
  allowed (Ầ Ề Ồ Ǻ Ů ḱ ƒ j ĵ ǰ Ỷ), alone as numerals, in 5 regions × 6 families × 2
  modes: 600 renders, 0 past a limit.
- **B-26 refusals** (`b26_bypass.py`): all 37 excluded characters, in NFC and NFD, were
  refused (74 of 74). No in-set sequence composes into an excluded character.
- **Descenders and punctuation runs** (`sweep.py`): ỵ ỹ ỷ ą ę ţ ş, and … — – ‘’ “”
  «» ‹› ‰ ′ ″ € ₫ ¥, at the limit in bottom-anchored titles, labels, attributions,
  bullets, tables and side bodies, both modes and six families: 198 texts, 0 past a
  limit.

## 3. Rulings on Q-53 … Q-59

| Q | Ruling |
|---|---|
| 53 | **Accept: U+2212 joins the measured set (B-27 item 1).** Negative figures are common, §4.4 accepts the sign, and models write it. Regenerate the tables and the numeral set, and re-run `measure_lo` and `fit_stress`. The pen still refuses other Mathematical Operators |
| 54 | **Accept with changes.** There is no new registry entry; the pen's warning stays the check. (a) A test pins the warning's prefix (`keyline pen: warning:`). (b) `gen_docs.py` generates the per-twin coverage table (which twin lacks which letters), and `brief.md` and `check.md` use it instead of a hand-typed "Caladea lacks 88". (c) The voice step picks the family from that table before building, so the warning is a backstop |
| 55 | **Accept with changes.** Pin python-pptx 1.0.2 through a constraints file, because determinism and the axis-id fix were proven on it; leave lxml and Pillow unpinned but record them. Skip without network locally, but **fail** in CI. `kl.py doctor` prints the python-pptx version, and `check.md` says byte-determinism holds on 1.0.2 |
| 56 | **Accept with a change.** Add a generic dev tool, `tools/ngram_overlap.py A B`: it counts shared 8-word sequences between two folders and holds no third-party text. The auditor runs it against a clone of anthropics/skills at the Phase B audit. The report's process statement stays |
| 57 | **Accept,** plus the per-twin coverage table from Q-54 |
| 58 | **Accept with changes.** (a) Before committing, record the sha256 of `dist/keyline.zip` and of every file the fresh session wrote. (b) If the pen changes later (audit fixes), this session may re-run the fresh session's build scripts **unchanged** to regenerate the decks; any script edit needs a fresh-session re-run. (c) A T-45 failure means a skill fix and a fresh re-run, never a hand edit |
| 59 | **Accept,** and the test covers the pen section too: `DoesNotFit`, B-22's refused classes, B-26 and the warning prefix |

## 4. Changes to the Phase B tasks

A separate cold reviewer read the tasks against §8 … §10, AC-17 … AC-23 and the
constitution. I checked the points below against the files before adopting them.

1. **FX-32 … FX-35 come first,** before T-33, with B-27.
2. **G-1 before packaging.**
   - G-1 closes, and its fix items land, before T-43.
   - Today no task covers spec §11's "G-1 fix items land as amendments before Phase B
     ends". Add one.
3. **Docs test first.**
   - The skeleton of `test_ac18_docs.py` lands with T-36, and each doc task adds its
     own checks.
   - At the moment T-35, T-37, T-38 and T-41 cite AC-18 checks that only exist at
     T-42.
4. **T-34 (`SKILL.md`):**
   - say how the agent finds its own folder on each surface, since no absolute paths
     are allowed;
   - give the loop's voice step its own step (B-8.15), and test that it is there;
   - test that every token `doctor.py` can print has an action in `SKILL.md`;
   - when python-pptx cannot be installed (no network), route to "check a deck" and
     say why.
5. **T-44 (sandbox smoke):**
   - `build_specimens.py` reads its briefs from `parents[1]` (line 20), so "copied
     beside it" fails. Copy the `fixtures/packs/` layout, or pass the paths.
   - `kl.py run` must set `sys.argv` and run with `run_name="__main__"`.
   - The test scrubs `PYTHONPATH`, runs from a working directory outside the repo, and
     asserts that `keyline.__file__` is under `lib/`.
6. **T-45:** the deck tests skip only while no demo file exists. Once one exists, they
   fail when they cannot run. "Two builds identical" includes the committed bytes.
7. **T-46 (the demo):**
   - The fresh session runs in an empty directory **outside the keyline checkout**.
     There the root `CLAUDE.md` ("You implement") is not loaded, and no dev-installed
     keyline can shadow `lib/`.
   - Record the working directory, the skill path, the zip's sha256 and where
     `keyline` imports from.
   - This session then copies the outputs into `examples/bonsaihub/`.
8. **T-48 (hygiene), moved before T-43:**
   - extend `test_ac12_hygiene.py` from `fixtures/` to `examples/**` and `skill/**`;
   - use an allow-list for core properties (creator, lastModifiedBy);
   - Tyler reads the slide text of the surface decks at T-47, because the agent on
     claude.ai knows the account holder's name.
9. **Reference sizes:** `craft-floor.md` is read before every build, so give each
   reference a line cap in its test, and each rule id its own heading.

## 5. Auditor's own errors this round

1. B-22 item 4 and B-25 item 5 were hand-written character lists. A third character
   slipped through (FX-33). I should have asked for measured data from the start, as
   B-26 does.
2. B-25 item 2 covered top and left overhang but not the right. The right edge was
   left to the 0.99 margin, which does not scale with large type (FX-32).

## Amendment to append (verbatim)

- **B-27 (2026-10-09, audit 07).**
  1. U+2212 MINUS SIGN joins B-25's measured set. The tables, the numeral set and the
     measurements are regenerated (Q-53).
  2. A line's estimated width also includes max(0, the last glyph's ink right − its
     advance), taken from the twin. The fit tables store each glyph's right reach.
  3. The no-break-before and no-break-after sets of B-22 item 4 and B-25 item 5 are
     **measured**, not listed.
     - `measure_lo.py` probes every non-letter character of the measured set, in both
       line conditions, on each LibreOffice version measured.
     - The union over the versions is committed as data, and a test re-derives it.
  4. Kerning pairs are looked up across default-ignorable code points.
  5. `missing_glyph_em` and `missing_line_em` take the largest value measured in any
     environment Tyler or the auditor has run, and each environment is recorded with
     the data.
