# The brief

A brief is the deck before it has a look: who it is for, what it claims, and one line
per slide. Two TOML files hold it. `kl.py brief <deck>.brief.toml` validates both and
prints the spine. Fix recipes for its findings are in `check.md`.

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
