# Lessons learned

Append-only. Each entry records what happened, what it cost, and the rule it gave us.

**L-001 · 2026-09-24 · OfficeCLI positional paths skip charts.**
In `officecli dump`, `shape[N]` counts shapes and text boxes but not charts. This is
not documented. The prototype folded `set` commands by position, so every shape after
a chart got the wrong text, which produced two false overlaps.
→ Never resolve shapes by position. The lxml adapter uses spTree order and shape ids.

**L-002 · 2026-09-24 · OfficeCLI screenshots fall back to sans-serif.**
The OfficeCLI renderer emits `font-family:'Georgia','PingFang SC',…,sans-serif` with no
`@font-face`. Any font that isn't installed, serif or not, renders as sans. A
Georgia + Calibri pairing looks the same as Calibri + Calibri in QA screenshots.
→ Screenshots cannot verify typography until the render step injects `@font-face` (M3).

**L-003 · 2026-09-24 · `officecli view issues` misses composition.**
It reported 0 issues on a deck whose content slides left 37–42% of their height empty
at the bottom. It checks overflow, off-slide shapes, and contrast within a single shape.
→ Composition needs its own rules (`dead-band`).

**L-004 · 2026-09-24 · The recipe is the slop.**
Following the KPI-card recipe in `officecli-pptx` (equal rounded cards, flat brand
fills, centered numbers) produced an AI-looking slide. That skill's own "AI tells"
list does not cover its recipes.
→ Structural slop gets rules (`equal-card-row`); a skill has to override its
defaults, not just add taste on top.

**L-005 · 2026-09-24 · Box overlap is not visible overlap.**
The prototype reported 6 text overlaps on the editorial deck. None of them is visible.
→ Box-based overlap is `advisory` until render-based checks exist (constitution IV).

**L-006 · 2026-09-24 · Taste is not measurement.**
The editorial rebuild we presented as the "good" slide has two real bottom-margin
defects (0.88 cm and 0.54 cm against a 1.27 cm floor). Its red 9.5 pt label reaches
only 3.57:1 contrast on the off-white paper. We claimed it would pass. It doesn't.
→ The golden fixtures record this. A single accent red also needs a size rule:
small text in the accent must reach 4.5:1.

**L-007 · 2026-09-24 · The editorial look sits next to the "Claude look".**
Off-white paper, a red accent and tracked caps are one step from the documented
Claude look: cream background, terracotta accent, eyebrow labels.
→ The guards must be rules, not taste (see `docs/research.md`, section on canon and tells).

**L-008 · 2026-09-24 · No font embedding in OfficeCLI for pptx.**
`embedFonts` exists only for docx, and `add-part` accepts only charts. A research
spike with an EOT post-processor passed `officecli validate`, but nobody has opened
the result in real PowerPoint yet.
→ M3 has to test on real PowerPoint for Windows and for Mac before claiming support.

**L-009 · 2026-09-25 · Stock templates fail the uncalibrated defaults.**
Linting a deck built on the Office default template (python-pptx 1.0.2, "Title and
Content") raises `edge-margin` on the title, which sits 0.76 cm from the top, and in read
mode `title-not-dominant`, because the 44 pt title is only 1.38× the 32 pt body (the
floor is 1.6×). Both measurements are correct (report 001, Q3; audit 02 ruling 3).
→ This is calibration data, not a defect. Thresholds stay as they are until they are
measured against human-labelled decks (constitution V, M6 calibration).
