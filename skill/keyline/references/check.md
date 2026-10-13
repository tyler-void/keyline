# Reading the check

`kl.py check DECK.pptx --brief BRIEF.toml` lints the deck, compares it with its brief,
validates the file when OfficeCLI is present, and renders a contact sheet when it can
(`-o DIR` chooses where). `kl.py brief BRIEF.toml` checks the brief alone.

- **Exit code:** 0 is clean; 2 means at least one warning or error; 1 means the file
  could not be read.
- **A finding** is one line: `slide N · rule-id · severity · shape · what was measured`.
  With `--json` the same findings come on stdout.
- **Severity:** fix every `error` and `warning`. An `advisory` is a hint: read it, and
  decide.
- **One round.** Apply all your fixes in one batch, rebuild, and check once more. Report
  what remains; do not loop.
- **Fix the source.** For a deck you built, change the brief or the build script, never
  the `.pptx`. For someone else's deck, describe the fix in their terms.

## Recipes

One per rule that reports a warning or an error.

### accent-overuse

More accent-coloured elements on a slide than the pack's budget. Keep the one that
carries the point: drop `accent=True` from the figure, or the `highlight` from the
chart.

### body-too-small

Body text below the mode's minimum size. The pen cannot write it. In another deck, raise
the size and cut words until it fits, or move the deck to read mode if it is meant to be
read alone.

### brief-headline

A slide's title is not its brief headline. Change the headline in the brief and rebuild;
do not retitle the slide in the build script.

### brief-headline-long

A headline has more words than the mode allows. Rewrite it as a shorter claim. If it
needs two clauses, it is two slides.

### brief-mood

An `own_world` item is only mood words. Replace it with a thing from the subject's
world: an object, a place, a material.

### brief-notes

A presented statement, evidence, quote or close slide has no notes. Write what the
speaker says while the slide is up, in the slide's `notes`.

### brief-reads

A slide has more reads than the mode allows. Split it: each slide takes the reads that
belong to one claim.

### brief-role

A slide's role is not the one in its brief, or it has none. Build with `next()`, which
takes the role from the brief. A slide made outside the pen has no role.

### brief-slide-count

The deck and the brief have different numbers of slides. Call `next()` once per brief
slide, and never `add()` on a brief's deck.

### claude-look-palette

Cream paper on most slides with a terracotta accent. Change the voice: a neutral or
clearly coloured paper, and an accent that is not rust or terracotta.

### closing-cliche

The last slide is "Thank you", "Questions?" or similar. Make the close say what to do
next, in words that answer the motif.

### dead-band

A wide empty band on an evidence slide. Give the main region its content: the table, the
chart, or a paragraph. If the slide has one sentence to say, make it a statement slide.

### edge-margin

A shape sits closer to the slide's edge than the margin. The pen's regions keep the
margin. In another deck, move the shape inside it.

### equal-card-row

Three or more equal filled boxes in a row, each with text. Say it another way: a table
when the items share columns, one figure and a sentence when one number matters.

### fiction-undisclosed

The product is fictional and neither the first nor the last slide says so. Call `note()`
on the cover or the close: without text it writes the evidence file's disclosure.

### font-count

More font families than the limit. A voice has two at most. In another deck, keep one
family for titles and one for text.

### notes-missing

A content slide has no speaker notes (a warning in presented mode). Put the notes in the
brief; `next()` applies them.

### off-pack-font

A font that is not one of the voice's. The pen writes only the voice's families, so the
deck was edited afterwards, or checked with the wrong voice. Rebuild, or pass the right
`--brief`.

### off-palette-color

A colour that is not in the voice's palette. Same cause and same fix as `off-pack-font`.

### off-scale-size

A text size that is not on the pack's scale. Same cause and same fix as
`off-pack-font`. If text was shrunk by hand to fit, restore the style and shorten the
text.

### off-slide

Text, a table or a chart reaches past the slide's edge. The pen's regions cannot. In
another deck, move or resize the shape.

### ooxml-invalid

OfficeCLI's validator found a schema error in the file. A deck from the pen should have
none: report it, with the message. In another deck, re-save it from PowerPoint.

### source-missing

A slide shows evidence and has no source line. Call `source()` on that slide.

### text-contrast

Text too close in colour to its background. With the pen this comes from the voice: see
`voice-contrast`. In another deck, darken the text or lighten the background.

### title-not-dominant

The title is not clearly larger than the body text. The pack's scale keeps the ratio. In
another deck, enlarge the title or reduce the body, within the mode's minimum.

### title-too-long

The title has more words than the mode allows. Same fix as `brief-headline-long`.

### title-underline

A short accent bar sits just under the title. Remove it. The pen has no such shape; its
keyline spans the full width.

### unsourced-number

A significant number on a slide is not in that slide's brief evidence. Either add an
evidence entry with a source and list its id on the slide, or remove the number. If the
deck writes the value another way ("62 percent"), add that form to the entry's
`aliases`.

### voice-claude-look

The voice has cream paper and a terracotta colour. Move the paper toward a neutral or a
clear tint from `own_world`, or the accent away from rust. Keep the `why` lines true.

### voice-contrast

A text colour of the voice is below the contrast floor on a surface. The message names
the pair and the ratio. Darken or lighten that colour until it passes. The pen refuses
to build with this error.

### voice-why

An inline voice has no `why` line for a palette role. Add one line per role that names
the thing in `own_world` the colour comes from.

