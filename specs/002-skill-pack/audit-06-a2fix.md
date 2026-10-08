# Audit 06 of spec 002: the A2 fix round (FX-16 … FX-24)

- **Audited:** branch `002-skill-pack` at `1dd6216`, fresh clone, 2026-09-30, on
  LibreOffice 24.2.7.2 with all six metric twins installed.
- **Auditor:** the external session. **Decides:** Tyler.
- **Verdict: FX-16 … FX-24 ACCEPTED.** The pen now writes exactly what it estimates.
  AC-13(b) per B-24 passes on 24.2, as it does on 26.8.
- **Then a last, bounded fix round (FX-25 … FX-31).** A new adversarial pass found
  gaps, and two of them sit inside the pen's working set:
  - tall Vietnamese capitals overflow the top edge;
  - positive kerning is not counted.

  The rest are scripts the fit was never measured on.
- **B-25 names the set the fit guarantees cover, so audits of the estimator
  converge.** Outside that set the pen warns and stays conservative, but promises
  nothing.
- **After FX-25 … FX-31, write Phase B's tasks and stop once,** for one combined audit.

## 1. What was checked

| check | result |
|---|---|
| Identity | 17 commits, all `Tyler <code@tyler-void.dev>`, one Claude trailer each |
| Docs | spec: +46 lines (B-22 … B-24), 0 removed; decisions, lessons, constitution unchanged |
| Hashes | product `9b0fea6e…`, oracle `af534e21…`; audit 05 and its repro folder identical to the auditor's |
| Fixtures | 28 files rebuilt, all spec 002 fixtures; goldens untouched. Zip by zip: the 10 rule fixtures and the 7 A1 drift decks changed only in their layouts, and the 7 pen-built drift decks and 3 specimens in layouts and slides, as FX-24 requires. `expect.toml` still passes |
| ruff | clean, 193 files |
| pytest (24.2) | **1103 passed, 8 skipped, 0 failed.** The skips: 6 fit-table provenance checks (a different Liberation build here), engine selection, non-root |
| M1 baseline | no differences |
| Regression | main vs branch: 308 pairs, 0 differing, 0 tracebacks |
| `fit_stress.py` (24.2) | **PASS:** 642 texts, 0 past a limit. Per edge: left +2.7 px (allowance 1.9 px), top −2.3, right +0.7, bottom +0.7. These equal the 26.8 maxima; individual ink boxes differ by 1–2 px |
| `measure_lo.py` (24.2) | (a) holds, (b) holds, (d) holds (widest fallback 1.4798 em); **(c) FAILS**, see FX-31 |

Both outputs are in `audit06-repros/`.

### The deviations and premises, ruled

- **Deviation A (row allowance): accepted.** Measured.
- **Deviation B (descent room): accepted.** It was a real gap, exposed by FX-24.
- **Deviations C, D and E: accepted.**
- **Where Claude Code corrected audit 05:**
  - `body-too-small` is a warning, not an error. My mistake.
  - LibreOffice keeps 10 of the 15 characters with the word before only when the
    space fits. Audit 05 stated the UAX #14 rule as absolute.

  Both corrections stand; neither changes a fix.
- **The contact sheets after FX-24:**
  - evidence titles sit on the rule;
  - the cover and close titles sit on their lede;
  - the statement slide keeps its deliberate emptiness.
  - The descent room keeps descenders clear of the rule.
  - The soul verdict is still Tyler's at G-1.

## 2. New findings

A separate adversarial agent attacked the fix round. It had not seen this audit's
work. I re-ran every item below myself on 24.2. The scripts are in `audit06-repros/`.

### FX-25 · Major · Tall Vietnamese capitals leave the top edge

- **Cause:**
  - LibreOffice puts the first baseline 0.99 em below the box top.
  - Gelasio's stacked capitals reach 1.27 em (Ẩ), 1.17 em (Ẳ) and 1.10 em (Ỗ) above
    the baseline.
  - The estimator reserves room below the last line (Deviation B), but no room above
    the first line.
- **Measured (`t_top.py`, stock `field` voice), past the 2 px limit:**
  - statement title "Ẩn số": +18.5 px presented, +11.5 px read;
  - section title "Ẩm thực": +15.5 px;
  - quote title: +17.3 px;
  - lede and label: +4.5 … +6.9 px;
  - bottom-anchored two-line titles: evidence +14.6 px, cover +12.9 px (`t_top2.py`).
- **Why this counts as a real overhang, like the left edge.** Diacritics hang above
  the cap line as punctuation hangs in a margin. So the region box should not move
  down: moving it would lose cap-height alignment to the grid. But the overhang must
  never reach another box or the slide edge.
