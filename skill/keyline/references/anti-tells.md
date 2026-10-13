# Anti-tells, v1

A tell is a pattern that makes a deck look generated. This table says what stops each
one. Rows are added, never dropped.

**Enforcement** is one of:

- `rule:<id>`: `check` reports it. The recipe is in `check.md`.
- `brief:<id>`: `brief` or `check --brief` reports it.
- `pen`: the pen cannot produce it, or refuses.
- `backlog:<id>`: not enforced yet. Avoid it by hand.

**Sources.** The tells and their measurable signatures are from `docs/research.md` in the
keyline repository: the sections "ANTI-TELLS.md should start from about 30 tells with
measurable signatures" (most rows), "'Editorial' has become Claude's look: the Swiss
pack needs hard guards" (the colour and type rows) and "The canon agrees on 'one claim
per slide' and disagrees on density" (titles, notes, sources).

| id | tell | enforcement | Swiss policy |
|---|---|---|---|
| equal-cards | three or more equal cards, whatever the item count | `rule:equal-card-row`; `pen` | No card verb. Use a table, or one figure and a sentence. |
| cards-everywhere | text inside filled boxes, boxes inside boxes | `pen` | `containers = "rules"`: hairlines separate things, boxes never do. |
| stat-tile-row | a row of big numbers with small labels | `pen` | At most one figure on a presented slide, two on a read slide. |
| everything-centered | centered body text | `pen`; `backlog:centered-body` | Flush left, ragged right, everywhere. |
| flat-hierarchy | a title barely larger than the body | `rule:title-not-dominant` | The type scale keeps the title at least twice the body in presented mode. |
| position-drift | titles that jump between slides | `pen` | The layouts fix every position. |
| no-confident-emptiness | no slide is allowed to breathe | `brief:brief-no-statement` | A statement slide holds one sentence and space. |
| dead-band | a large empty band on a content slide | `rule:dead-band` | An evidence slide fills its main region. |
| title-underline | a short accent bar under the title | `rule:title-underline`; `pen` | No bar verb. The keyline spans the full width, in ink. |
| icon-in-circle | small icons in coloured circles, repeated | `pen` | No icon verb. |
| eyebrow-caps | tracked capitals above every heading | `pen`; `backlog:eyebrow-caps` | Capitals only in the `label` style: table headers, figure labels, attributions. |
| claude-look | cream paper with a terracotta accent | `rule:claude-look-palette`; `brief:voice-claude-look` | The stock voices have neutral paper and no terracotta. |
| italic-insert | an italic phrase in another family inside a title | `pen`; `backlog:title-italic-insert` | No italic. One style per title. |
| effects | purple-blue gradients, identical shadows, glow | `pen` | Flat colour only. |
| unsourced-numbers | numbers with no source | `brief:unsourced-number`; `brief:source-missing` | Every figure, table and chart comes from evidence, and `source()` writes the line. |
| hype-language | hype words, "not X but Y", decorative dashes, emoji bullets | `backlog:language-tells` | Write plain claims. Not checked yet. |
| thank-you-closer | a "Thank you" or "Questions?" last slide | `rule:closing-cliche` | The close answers the motif. |
| ticker-bar | a thin full-width band of capital items | `pen` | No such verb. |
| topic-titles | long descriptive titles that claim nothing | `rule:title-too-long`; `brief:brief-headline-long` | A headline is a claim within the word limit. |
| cramming | text shrunk until it fits | `pen`; `rule:off-scale-size` | The pen refuses with `DoesNotFit`. Sizes never change. |
| font-soup | more than two families | `rule:font-count`; `rule:off-pack-font` | A voice has one display and one text family. |
| accent-everywhere | the accent on many elements of a slide | `rule:accent-overuse` | `accent_budget = 1`. |
| tiny-body | body text below the mode's floor | `rule:body-too-small` | The scale's `body` is above the floor in both modes. |
| low-contrast | text below the contrast floor | `rule:text-contrast`; `brief:voice-contrast` | Checked for every text colour on every surface of the voice. |
| no-notes | presented slides without speaker notes | `rule:notes-missing`; `brief:brief-notes` | The brief carries the notes, and `next()` applies them. |
| visual-on-every-slide | a picture forced onto every slide | `pen`; `brief:brief-no-statement` | Statement, section and quote slides have no `image` verb. |
| mood-direction | a direction made of adjectives | `brief:brief-mood` | `own_world` names things from the subject. |
| one-look-for-everything | the same palette and fonts for every subject | `brief:voice-why`; `backlog:diversity-fingerprint` | The voice is derived from `own_world`, one `why` line per colour. Stock voices are fallbacks. |
