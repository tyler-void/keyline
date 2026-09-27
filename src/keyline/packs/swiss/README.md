# Swiss (v1)

**Direction.** A grid, flush-left and ragged-right. One sans family. Paper, ink and one
signal red. Hairlines instead of boxes. Statement slides are allowed to be mostly empty,
and that emptiness is the point.

**The device.** Every `evidence` slide carries *the keyline*: one strong ink rule at a
fixed height, across the full content width. It is the only recurring decoration. The
pen draws it; nobody places it by hand.

## Why these choices

- **Paper is neutral, not cream** (`F2F2F0`, CIELAB C\* 1.02). A cream paper with a
  terracotta accent is the documented "Claude look" (L-007); the palette keeps clear of
  both, and `claude-look-palette` checks it.
- **The red is a signal red** (`CC3322`, HSL hue 6°), not a terracotta. It reaches
  4.61 : 1 on paper, so it is legible at any size (L-006 recorded what happened with the
  first, lighter red). On the ink surface the red is `E8422E`, because `CC3322` only
  reaches 3.65 : 1 there.
- **One accent per slide** (`accent_budget = 1`). A red that appears everywhere stops
  meaning anything.
- **Rules, not boxes** (`containers = "rules"`). Filled cards are the most common
  generated-deck tell (L-004); tables get hairlines and no fills.
- **Arial only** (D-017), regular and bold, until fonts can be embedded (M3). Every
  surface has it, and Liberation Sans matches its metrics, so renders and the pen's fit
  estimate agree with PowerPoint closely.
- **Sizes differ by mode.** A presented deck is read from across a room (body 24 pt);
  a read deck is read at arm's length (body 13 pt). The scale keeps the title at least
  twice the body in presented mode and 1.6 times in read mode.

## The grid

Twelve columns of 2.114 cm with 0.50 cm gutters and 1.50 cm side margins; 64 rows of
0.25 cm between 1.525 cm top and bottom margins. Eight columns (20.41 cm) are wide
enough for the longest numeral in the demo evidence, "212 years" at 120 pt.

## Examples

The specimens in `fixtures/packs/` show every role and every component once. Each is
**one idea, not a template**: they show what the tokens do, not what a deck should say.