- **Fix (B-25):**
  - The top edge gets an allowance, like B-24's left edge: size × max(0, the highest
    glyph top among the text's characters − the first baseline). The first baseline is
    measured per line spacing: 1.00 em at 1.0, and 1.12 em at 1.1.
  - A **pack invariant** test: for every region, every style allowed in it and every
    portable family, the largest such overhang over the measured set (B-25) is smaller
    than the free space above the region, measured to the region or keyline rule above
    it, or to the slide edge. The same holds for the left edge.
  - If the Swiss pack fails the invariant, report it; region changes are Tyler's call.
  - `fit_stress` gains Vietnamese texts, stacked capitals included.

### FX-26 · Major · Positive kerning makes text wider than its advances

- §6.4 ignores kerning on the assumption that it only tightens. It does not.
  - Carlito has 6,639 positive pairs, for example V+ĩ and T+ĩ at +0.063 em.
  - Caladea has f+’ at +0.083 em.
- **Measured (`t_kern.py`):**
  - repeated "Vĩ Tĩ" in Calibri: the statement title ends +74.6 px past its bottom
    (one line more than estimated);
  - "staff’s" in Cambria: body +24.8 px.
  - A realistic list of province names held.
  - Vietnamese in a Calibri voice is exactly the case Tyler's decks will hit.
- **Fix (B-25):** a word's width is its advances plus the sum of its **positive**
  kerning pairs, for pairs inside the measured set. The fit tables store those pairs.
  Negative pairs stay ignored, which is conservative.

### FX-27 · Minor · No break after an opening bracket and a space (UAX #14 LB14)

- LibreOffice keeps `( ` `[ ` `{ ` `¿ ` `¡ ` `„ ` with the next word; the estimator
  breaks after them.
- It also keeps the fullwidth closers `！ ？ ， 。 」 ）` with the word before.
- **Measured (`t_break.py`):** the pen accepts 2 lines, LibreOffice sets 3, and the
  bottom-anchored title's first line is clipped at the slide's top edge.
- **Fix:** extend B-22 item 4:
  - a piece ending in an opening punctuation mark joins the piece after it, even across
    a space;
  - the fullwidth closers join the no-break-before list;
  - test each character in LibreOffice, in both line conditions.

### FX-28 · Minor · CJK in a table cell sets a taller line (24.2)

- In cells, LibreOffice 24.2 sets a line containing CJK at the East Asian fallback
  font's line height, about 1.42 em. Text boxes held at 1.2.
- **Measured (`t_table.py`):** the longest table the pen accepts ends +46.8 px past
  `main` (Arial, presented), into the footer.
- **Fix:** in a table cell, a line that contains a missing glyph uses `missing_line_em`.
  It is measured like `missing_glyph_em`: data, stored with the LibreOffice version.

### FX-29 · Minor · Hebrew is measured in the twin but set in another font

- The theme leaves `<a:cs typeface=""/>` empty, so LibreOffice sets Hebrew in its
  default CTL font, while the estimator uses the twin's Hebrew widths.
- **Measured (`t_ctl.py`):** Times New Roman statement title +90.6 px; Arial, read,
  +52.6 px.
- **Fix:**
  - The templates set the theme's `cs` font, major and minor, to the voice's display
    and text families, as they do for `latin`. PowerPoint then sets complex scripts in
    the voice's family too.
  - Hebrew and Arabic stay outside the measured set (B-25), so the pen warns.

### FX-30 · Minor · Chart series are checked late

- **Repro (`t_chart.py`):** `nan`, `inf` and `series = []` pass the evidence loader and
  `chart_bar()`. `save()` then fails and the deck is lost. An integer above 1e308 makes
  `chart_bar()` raise a raw `OverflowError`.
