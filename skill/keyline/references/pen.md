# The pen

The pen is the only way to put content on a slide. You give it text, evidence ids and
names from the pack. It gives you a `.pptx`, or it refuses and says why. It never
shrinks text, and it takes no size, colour or position.

## A build script

```python
from keyline.pen import Deck

deck = Deck.from_brief("deck.brief.toml")
deck.next().text("A tool library that repairs what it lends.", style="lede")
deck.next().text("Members come back for the bench, not the shelf.", style="lede")
deck.next(variant="figure").figure("returns_repaired").text(
    "Six in ten returned tools go to the bench before the next loan.", region="side"
).source()
deck.next().chart_bar("repairs_by_month", highlight="Jun").source()
deck.next().text("Fund the second bench.", style="lede")
deck.save("deck.pptx", author="Tyler")
```

Run it with `kl.py run build_deck.py`. One `next()` per brief slide, in order. Every verb
returns the slide, so calls chain. When the pen refuses, `kl.py run` prints one line,
such as `build_deck.py:7: DoesNotFit: text needs 6 lines, region holds 3`, and exits 1.

## The deck

### `Deck.from_brief(path)`

The brief's mode, pack, voice and evidence. This is the form to use.

### `Deck(pack, mode, voice, evidence=None)`

A deck without a brief. `voice` is a voice name of the pack or a voice file; `evidence`
is one evidence file or a list. Use `add()` with it. Such a deck has no spine, and
`check` cannot compare it with a brief.

### `next(variant=None)`

The next brief slide: its role, headline and notes are already applied. It refuses when
the brief has no more slides, and on a deck that has used `add()`. If the headline does
not fit its title, the refusal names the slide: "slide 10 (close): headline needs 3
lines, region holds 2". Shorten that headline in the brief.

### `add(role, headline, notes=None, variant=None)`

A slide without a brief entry. Only for `Deck(...)`.

### `save(path, author="")`

Writes the deck. The file appears whole or not at all. The same script gives the same
bytes (with python-pptx 1.0.2). If the fit does not cover some characters, it prints one
`keyline pen: warning:` line; see *The coverage warning* below.

## Layouts and regions

A role has a default layout, and some have a variant. Each verb fills one region, and a
region holds one thing. The title region is filled by the headline; the footer takes
only `source()` and `note()`.

<!-- gen:begin layouts -->
| Role | Layout | Regions |
|---|---|---|
| `cover` | default | `title`, `main`, `footer` |
| `section` | default | `title`, `main` |
| `statement` | default | `title`, `main`, `footer` |
| `evidence` | default | `title`, `main`, `footer` |
| `evidence` | `variant="figure"` | `title`, `main`, `side`, `footer` |
| `quote` | default | `title`, `main` |
| `close` | default | `title`, `main`, `footer` |
<!-- gen:end -->

## The verbs

Which verb, and which style, a role allows is in the *roles* table of `craft-floor.md`.

### `text(content, style="body", region="main")`

A block of text. Pass the style the role allows: `lede` on a cover, a statement or a
close; `label` on a section. `\n` in `content` starts a new paragraph.

### `bullets(items, region="main")`

A list of strings. The slide's bullets together stay within the mode's limit.

### `figure(evidence_id, region="main", label=None, accent=False)`

An evidence `value` as a large numeral, with its label under it. `label` defaults to the
evidence label. `accent=True` sets the numeral in the accent, and spends the slide's
accent. A `series` entry is refused: use `chart_bar`. The numeral takes only the
numeral set; see below.

### `table(rows, header=True, region="main")`

Rows of strings, all the same length. Hairlines, no fills. Header cells are labels, so
each stays within the caption word limit. An empty body cell is allowed.

### `chart_bar(evidence_id, region="main", highlight=None)`

A column chart of a `series` entry. `highlight` names one category to set in the accent,
and spends the slide's accent. A `value` entry is refused: use `figure`.

### `image(path, region="main", *, alt)`

A PNG, JPEG, GIF, BMP or TIFF, fitted inside the region without cropping. `alt` is
required: say what the picture shows.

### `attribution(text)`

Who said the quote, on a quote slide. A label: it stays within the caption word limit.

### `source(text=None)`

The source line. Without `text` it joins the sources of the slide's brief evidence. One
per slide.

### `note(text=None)`

The note line. Without `text`, on a cover or a close, it writes the product's
disclosure. One per slide.

### `notes(text)`

