# keyline: instructions for Claude Code

keyline makes AI-generated PowerPoint decks look designed instead of generated.
It has three layers, built in this order:

1. `keyline lint`: deterministic design checks on any `.pptx` (current work).
2. `keyline render` / `keyline check`: per-slide PNGs, a contact sheet, and the gate.
3. A cross-surface Agent Skill (Claude Code, claude.ai web, Claude desktop) with a
   brief format and style packs. Not started; do not build ahead.

Status: pre-alpha. **Active spec: `specs/001-lint-core/spec.md`.**

## Read before any work

- `docs/constitution.md`: the principles. They are non-negotiable.
- `docs/decisions.md`: what has been decided and why (append-only).
- The active spec.
- `docs/lessons-learned.md`: OfficeCLI quirks and mistakes already paid for.
- `docs/research.md` is background. Cite it by section; do not re-research it.

## Roles

- **Tyler (@tyler-void)** owns every decision.
- **You** implement.
- **An external auditor** (a separate Claude session) reviews each milestone. It
  clones the repo and re-runs everything; it never sees your session. So:
  everything must be reproducible from the repo alone, and every claim in a report
  must point to a command and its output.

## Workflow per spec

1. **Plan.** Read the spec. Write `specs/NNN-*/plan.md` and `tasks.md`. Commit them
   on a branch named after the spec (e.g. `001-lint-core`). **Stop and report.**
   Do not implement until Tyler approves the plan.
2. **Implement** task by task. Every task lands with its tests.
3. **Report.** Write `specs/NNN-*/report.md`:
   - each acceptance criterion: the command, an output excerpt, PASS/FAIL;
   - a **Deviations** section: "Spec said X; implemented Y because Z";
   - an **Open questions** section.

The spec is append-only. Never edit it to match what you built. Propose
amendments in `report.md` and Tyler decides.

## Hard rules

- **Identity.** This is a public repo. No personal name other than "Tyler" or
  "tyler-void"/"@tyler-void" may appear anywhere (code, docs, fixtures, commit metadata).
  Commits use the approved identity in D-014. Tool-attribution trailers
  (`Co-Authored-By: Claude …`) are allowed (D-013). Before the first commit in any
  clone, check `git config user.name` and `git config user.email` against D-014.
- **Licensing.** Never copy text from Anthropic's skills (source-available, not open
  source). impeccable and OfficeCLI are Apache-2.0: borrowing ideas is fine; copying
  code requires attribution in `NOTICE`.
- **Portable lint core.** Pure Python >= 3.10. Runtime deps: `lxml` and `Pillow` only.
  `keyline lint` makes no network calls, no model calls, and does not use OfficeCLI.
  It must run inside the claude.ai code-execution sandbox.
- **Deterministic.** The same input produces byte-identical JSON.
- **Honest fixtures.** Never tune a threshold or rule to make a golden fixture pass,
  and never edit a provided fixture. If an expectation looks wrong, report it.

## Conventions

- `src/` layout, `pytest`, `ruff`. Conventional commits (`feat:`, `fix:`, `test:`, `docs:`).
- Units: EMU internally; cm (2 decimals) in messages; pt for type sizes.
- Rule IDs are kebab-case and never renamed once released. Deprecate instead.

## Environment

- OfficeCLI: `npm install -g @officecli/officecli` (tested 1.0.152). It is needed
  only to regenerate fixtures and for `keyline render`. Its quirks are in
  `docs/lessons-learned.md`.
- Tests that need OfficeCLI must skip cleanly when it is absent.
