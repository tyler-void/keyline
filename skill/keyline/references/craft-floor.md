# Craft floor

Read this right before every build. Each line is enforced: by a rule that `check` or
`brief` runs (its id is in the comment after the line), or by the pen, which refuses.
Nothing here is taste. Fix recipes are in `check.md`.

## Say one thing per slide

- The title is the brief's headline, word for word. <!-- rule:brief-headline -->
- A headline stays within the mode's word limit. Quote slides are exempt: there the
  headline is the quote. <!-- rule:title-too-long --> <!-- rule:brief-headline-long -->
- A slide keeps the role its brief gives it, and the deck has as many slides as the
  brief. <!-- rule:brief-role --> <!-- rule:brief-slide-count -->
- A slide asks the audience to take in only a few things: its reads. <!-- rule:brief-reads -->
- The last slide is not "Thank you" or "Questions?". It answers the motif. <!-- rule:closing-cliche -->
- In a presented deck, every statement, evidence, quote and close slide has speaker
  notes. <!-- rule:brief-notes --> <!-- rule:notes-missing -->

## Source every number

- A significant number on a slide is in that slide's brief evidence. <!-- rule:unsourced-number -->
- A slide that shows evidence carries a source line: call `source()`. <!-- rule:source-missing -->
- A fictional product says so on the first or the last slide: call `note()` there. <!-- rule:fiction-undisclosed -->

## Let the pack set the type

<!-- gen:begin type-scale -->
| Style | presented, pt | read, pt | Weight | Case | Line spacing |
|---|---|---|---|---|---|
| `cover_title` | 66 | 40 | bold | as typed | 1 |
| `statement` | 60 | 36 | bold | as typed | 1 |
| `headline` | 48 | 28 | bold | as typed | 1 |
| `quote` | 44 | 24 | regular | as typed | 1 |
| `lede` | 28 | 16 | regular | as typed | 1.1 |
| `body` | 24 | 13 | regular | as typed | 1.1 |
| `numeral` | 120 | 60 | bold | as typed | 1 |
| `label` | 14 | 10 | bold | caps, +8 % tracking | 1 |
| `source` | 12 | 9 | regular | as typed | 1 |
<!-- gen:end -->

- These are the only sizes. You pass a style name, never a size. <!-- rule:off-scale-size -->
- The deck uses the voice's families and no others. <!-- rule:off-pack-font --> <!-- rule:font-count -->
- The title is clearly the largest text on its slide, and body text is never below the
  mode's minimum. <!-- rule:title-not-dominant --> <!-- rule:body-too-small -->
- Text that does not fit its region is refused, not shrunk (`DoesNotFit`). Shorten it, or
  split the slide.

## Spend colour once

- Every colour comes from the voice's palette. <!-- rule:off-palette-color -->
- One accent element per slide, at most: a figure with `accent=True`, or one highlighted
  bar. <!-- rule:accent-overuse -->
- Text meets the contrast floor on its surface, in every voice. <!-- rule:text-contrast --> <!-- rule:voice-contrast -->
- Cream paper with a terracotta accent is the look of a generated deck. A voice does not
  use it. <!-- rule:claude-look-palette --> <!-- rule:voice-claude-look -->
- An inline voice says where each colour comes from, and `own_world` names things, not
  moods. <!-- rule:voice-why --> <!-- rule:brief-mood -->

## Leave the layout to the pen

- Everything sits in a region of the layout, inside the slide and its margins. <!-- rule:off-slide --> <!-- rule:edge-margin -->
- No row of equal cards, and no small bar under a title. The pen has no verb for
  either. <!-- rule:equal-card-row --> <!-- rule:title-underline -->
- An evidence slide fills its main region. For one sentence with space around it, use a
  statement slide. <!-- rule:dead-band -->

## Stay inside the budgets

<!-- gen:begin budgets -->
| Limit | presented | read |
|---|---|---|
| Words in a title or headline | 10 | 15 |
| Reads per brief slide | 3 | 5 |
| Items in a bullet list | 4 | 6 |
| Figures on a slide | 1 | 2 |
| Words in a figure's numeral | 5 | 5 |
| Words in a label, table header or attribution | 5 | 5 |
| Smallest body text, pt | 18 | 11 |
| Smallest source or note line, pt | 12 | 9 |
| Font families in a deck | 2 | 2 |
| Text contrast, at least | 4.5 | 4.5 |
| Accent elements on a slide | 1 | 1 |
<!-- gen:end -->

## Put the right thing on each role

<!-- gen:begin roles -->
| Role | Surface | Title style | Verbs (styles), presented | read |
|---|---|---|---|---|
| `cover` | paper | `cover_title` | `text` (lede), `source` (source), `note` (source) | the same |
| `section` | ink | `headline` | `text` (label) | the same |
| `statement` | paper | `statement` | `text` (lede, body), `figure` (numeral, label), `source` (source), `note` (source) | the same |
| `evidence` | paper | `headline` | `text` (body), `bullets` (body), `figure` (numeral, label), `table` (body, label), `chart_bar` (label, source), `image`, `source` (source), `note` (source) | `text` (body, lede), `bullets` (body), `figure` (numeral, label), `table` (body, label), `chart_bar` (label, source), `image`, `source` (source), `note` (source) |
| `quote` | paper | `quote` | `attribution` (label) | the same |
| `close` | paper | `cover_title` | `text` (lede), `figure` (numeral, label), `source` (source), `note` (source) | the same |
<!-- gen:end -->