Speaker notes. `next()` already applies the brief's notes; call this only to replace
them. `\n` starts a new paragraph.

## When the pen refuses

A refused verb leaves the slide exactly as it was, so you can correct the call and go
on. There are two kinds of refusal.

### `DoesNotFit`

The text needs more lines than its region holds at its style's size. The message gives
both numbers.

- Shorten the text, or split the slide in the brief.
- Move detail to the notes, or to a table on its own evidence slide.
- Never look for a smaller style. The scale is fixed.
- "the word … is wider than its region": break the word up, or reword. A phrase joined
  by no-break spaces counts as one word.

### `PenError`

Everything else. The message names the value and the rule. The common ones:

| Message says | Change |
|---|---|
| role … does not allow … | Use a verb the role allows (`craft-floor.md`, *roles*). |
| style … is not allowed for … | Pass the style the role allows for that verb. |
| layout … has no region … | Use a region of that layout, or ask for the variant. |
| region … already holds a component | One verb per region. |
| … has N words; at most … | A label, header cell or attribution is a caption. Shorten it. |
| N bullets on this slide; at most … | Fewer bullets, or two slides. |
| figure N; at most … per slide | One figure on a presented slide. |
| … would be accent N; the budget is … | Remove `accent=True` or the `highlight`. |
| unknown evidence id … | Add the entry to an evidence file, and to the slide's `evidence`. |
| … contains U+…, which the pen refuses | See *Characters* below. |
| … has no visible character | The text is only spaces or invisible characters. |
| the pen refuses this voice: … | Fix the voice in the brief (`check.md`, `voice-contrast`). |

### Characters

The pen writes exactly the text it measured. It first normalizes it: composed letters
(NFC), every run of spaces as one space, none at the ends. It refuses, naming the code
point:

- **controls:** tabs and other control characters;
- **line breaks:** every line-break character, in a one-line text. `text()` and `notes()`
  accept `\n` between paragraphs, and nothing else;
- **invisible break characters:** the soft hyphen (U+00AD), the zero-width space
  (U+200B), the word joiner (U+2060) and the byte-order mark (U+FEFF);
- **noncharacters** and lone surrogates.

A no-break space stays, and keeps its two words on one line.

### The numeral set

A figure's numeral is the largest text on a slide, so a tall or wide glyph would leave
its region. The numeral takes digits, signs and unit words: `62%`, `−0.4%`, `$1.2M`,
`12 tỷ ₫`. It refuses these characters, and anything outside the measured set (below).
The message names the character and tells you to put it in the label.

<!-- gen:begin numeral-excluded -->
| Why | Count | Characters |
|---|---|---|
| It would rise above the region | 33 | Ǖ (U+01D5) Ǘ (U+01D7) Ǚ (U+01D9) Ǜ (U+01DB) Ǟ (U+01DE) Ǡ (U+01E0) Ȫ (U+022A) Ȭ (U+022C) Ȱ (U+0230) Ḕ (U+1E14) Ḗ (U+1E16) Ḯ (U+1E2E) Ṍ (U+1E4C) Ṏ (U+1E4E) Ṑ (U+1E50) Ṓ (U+1E52) Ṥ (U+1E64) Ṧ (U+1E66) Ṹ (U+1E78) Ṻ (U+1E7A) Ấ (U+1EA4) Ẩ (U+1EA8) Ẫ (U+1EAA) Ắ (U+1EAE) Ằ (U+1EB0) Ẳ (U+1EB2) Ẵ (U+1EB4) Ế (U+1EBE) Ể (U+1EC2) Ễ (U+1EC4) Ố (U+1ED0) Ổ (U+1ED4) Ỗ (U+1ED6) |
| It would reach left of the region | 4 | Ɲ (U+019D) Ȉ (U+0208) ȉ (U+0209) ⁄ (U+2044) |
<!-- gen:end -->

`kl.py brief` applies the same test to every evidence `value`.

### The coverage warning

The pen measures text with tables for the six portable families, over Latin letters
(Vietnamese included), general punctuation, currency signs and the minus sign: the
measured set. Outside it, or for a letter the voice's font lacks, the pen still
estimates, on the safe side, but promises nothing. `save()` then prints one line that
starts with `keyline pen: warning:` and lists the characters.

- A letter the font lacks: change the voice's family (`brief.md`, *Fonts*), and rebuild.
- A character outside the measured set: reword, or accept that the preview may set it
  in another font and check that slide by eye.
