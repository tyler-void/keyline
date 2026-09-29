# Audit 05 of spec 002: phase A2 (the fit estimator and the pen)

- **Audited:** branch `002-skill-pack` at `9813345`, fresh clone, 2026-09-29. The
  auditor's sandbox runs LibreOffice 24.2.7.2 with all six metric twins installed.
- **Auditor:** the external session. **Decides:** Tyler.
- **Verdict: FIX, then G-1 and Phase B.**
  - The pen's architecture holds: token-only API, writer isolation, determinism,
    validity, the voice refusal, and core purity.
  - But the estimator and the writer do not see the same text. Common inputs are
    accepted and then overflow in LibreOffice: a `\n` in a headline, double spaces
    after a full stop, tabs.
  - Table cells in the Georgia voice overflow on LibreOffice 24.2.
  - Eight fix items (FX-16 … FX-23), amendments B-22 … B-24, and rulings on
    Q-47 … Q-49.
  - The PowerPoint part of G-1 can run now. The title-anchor question below should be
    settled with it.

## 1. What was checked

| check | result |
|---|---|
| Identity | 18 commits, all `Tyler <code@tyler-void.dev>`, one Claude trailer each |
| Docs | spec: +14 lines (B-21, verbatim), 0 removed; decisions, lessons, constitution unchanged |
| Hashes | product `9b0fea6e…`, oracle `af534e21…`; audit 04 and its three evidence files identical to the auditor's |
| Fixtures | 17 files, all new: pen drift decks, specimens and their briefs, fit strings. No existing fixture or golden changed |
| Older tests | only FX-3 and FX-11 changed, adding a `sleep` skip (report finding 4) |
| Dependencies | runtime still `lxml` and `Pillow`; python-pptx sits in the `pen` extra |
| ruff | clean, 183 files |
| pytest (24.2) | **854 passed, 1 failed, 8 skipped, 1 xfailed, 3 xpassed** (details below) |
| M1 baseline | no differences |
| Regression | main vs branch: 308 pairs, 0 differing, 0 tracebacks |

- **The failure is AC-13(b)'s own "edges the estimator decides" test.** On 24.2, a
  presented `field` table ends 4.8 px below `main` (FX-18). Tyler's 26.8 run passed it.
- **Six of the skips** are the fit-table provenance check: this sandbox's Liberation
  build differs from Tyler's. The other two are the engine-selection and non-root
  tests, both known.
- **AC-11 holds across machines.** The specimen tests compare against the committed
  bytes, and they pass here, on another OS, another LibreOffice and other font builds.
  VERIFIED.

## 2. New findings

A separate adversarial agent attacked the pen. It had not seen this audit's work. I
re-ran every item below myself on 24.2 before listing it. The repro scripts are in
`audit05-repros/`, with a README.

### FX-16 · Blocker · The estimator and the writer see different text

- **Cause:** `fit.wrap()` splits with `str.split()`, so it collapses space runs, drops
  leading and trailing spaces, and treats `\t`, `\n`, `\r` and NBSP as breaks. The
  writer puts the raw string into `<a:t>`.
- **Accepted, then set past the title region** (presented, neutral, evidence; the
  title region ends at 163.7 pt):

  | input | pen | LibreOffice | lowest line past the region |
  |---|---|---|---|
  | `"x\t" * 40 + "x"` | accepted | 4 lines | +110 pt |
  | `add(role, "Line one\nLine two\nLine three")` | accepted | 3 lines | +64 pt |
  | the same with `\r` | accepted | 3 lines | +64 pt |
  | runs of 60 spaces | accepted | 3 lines | +53 pt |
  | 70 leading spaces | accepted | 2 lines, one word past | +53 pt |

- **Other cases:**
  - `text()` with `\r\n` line endings;
  - two spaces after each full stop, filled to the pen's limit: 3 of 12 presented
    cases run about 23 pt into the footer;
  - an NBSP-joined headline wider than the region is accepted, and LibreOffice breaks
    it mid-word, which §6.4 forbids.