## Advisories

- `adapter-unresolved`: a property could not be read, and rules that need it skipped it.
- `box-overlap`: two text boxes intersect. Boxes, not ink: look at the preview.
- `brief-no-statement`: a long presented brief has no statement slide. Consider one.
- `unsupported-content`: content the linter does not read, such as SmartArt or table
  text. On a table, "table text is not read" is expected.

## What the pen reports

The pen speaks before `check` does. `pen.md` has the details.

- **`DoesNotFit`:** the text needs more lines than its region holds. Shorten or split.
- **Refused characters (B-22):** controls; line breaks in a one-line text; the invisible
  break characters U+00AD, U+200B, U+2060 and U+FEFF; noncharacters and lone surrogates.
- **Text with no visible character** is refused too.
- **The numeral set (B-26):** a figure's value takes digits, signs and unit words. The
  refusal names the character; move it to the label.
- **`keyline pen: warning:`** means the fit does not cover some characters of the deck.
  See *Known limits*.

## Known limits

Say these in the report when they apply.

### Numbers

`unsourced-number` compares number tokens, not meanings.

- Units are not compared: "38 days" matches "38 years".
- A space as a thousands separator is not read. "24/7" gives "24".
- "27 September 2026" gives a significant "27". "v2.0.1" gives "2.0.1". "3 × 4" gives
  "3×". "$-5" gives "-5".
- "B2B" gives "2B", "4K" gives "4K", "COVID-19" gives "19", "iPhone 15" gives "15".
- "5 %" with a no-break space gives a "5" that is not significant: only a plain space
  joins the "%".
- A source line inside a table cell is not recognised: table text is scanned whole.
- A "Source: " run counts as a source line even when its fill makes it invisible. The
  check targets accidents, not someone gaming it.

### Fonts and coverage

The pen measures with a metric twin of each portable family. A letter the twin lacks is
set in a fallback font, and nothing is promised for it.

<!-- gen:begin coverage -->
| Family | Metric twin | Letters it lacks, of 709 | Vietnamese letters it lacks, of 134 | Signs it lacks, of 176 |
|---|---|---|---|---|
| Arial | Liberation Sans | 9 | 0 | 52 |
| Times New Roman | Liberation Serif | 9 | 0 | 52 |
| Courier New | Liberation Mono | 10 | 0 | 53 |
| Georgia | Gelasio | 85 | 0 | 61 |
| Calibri | Carlito | 9 | 0 | 52 |
| Cambria | Caladea | 442 | 88 | 77 |

Every Vietnamese letter: Arial, Times New Roman, Courier New, Georgia, Calibri.

Cambria lacks these Vietnamese letters: ơ ư ả ạ ằ ắ ẳ ẵ ặ ầ ấ ẩ ẫ ậ ẻ ẹ ề ế ể ễ ệ ỉ ị ỏ ọ ồ ố ổ ỗ ộ ờ ớ ở ỡ ợ ủ ụ ừ ứ ử ữ ự ỷ ỵ Ơ Ư Ả Ạ Ằ Ắ Ẳ Ẵ Ặ Ầ Ấ Ẩ Ẫ Ậ Ẻ Ẹ Ề Ế Ể Ễ Ệ Ỉ Ị Ỏ Ọ Ồ Ố Ổ Ỗ Ộ Ờ Ớ Ở Ỡ Ợ Ủ Ụ Ừ Ứ Ử Ữ Ự Ỷ Ỵ.
<!-- gen:end -->

- For Vietnamese text, use a family the table shows with no Vietnamese letter missing.
- Outside the measured set (Latin letters, general punctuation, currency signs and the
  minus sign) the pen estimates on the safe side, warns once per deck, and promises
  nothing. The preview may set those characters in another font.
- Fonts are not embedded. The deck needs the voice's families, or their twins, on the
  machine that opens it.
- The preview is LibreOffice's or OfficeCLI's. Its line breaks can differ from
  PowerPoint's.

### Numerals

A figure's value cannot use these characters:

<!-- gen:begin numeral-excluded -->
| Why | Count | Characters |
|---|---|---|
| It would rise above the region | 33 | Ǖ (U+01D5) Ǘ (U+01D7) Ǚ (U+01D9) Ǜ (U+01DB) Ǟ (U+01DE) Ǡ (U+01E0) Ȫ (U+022A) Ȭ (U+022C) Ȱ (U+0230) Ḕ (U+1E14) Ḗ (U+1E16) Ḯ (U+1E2E) Ṍ (U+1E4C) Ṏ (U+1E4E) Ṑ (U+1E50) Ṓ (U+1E52) Ṥ (U+1E64) Ṧ (U+1E66) Ṹ (U+1E78) Ṻ (U+1E7A) Ấ (U+1EA4) Ẩ (U+1EA8) Ẫ (U+1EAA) Ắ (U+1EAE) Ằ (U+1EB0) Ẳ (U+1EB2) Ẵ (U+1EB4) Ế (U+1EBE) Ể (U+1EC2) Ễ (U+1EC4) Ố (U+1ED0) Ổ (U+1ED4) Ỗ (U+1ED6) |
| It would reach left of the region | 4 | Ɲ (U+019D) Ȉ (U+0208) ȉ (U+0209) ⁄ (U+2044) |
<!-- gen:end -->

### Determinism

The same build script gives the same bytes with python-pptx 1.0.2. Other versions are
not tested.
