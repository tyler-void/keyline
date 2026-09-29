# Swiss (v1)

**Direction.** A grid, flush-left and ragged-right. One family per voice, regular and
bold. Paper, ink and one signal colour. Hairlines instead of boxes. Statement slides are
allowed to be mostly empty, and that emptiness is the point.

**The device.** Every `evidence` slide carries *the keyline*: one strong ink rule at a
fixed height, across the full content width. It is the only recurring decoration. The
pen draws it; nobody places it by hand.

## System and voices

`pack.toml` is the **system** (amendment B-8, D-020): the grid, the type scale, the roles,
the regions and the device, with colours named by role (`paper`, `ink`, `muted`,
`hairline`, `accent`, `accent_on_ink`) and fonts named as `display` or `text`. A **voice**
gives the roles their values and names the two families. A deck's voice comes from its
brief, ideally derived from the subject's own world; the stock voices below are
fallbacks for when the user asks for a plain look or gives no subject world.

| voice | fonts | paper | ink | accent | where it comes from |
|---|---|---|---|---|---|
| `neutral` | Arial | `F2F2F0` | `111111` | `CC3322` | uncoated offset paper, printing ink, a Swiss signal red |
| `night` | Arial | `16181B` | `ECECE8` | `F0B429` | a darkened room, chalk on slate, an instrument lamp |
| `field` | Georgia | `EEF2EE` | `16251D` | `1D4FB8` | a field notebook, forest ink, a survey marker |

Each voice's `[why]` table gives the reason for every role. In `night`, paper is the
dark surface and ink the light one, so its section slides are light: sections invert in
every voice.

## Why these choices

- **Paper is never cream.** A cream paper with a terracotta accent is the documented
  "Claude look" (L-007). The `neutral` paper is `F2F2F0` (CIELAB C\* 1.02), and
  `voice-claude-look` checks every other voice.
- **The accent must read at any size.** Every (text colour, surface) pair a voice allows
  reaches 4.5 : 1, which `voice-contrast` checks. That is why the ink surface has its own
  accent value: in `neutral`, `CC3322` reaches 4.61 : 1 on paper but only 3.65 : 1 on
  ink, so the ink surface uses `E8422E` (4.72 : 1). L-006 recorded what happened with
  the first, lighter red.
- **One accent per slide** (`accent_budget = 1`). An accent that appears everywhere
  stops meaning anything.
- **Rules, not boxes** (`containers = "rules"`). Filled cards are the most common
  generated-deck tell (L-004); tables get hairlines and no fills.
- **Portable fonts only** (D-020), until fonts can be embedded (M3). A voice may use a
  family that ships with Windows and macOS, or with Office, and that has an open
  metric-compatible twin (`portable_fonts` in `thresholds.toml`), so renders and the
  pen's fit estimate agree with PowerPoint closely.
- **Sizes differ by mode.** A presented deck is read from across a room (body 24 pt);
  a read deck is read at arm's length (body 13 pt). The scale keeps the title at least
  twice the body in presented mode and 1.6 times in read mode.

## The grid

Twelve columns of 2.114 cm with 0.50 cm gutters and 1.50 cm side margins; 64 rows of
0.25 cm between 1.525 cm top and bottom margins. Eight columns (20.41 cm) are wide
enough for the longest numeral in the demo evidence, "212 years" at 120 pt.

## Templates

Templates are built per voice and mode, in memory, by `keyline.packs.templates`. Only
the `neutral` pair is committed (`swiss-neutral-presented.pptx`,
`swiss-neutral-read.pptx`), for inspection; `src/build_templates.py [OUT_DIR] [--voice
NAME]` writes any voice's pair, and the build is byte-stable.

## Examples

The specimens in `fixtures/packs/` show every role and every component once. Each is
**one idea, not a template**: they show what the tokens do, not what a deck should say.