- **Why this is a blocker.** A `\n` in a headline and double spaces are ordinary model
  output. The brief path refuses line breaks (B-17), but `Deck.add()` does not, and
  Phase B's skill calls the pen directly.
- **Fix (B-22 items 1–3).** One normalization function, used by the estimator and by
  the writer, so the pen writes exactly the text it estimated.

### FX-17 · Major · The wrap breaks where LibreOffice does not

- LibreOffice never breaks before `/` or closing punctuation, even after a space
  (UAX #14, LB13). The estimator does.
- **Repro:** `attack_uax14.py presented neutral evidence keyline:evidence "/"`. The
  headline `plan / district / ship / …` is accepted as 2 lines, and LibreOffice sets 3.
- **Fix (B-22 item 4):** no break before those characters, even after a space. Test it
  against LibreOffice with each character.

### FX-18 · Major · Table-cell line pitch is not 1.2 in every twin

- **Measured (`attack_table2.py`, 24.2, presented body in a table cell):** row pitch
  40.73 pt for Gelasio and 39.43 pt for Carlito, against 38.89 pt for the other four.
- **The rule that fits every measured row exactly (INFERRED from 12 data points):**
  - In table cells, LibreOffice uses max(1.2, the twin's hhea line height) em.
  - Gelasio's hhea is 1.2695 em and Carlito's is 1.2207 em. The other four are ≤ 1.15.
  - Text boxes stay at 1.2 for every twin (B-21, measured).
- **Consequence:** the longest `field` table the pen accepts ends 4.9 pt below `main`.
- **Gelasio matches Georgia's widths only.** Real Georgia's hhea is about 1.14. That
  figure is from memory and was not measured here, because Georgia is not installed.
  So PowerPoint is probably fine, but the check render is not.
- **Tyler's 26.8 run passed this table.** So either 26.8 lays table cells out
  differently, or the stress landed differently. The estimator must hold on both
  versions (B-22 item 7): Ubuntu 24.04 LTS ships 24.2.
- **Fix:**
  - The fit tables store each twin's hhea.
  - Table cells use max(1.2, hhea).
  - `measure_lo.py` adds a table-cell pitch criterion.
  - `fit_stress` covers all six families, through test-only voices, because inline
    voices may use any of them.

### FX-19 · Major · The maximum-advance rule is not a bound for a monospace twin

- Liberation Mono's maximum advance is 0.6 em, but CJK and emoji render about 1 em
  wide in the fallback font.
- **Repro:** `attack_fit2.py`, after `mkvoices.py`, with a Courier New voice in read
  body. 330 CJK words are accepted and end 82 pt below the region, cut off at the
  slide edge. Emoji: 69 words past the region.
- Arial and Calibri held, because their maximum advance is 1.33 em.
- **Fix (B-22 item 6):** a missing glyph counts as max(the table's maximum advance,
  `missing_glyph_em`). That value is measured on LibreOffice for CJK, emoji and Thai
  fallbacks, and stored as data with the version.

### FX-20 · Major · Late, untyped failures lose the whole deck

- **Repro (`attack_ctrl.py`):**
  - `add()`, `text()`, `table()` and `notes()` accept `\x00`–`\x1f` controls, U+FFFE
    and lone surrogates;
  - `save()` then raises a raw `ValueError` or `UnicodeEncodeError`, not `PenError`.
- **Repro (`attack_img.py`):**
  - `image()` accepts WebP, PPM, TGA and ICO, and `save()` fails the same way;
  - `save(author=)` fails the same way with 256 characters or a control character;
  - replacing an image file between `image()` and `save()` distorts it.
- **Fix (B-23):**
  - every input is checked at the verb that receives it;
  - images are limited to PNG, JPEG, GIF, BMP and TIFF, and read at call time;
  - `save()` raises only `PenError` and writes atomically: a temp file, then a rename.

### FX-21 · Major · A legal pen call can produce an error-level lint finding

- `text(style="label")` has no word cap. Seven words are accepted in both modes, where
  `attribution()` refuses the same words.
- `keyline lint --pack swiss` then reports `body-too-small`.
- **The invariant:** a deck built only through legal pen calls lints with no
  error-level finding.
- **Fix (B-23):**
  - The caption cap applies to every style below the mode's body minimum, mirroring
    lint's exemption.
  - Add a generated sweep: every role × allowed component × allowed style × mode ×
    stock voice. It asserts 0 error-level findings.

### FX-22 · Major · A refused verb destroys earlier content

- **Repro (`attack_state.py`, part b):**
  - `note()` succeeds;
  - a long `source()` raises `DoesNotFit`;
  - the retry with a short source raises "already has a source line";
  - the saved slide has neither the note nor the source.
- **Part c:** `text(region="footer")` is accepted in the body style, and a later
  `source()` deletes it without a word.
- **Fix (B-23):**
  - A refused verb leaves the slide exactly as it was.
  - The footer region takes only `source()` and `note()`.

### FX-23 · Minor · Loose flags, and `next()` after `add()`

- `figure(accent="#00FF00")` spends the accent, and `table(header="2cm")` is accepted.
  The flags must be `bool`.
- `next()` indexes the brief by the deck's slide count. So after an `add()`, it
  silently skips a brief slide (`attack_next.py`).
- `bullets()` in both `main` and `side` puts 8 bullets on one presented slide. §6.1's
  intent is per slide.
- **Fix (B-23).**

### Held under attack

- **Tokens:**
  - hex values and every unit are refused;
  - Unicode digits, uppercase and whitespace variants end as "unknown style/region";
  - non-string tokens raise `PenError`;
  - no python-pptx type goes in or out.
- **Voices:** a voice at 4.12 : 1 contrast is refused, both as a file and inline.
- **Refusals:** `numerals_max`, the accent budget, `series` in a figure,
  `EvidenceError`, a second component in one region, and the caption caps on
  attributions and header cells.
- **Determinism:** the same SHA-256 across TZ, LANG, PYTHONHASHSEED,
  SOURCE_DATE_EPOCH, the working directory, and two decks built in one process.
- **Validity:** `officecli validate` reports 0 errors, and lint 0 error-level findings,
  on six kitchen-sink decks (2 modes × 3 voices, with Vietnamese and XML
  metacharacters).
- **Fit:**
  - CJK and emoji in Arial and Calibri;
  - an NFD against an NFC tracked label;
  - stacks of short paragraphs;
  - bullets at the maximum count.

## 3. Rulings on Q-47 … Q-49

| Q | Ruling |
|---|---|
| 47 | **Amend AC-13(b), and keep checking the left edge (B-24).** The overhang is a glyph's side bearing, not a fit failure. But dropping the left edge would hide real indent bugs. So the left edge gets an allowance: the most negative left side bearing among the text's characters × size, computed in the test from the twin's TTF with fontTools, plus the 2 px. No fit-table data is needed. The other three edges stay at 2 px |
| 48 | **Drop the row rounding of the numeral box.** The numeral box is exactly one numeral line: size × 1.2 + 0.01 mm (B-21). The label box starts directly below. On presented statement and close, 144.03 + 16.83 = 160.86 pt fits in 23 rows (163.0 pt), so the pack does not change. This supersedes the row rounding in Q-43, which I accepted. The gap between the numeral and its label is then constant per mode. G-1 judges it |
| 49 | **Keep the wording.** The message "in M1" is part of M1's byte-identical output (the baseline and the 308 pairs). Change it in spec 004, when table text is read |

## 4. For G-1 (Tyler): what the contact sheets show

The PowerPoint checks (repair prompts, a new text box in `night`) do not depend on the
fixes. Run them now.

- **Titles are top-anchored in regions sized for two lines.**
  - Every slide is written with `anchor="t"`, and the spec says nothing about vertical
    anchoring.
  - So a one-line title leaves an empty band above the keyline rule or the lede.
  - This shows on presented slides 6 and 7, and on 7 of 9 `field` (read) slides:
    cover, statement, the four evidence slides, and close.
  - In a Swiss layout, the title usually **sits on** the rule, or on the lede.
  - **Proposal:** an `anchor` per region in `pack.toml`. It is data, and it does not
    touch the fit.
    - `b` for the cover, evidence and close titles;
    - `t` for everything else, including the statement slide, where the emptiness is
      the point.
  - If you agree, it goes into FX-24 and the specimens are rebuilt.
- **Section slides invert** (light in `night`, dark in `neutral` and `field`). This
  was intended in B-8.10.
- **Otherwise the discipline shows:**
  - one accent per slide;
  - the rule on every evidence slide;
  - a source on every evidence slide;
  - a quiet chart with one highlighted bar;
  - the disclosure note on the close.
- **The soul verdict is yours** (principle VIII).

## 5. Auditor's own errors this round

1. B-21 measured pitch in text boxes only, and I wrote "every twin". Table cells
   follow the font's hhea (FX-18).
2. I accepted Q-43's row rounding without checking it against the smallest region
   that allows a figure (Q-48).
3. My 420-case stress in audit 04 built its own boxes rather than going through the
   pen. So it could not see FX-16 or FX-17.

## Amendments to append (verbatim)

- **B-22 (2026-09-29, audit 05).** The fit estimator and the writer see the same text.
  1. **One normalization, before both estimate and write:**
     - NFC;
     - runs of space separators (category Zs, except U+00A0, U+202F and U+2007)
       become one U+0020;
     - leading and trailing spaces are removed.
  2. **Paragraphs and line breaks.**
     - `\n` separates paragraphs only in `text()` and `notes()`.
     - Every other string is one line and refuses B-17's line-break set: headlines,
       labels, cells, source, note, attribution and bullet items.
  3. **Refused everywhere,** as `PenError` naming the code point:
     - C0 and C1 controls (except `\n` where item 2 allows it) and tab;
     - U+FFFE, U+FFFF and lone surrogates;
     - the invisible break controls U+00AD, U+200B, U+2060 and U+FEFF.

     U+00A0, U+202F and U+2007 join words: the estimator treats a joined run as one
     word, so §6.4's "a single word wider than the region does not fit" applies to it.
  4. **No line break before** `) ] } , . : ; ! ? / % ‰ » ” ’`, even after a space
     (UAX #14, LB13). The estimator keeps them with the preceding word.
  5. **Table cells:** pitch = size × max(1.2, the twin's hhea line height) × line
     spacing + 0.01 mm. The fit tables store the hhea value. Text boxes keep B-21's 1.2.
  6. **Missing glyphs:** a character missing from the twin's table counts as
     max(the table's maximum advance, `missing_glyph_em`). That value is data in
     `thresholds.toml`, measured on LibreOffice (CJK, emoji and Thai fallbacks) and
     recorded with the version.
  7. **Versions.** Fit constants must hold on every LibreOffice version that Tyler or
     the auditor has measured: now 24.2.7.2 and 26.8.0.3. Where the versions differ,
     the estimator takes the larger value.
- **B-23 (2026-09-29, audit 05).** Pen state and inputs.
  - A refused verb leaves the slide exactly as before.
  - The footer region takes only `source()` and `note()`.
  - Flags (`accent`, `header`) must be `bool`.
  - On a deck made from a brief, `next()` after `add()` is a `PenError`.
  - `bullets_max` counts per slide.
  - The caption cap (`caption_exempt_words`) applies to every style whose size is below
    the mode's body minimum, as lint's exemption does.
  - Images are PNG, JPEG, GIF, BMP or TIFF, read when `image()` is called.
  - `save()` validates `author`, writes atomically, and raises only `PenError`.
  - **Invariant:** a deck built only through legal pen calls lints with no error-level
    finding. This is tested by a generated sweep.
- **B-24 (2026-09-29, audit 05).** AC-13(b) judges the right, top and bottom edges at
  2 px.
  - The left edge is judged at 2 px plus the most negative left side bearing among the
    text's characters × size, taken from the twin.
  - The stress covers all six portable families.
  - It runs on every LibreOffice version available: Tyler's 26.8.0.3, and the
    auditor's 24.2.7.2 at audit time.
