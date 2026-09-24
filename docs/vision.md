# Vision

**keyline is impeccable for slides.** It gives AI agents a design language and a
deterministic gate, so the decks they produce look designed rather than generated.
Its output is an editable `.pptx`.

The name comes from print. A *keyline* is the thin line that marks where content
goes. Read as "key line", it is also the one sentence each slide has to say.

## Who it is for

1. People who make many internal decks with Claude and want a consistent, clean result
   every time.
2. Someone asked to make a demo deck for a product, who needs it to look like it came
   from a designer.
3. Later, anyone comparing models. The question: given the same brief and the same
   design system, which model ships fewer known defects?

## Where it runs

One Agent Skill, packaged as a ZIP, runs on claude.ai web, Claude desktop and Claude
Code. Hooks are an extra that only Claude Code gets. The gate itself runs everywhere
(see constitution II).

## Layers

| Milestone | Layer | Why in this order |
|---|---|---|
| M1 | `keyline lint` core + render + `check` gate | Everything else calls it |
| M2 | Skill: brief (thesis, own-world, headline spine), craft floor, ANTI-TELLS, first style pack | Where the soul comes from; usable decks start here |
| M3 | Font embedding, `@font-face` QA render, Claude Code hooks, more rules | Raises the ceiling and speeds up the loop |
| M4+ | More packs, corporate `.potx` templates, calibration, then a benchmark | Only once rules have measured precision |

## Non-goals

- HTML decks, or slides generated as images.
- Parity with Google Slides or Keynote beyond a documented portable subset.
- Any claim to measure beauty. The linter only removes known reasons a deck looks
  generated.
