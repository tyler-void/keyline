# Decisions

Append-only. To change a decision, add a new entry that supersedes the old one.

| ID | Date | Decision | Why |
|---|---|---|---|
| D-001 | 2026-09-24 | Name: **keyline** | Free on npm and PyPI (checked 2026-09-24). No slide or design tool with that name found. Every "Slide Bench" spelling is taken. |
| D-002 | 2026-09-24 | License: Apache-2.0. `NOTICE`: "Copyright 2026 Tyler (@tyler-void)" | Same license as impeccable and OfficeCLI; public repo |
| D-003 | 2026-09-24 | Output: editable `.pptx`. OfficeCLI builds decks and renders previews | Users want native, editable decks and corporate templates, and HTML-to-pptx conversion loses fidelity (research §1, §4) |
| D-004 | 2026-09-24 | `keyline lint` reads the OOXML package with lxml, with no OfficeCLI dependency. Supersedes the prototype's `dump` approach | Lints decks from any source, runs in the claude.ai sandbox, avoids L-001 |
| D-005 | 2026-09-24 | The gate is a tool (`keyline check`), not a hook | claude.ai web and desktop have no hooks (support docs, 2026-09) |
| D-006 | 2026-09-24 | Distribution: one Agent Skill folder, zipped for claude.ai web and desktop, installed or synced for Claude Code. Package code is vendored into the skill (M2) | Skills upload as a ZIP and sync one-way to Claude Code; no programmatic upload exists (anthropics/claude-code#93163) |
| D-007 | 2026-09-24 | Finding contract modeled on impeccable: JSON on stdout, human output on stderr, exit 0 / 2 / 1; `advisory` findings never fail | Proven in CI and hooks; one contract for every consumer |
| D-008 | 2026-09-24 | Two modes: `presented` (default) and `read` | The canon conflicts on density because presented decks and reading decks are different artifacts |
| D-009 | 2026-09-24 | Build order: lint core (M1), then skill + brief + first pack (M2), then fonts + hooks (M3) | The author needs usable decks early; the report's order optimized only for a moat |
| D-010 | 2026-09-24 | Benchmark name deferred. Avoid SlidesBench and SlideBench variants | Both names are taken (AutoPresent, slidebench.org, SlideChat) |
| D-011 | 2026-09-24 | Roles: Tyler decides, Claude Code executes, an external Claude session audits by cloning | Independent verification: the builder does not grade its own work |
