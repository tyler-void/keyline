# The brief

A brief is the deck before it has a look: who it is for, what it claims, and one line
per slide. Two TOML files hold it. `kl.py brief <deck>.brief.toml` validates both and
prints the spine. Fix recipes for its findings are in `check.md`.

## The evidence file

Every number a slide shows comes from here.

```toml
schema = 1

[product]
name = "Toolshed Commons"
fictional = false            # true needs a disclosure line
# disclosure = "Toolshed Commons is a made-up example."

[[evidence]]
id = "returns_repaired"      # a-z, 0-9 and _; unique across all evidence files
label = "returned tools repaired"     # a few words: the limit is in craft-floor.md
source = "Loan ledger, 2026"          # never empty
value = "62%"                         # or series, never both
aliases = ["62 percent"]              # other ways the deck may write the value

[[evidence]]
id = "repairs_by_month"
label = "repairs per month"
source = "Loan ledger, 2026"
series = [["Apr", 41], ["May", 58], ["Jun", 77]]
```

- **`value`** becomes a figure's numeral. Keep it to digits, signs and unit words:
  `62%`, `−0.4%`, `12 tỷ ₫`. Capitals with stacked accents and a few other characters
  are refused there (`pen.md` lists them); put the words in the label.
- **`series`** becomes a bar chart. It needs at least one `[category, number]` pair, and
  every number must be finite.
- **`source`** is what the source line prints. A number the user told you gets
  `user, <date>`.
- **Unknown keys are ignored**, so the user's file can carry anything else: a one-liner,
  a `[product.world]`, features, audiences. Read them; they are material for the brief.
- **Several files.** The first is the primary one and holds `[product]`. Later files hold
  only `[[evidence]]`. Add a second file when the first is not yours to edit.

## The brief file

```toml
schema = 1
mode = "presented"                    # presented | read
pack = "swiss"
evidence = ["product.toml", "deck.evidence.toml"]   # relative to this file

[direction]
audience = "Neighbours at the spring members' meeting"
decision = "Fund a second repair bench"
thesis = "Repairs, not new tools, are what keep members coming back"
own_world = ["chisels", "the lending shelf", "sawdust", "membership cards"]
motif = "A tag on every returned tool, filled in by the next borrower"

[voice.fonts]                         # or: voice = "neutral" at the top
display = "Georgia"
text = "Calibri"

[voice.palette]
paper = "EEF0F2"
ink = "1B1F24"
muted = "4F5761"
hairline = "BFC5CC"
accent = "1F6F5C"
accent_on_ink = "7FD1B9"

[voice.why]
paper = "the pale grey of a pegboard wall"
ink = "the black of a cast-iron vice"
muted = "graphite from a carpenter's pencil"
hairline = "a chalk line snapped across a board"
accent = "the green paint on the library's shed door"
accent_on_ink = "the same green under the workshop lamp"

[[slides]]
role = "cover"
headline = "Toolshed Commons"
reads = ["what the library is"]

[[slides]]
role = "evidence"
headline = "Most returned tools need a repair before the next loan"
reads = ["the share of returns that need a repair"]
evidence = ["returns_repaired"]
notes = "Point at the number, not the chart."
```

## The direction, field by field

| Field | What it is | Test |
|---|---|---|
| `audience` | Who is in the room, or who reads it alone | Could you name one of them? |
| `decision` | What they should decide or do afterwards | It starts with a verb they can act on. |
| `thesis` | One sentence someone could disagree with | If it reads like a mood or a topic, it is not a thesis yet. |
| `own_world` | 3 to 7 concrete nouns from the subject's world | Each is a thing you could photograph there. No adjectives about the deck. |
| `motif` | One device that repeats and grows | The close answers what the cover started. |

- "Our growth story" is a topic. "Repairs, not new tools, keep members coming back" is a
  thesis: a member could argue with it.
- `own_world` feeds the voice and the wording. "Chisels, sawdust, the lending shelf" can
  be drawn from. "Clean, modern, bold" cannot, and `brief` reports it. <!-- rule:brief-mood -->

## The slides

Each `[[slides]]` entry has a role, a headline and its reads.

| Role | Use it for |
|---|---|
| `cover` | The first slide: the name, and one line under it. Exactly one. |
| `section` | A divider between parts. No evidence: it has no room for a source line. |
| `statement` | One sentence that carries the argument, with space around it. |
| `evidence` | A claim with its proof: text, bullets, a figure, a table, a chart or a picture. |
| `quote` | Someone's words. The headline is the quote; no evidence here either. |
| `close` | The last slide: what to do now. It answers the motif. |

- **The headline test.** Read only the spine that `kl.py brief` prints, top to bottom. It
  has to tell the whole story. If a headline names a topic ("Market overview"), rewrite
  it as the claim that slide proves, within the word limit. <!-- rule:brief-headline-long -->
- **`reads`** are what the audience must take in from the slide, in order. They are your
  plan for the slide, not text on it. Few reads means one idea. <!-- rule:brief-reads -->
- **`evidence`** lists the ids the slide shows. A number on the slide that is not in its
  evidence is reported. <!-- rule:unsourced-number -->
- **`notes`** are the speaker notes. A presented statement, evidence, quote or close
  slide needs them. <!-- rule:brief-notes -->
- A presented deck of some length wants at least one statement slide. <!-- rule:brief-no-statement -->

## The voice

The voice is the deck's fonts and colours. Derive it from the subject at step 4 of the
loop; do not reach for the same look every time.

### Colours

Take them from `own_world` (or the evidence file's `[product.world]`). Each of the six
roles gets one hex colour and one `why` line that names the thing it comes from. <!-- rule:voice-why -->

| Role | Used for |
|---|---|
| `paper` | the default background |
| `ink` | text on paper, and the background of section slides |
| `muted` | labels, source and note lines |
| `hairline` | thin rules; never text |
| `accent` | the one signal colour on paper |
| `accent_on_ink` | the same signal on an ink background |

Check them as you choose. `brief` reports a voice whose text falls below the contrast
floor on its surface, and one with cream paper and a terracotta colour. Darken or
lighten the colour until it passes, and keep the `why`. <!-- rule:voice-contrast --> <!-- rule:voice-claude-look -->

### Fonts

Pick two families from the six portable ones: `display` for titles and `text` for the
rest. They may be the same. The deck's language decides: the table says which family's
metric twin has which letters. Pick before you build.

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

A family that lacks letters of your text makes the pen print one `keyline pen: warning:`
line per deck. That is the backstop. If you see it, change the family and rebuild; do
not accept the preview.

### Stock voices

`voice = "neutral"`, `"night"` or `"field"` at the top of the brief, in place of
`[voice]`. They are fallbacks. Use one only when the user asks for a plain look, or
gives no subject world.

## What `brief` checks

It exits 1 on a schema error, with one line that names the key. It exits 2 when it has
findings at warning or error level: too many reads, mood words in `own_world`, missing
notes, a headline over the word limit, a voice that fails its checks. It exits 0
otherwise. With `--json`, the spine and the findings come on stdout.