- **Fix:** a series is non-empty, and every value is finite and representable as a
  float. This is checked when the evidence loads, and again at the verb (FX-20's rule).

### FX-31 · Minor · `measure_lo` criterion (c) fails on 24.2

- Georgia table cells at 14 pt bold measure 17.915 pt against the 17.830 pt bound; the
  worst excess is 0.14 pt, about 0.05 mm. At 48 pt it is 0.0075 pt.
- 24.2 rounds cell lines more coarsely than 26.8.
- `fit_stress` still passes, because 6 rows × 0.14 pt stays under 2 px.
- **Fix (B-22 item 7):**
  - The per-line cell allowance becomes the largest excess measured on any version,
    rounded up to 0.01 mm. On 24.2 that is 0.05 mm.
  - It is stored as data with the versions it covers.
  - Criterion (c) then holds on both versions.

### Also found

- **Invisible-only text** (`" "`, ZWJ, U+2061, VS16, LRM) is accepted as a headline,
  a text or a source. This is trivial; it goes into FX-30's commit.
  - **Fix:** every text needs at least one character of category L, M, N, P or S.
- **Box-drawing characters** (U+2502, 0.303 em below the baseline) poke 4.7 px below a
  bottom-anchored title.
  - They are outside the measured set, so the pen warns and there is no fix.

### Held under attack

- **Normalization:** NFD Vietnamese at the limit; U+3000 and U+2003 collapse to a
  space; the ligature characters ﬁ and ﬂ; hyphens, en dashes and U+2011 compounds.
- **Break units:** opening quotes followed by a space; Arabic punctuation;
  `… — ‐ ‼ › ⁄`.
- **Transactions:** 300 random seeds, about 2,900 refusals. The state was identical
  after every refusal, and `save()` was byte-identical to a replay of only the accepted
  calls.
- **B-23 invariant:** kitchen-sink decks carrying noncharacters, private-use and bidi
  controls, ZWJ emoji and `]]>` gave 0 error-level findings and passed
  `officecli validate`.
- **The right edge** never went past 2 px.

## 3. Rulings on Q-50 and Q-51

| Q | Ruling |
|---|---|
| 50 | **One value.** `missing_glyph_em` stays one conservative number (1.49 em). Missing glyphs already trigger the "not faithful" warning, and over-counting only costs space in decks the fit does not promise to measure (B-25). Per-script values can come in spec 003, with script coverage per voice |
| 51 | **Keep the set, and name it.** The descent set becomes B-25's measured set, so the descent room, the ascent allowance (FX-25) and the kerning pairs (FX-26) all use one definition. A fixed per-font room keeps bottom-anchored titles on one baseline across slides, which matters more than 4–5 pt |

## 4. Why this is the last estimator round

Each adversarial pass finds new scripts, because the space of characters has no end.
B-25 turns "fit is conservative" into a claim with a stated domain (principle IV):

- **Inside the set:** measured, guaranteed and audited.
- **Outside it:** the pen still estimates conservatively and warns, and promises
  nothing.

The next audit re-runs this round's repros and `fit_stress` on 24.2. It does not
reopen the estimator for scripts outside the set.

## 5. Auditor's own errors this round

1. Audit 05 called `body-too-small` error-level. It is a warning.
2. Audit 05 stated UAX #14 LB13 as absolute. LibreOffice applies it only when the
   space fits.
3. B-24 gave the left edge an allowance but not the top. Tall Vietnamese capitals are
   the same kind of overhang, and I did not think of them. That matters for Tyler's
   own language.

## Amendment to append (verbatim)

- **B-25 (2026-09-30, audit 06).** The measured set, and overhang.
  1. **The measured set.**
     - It covers Basic Latin, Latin-1 Supplement, Latin Extended-A, Latin Extended-B,
       Latin Extended Additional (Vietnamese included), General Punctuation, Currency
       Symbols and ASCII digits, minus the characters B-22 refuses.
     - §6.4's fit guarantees, AC-13(b) and B-24 apply to text inside this set.
     - For any character outside it, the pen still estimates conservatively and prints
       one warning per deck, which names the characters. Nothing more is promised
       there.
  2. **Overhang allowances.** AC-13(b)'s top edge gets an allowance like B-24's left
     edge: size × max(0, the highest glyph top among the text's characters − the first
     baseline), taken from the twin. The first baseline is measured per line spacing.
     B-24's left edge is unchanged.
  3. **Pack invariant.** For every region, every style allowed in it and every portable
     family, the largest top and left overhang over the measured set is smaller than
     the free space beside the region: the gap to the region or keyline rule next to
     it, or to the slide edge.
  4. **Kerning.** A word's width is its advances plus the sum of its positive kerning
     pairs inside the measured set. Negative pairs are ignored.
  5. **Break units.** B-22 item 4 extends to UAX #14 LB14. A piece that ends in an
     opening punctuation mark joins the next piece, even across a space. The fullwidth
     closers `！ ？ ， 。 」 ）` join the no-break-before list.
  6. **Measured cell data.**
     - In a table cell, a line that contains a missing glyph uses `missing_line_em`.
     - Each cell line has an allowance equal to the largest excess measured on any
       LibreOffice version, rounded up to 0.01 mm.
     - Both are data, stored with their versions.
  7. **Complex scripts.** The templates set the theme's `cs` fonts to the voice's
     display and text families.
