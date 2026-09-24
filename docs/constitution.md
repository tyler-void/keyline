# Constitution

These principles outrank every spec. Changing one needs a dated entry in
`docs/decisions.md` that says what changed and why.

**I. Measure before teaching.**
If a design belief can be measured, it becomes a rule with fixtures before it becomes
prose in a skill. Written advice alone is not a gate.

**II. The gate lives in the tool.**
claude.ai web and Claude desktop have no hooks. Enforcement therefore happens inside
the command an agent must run to finish a deck (`keyline check`). Claude Code hooks
speed the loop up; they are not the enforcement mechanism.

**III. Any .pptx.**
`keyline lint` reads the OOXML package directly. It must not depend on whatever
generated the deck: OfficeCLI, pptxgenjs, python-pptx, or PowerPoint.

**IV. Declare the measurement basis.**
Every rule states what it measures: geometry, text, color, structure, or render.
Some rules approximate something visible, such as ink overlap estimated from bounding
boxes. Those rules are `advisory` until a render-based engine measures the visible
thing itself.

**V. Thresholds are data.**
Thresholds live in config, per mode (presented, read) and later per style pack. They
stay marked uncalibrated until they have been measured against human-labelled decks.

**VI. Honest fixtures.**
Every rule has at least one positive and one negative fixture. Golden decks record
real outcomes, including our own mistakes. A fixture is never edited to make a rule
pass.

**VII. Deterministic, portable core.**
No network, no model calls, byte-stable output. Python, `lxml` and `Pillow` only.

**VIII. Soul is not linted.**
The linter removes the known reasons a deck looks generated. It never claims a deck
is good. Beauty comes from the brief (thesis, own-world, headline spine) and from the
style packs. Any use of lint results as a score must come with a content gate, so
that an empty slide cannot win.

**IX. Bounded verification.**
Run one batch of checks, apply one batch of fixes, then do at most one more round.
After that, report.

**X. Public hygiene.**
The only identities allowed are "Tyler" and "@tyler-void". The license is Apache-2.0.
Never copy text from source-available material.
