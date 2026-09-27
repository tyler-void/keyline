# Audit 01: plan for spec 002

- **Auditor:** an external Claude session. It did not see the implementing session.
- **Date:** 2026-09-27
- **Scope:** branch `002-skill-pack` at `b349766`, four commits over `main` `678c69a`.

**Method**
- Cloned the public repo and checked out the branch.
- Hashed the handed-over files.
- Diffed every doc against `main`.
- Read `plan.md` and `tasks.md` in full.
- Recomputed the plan's grid arithmetic.
- Re-ran `ruff` and `pytest`.

## Verdict

**Approved with amendments.** Implementation of A1 may start once B-1 … B-7 below are
appended to the amendment log of spec 002. Spec 001's amendments are A-n, so spec 002's
are B-n, to keep the two apart.

## What was verified

- **Identity.** All 4 commits are `Tyler <code@tyler-void.dev>` as author and
  committer (D-014).
- **Integrity.** The three handed-over files are byte-identical to the bundle:
  - `spec.md`: `8b667242…`
  - `numbers_ref.py`: `af534e21…`
  - `product.toml`: `9b0fea6e…`
- **Docs.**
  - `docs/decisions.md` +72/−0, and every line of spec §0 is present verbatim.
  - `docs/lessons-learned.md` +21/−0.
  - `CLAUDE.md` changes exactly the two lines the handoff named.
  - `ruff.toml` adds only the `specs/*/evidence` exclusion.
- **Checks.** `ruff check .` and `ruff format --check .` are clean. `pytest` gives
  **215 passed** (Python 3.11.15). No code has changed yet.
- **CI** (run 36324648466) was not verified: the GitHub API is not reachable from the
  auditor's sandbox. The local run above stands in for it.
- **Grid arithmetic (plan §2.5), recomputed:**
  - Column width: (12192000 − 2 × 540000 − 11 × 180000) / 12 = 761000 EMU (2.114 cm).
  - Content height: 5760000 = 64 × 90000.
  - Eight columns: 20.41 cm, above the 19.5 cm that "212 years" needs with the 0.99
    margin.
  - Title region: 4.25 cm, holding two 48 pt lines at 4.06 cm.
  - Footer: 1.5 cm, holding two 12 pt lines at 1.02 cm.
  - Worst empty band: 3.525 cm = 18.5 % of the slide height.
  - Margins: 1.50 / 1.525 cm ≥ 1.27 cm.
- **The plan's pre-checks match the auditor's.** The three pack-free rules fire on no
  existing deck, which the auditor found independently on 2026-09-27. The oracle agrees
  on the §4.4 anchors.

## What the plan does well

- A baseline of M1 output is captured before any lint code changes (T-01). This
  gives spec 001 the rule-fixture snapshots it never had, so AC-2 becomes checkable.
- The two-argument arity adapter and the preserved message substrings keep the M1
  tests untouched, beyond AC-2's list.
- The tokenizer is tested differentially against the auditor's oracle: on the anchors,
  on every `product.toml` string, and on 5,000 generated strings. The oracle is
  imported by path, never copied.
- Templates are built from raw OOXML with the palette theme and no third-party author.
  They must pass `officecli validate` and rebuild byte-identically.
- Grid units are in EMU, so every region edge is an integer.
- It found my own errors (Q-1 and Q-7).

## Rulings on the open questions

"Accept" means the plan's proposal becomes binding, as written in the plan.

| Q | Topic | Ruling |
|---|---|---|
| 1 | Registry count | Accept: **32**. AC-2's "31" is my typo. **B-1** |
| 2 | Fields of the §4 ids | Accept |
| 3 | `slide` key for brief findings | Accept |
| 4 | AC-8 needs the pen | Accept: a fixture stand-in in A1, repeated with the pen in A2. **B-3** |
| 5 | Rule-fixture snapshots | Accept (T-01) |
| 6 | Tokenizer limits (dates, versions, `3 × 4`, `$-5`) | Accept, with **B-5** |
| 7 | Source and note lines in `title-not-dominant` | **Overruled: one body definition** (A-2). Source and note paragraphs are not body in either rule. §3.1's "everywhere else, both count as text" meant contrast, fonts and pack rules, not body. **B-2** |
| 8 | Mixed decks | Accept: a role, when present, decides |
| 9 | AC-5 slide order | Accept |
| 10 | Margins and the 8-column rule | Accept |
| 11 | No-engine message | Accept: keep the M1 substring |
| 12 | `officecli` rules in `lint` | Accept |
| 13 | `--pack` against the brief | Accept: compare resolved directories |
| 14 | Unknown pack, or a mode the pack lacks | Accept: exit 1. **B-4** |
| 15 | Stop after report A1 | Accept |
| 16 | Who runs the demo | Accept: Tyler starts the fresh session; the implementer prepares the exact commands and prompts |
| 17 | Raw OOXML templates | Accept, with **B-6** |
| 18 | LibreOffice 26.8 against 24.2 | Accept, with **B-7** |
| 19 | `numbers.py` → `numtokens.py` | Accept. Spec §1 already allows the plan to refine the layout |
| 20 | Theme colors and layout list | Accept, with one recommendation: map `hlink` to **ink** rather than accent. A hyperlink in accent counts as an accent element and would spend the slide's budget of 1. The implementer decides in T-08 and records the choice |
| 21 | Pen placeholders | Accept |
| 22 | Font check off Linux | Accept |
| 23 | `brief-mood` tokens | Accept |
| 24 | `accepted` | Accept |
| 25 | Cream ratio denominator | Accept |

## Amendments to append to spec 002 (verbatim)

- **B-1 (2026-09-27, audit 01).** AC-2: `test_rules_listing` accepts the **32** ids of
  AC-1, not 31.
- **B-2 (2026-09-27, audit 01).** Source and note paragraphs (§3.1) are not body in
  `body-too-small` and not body in `title-not-dominant`, so A-2's single body definition
  holds. They still count as text for contrast, fonts and the pack rules.
- **B-3 (2026-09-27, audit 01).** AC-8 runs in A1 on a deck built by a fixture script
  that writes what the pen will write: the Swiss layouts, region boxes, and source and
  note lines. AC-8 runs again in A2 on a pen-built deck, with the same six drifts and
  the same expected findings.
- **B-4 (2026-09-27, audit 01).** Two more schema errors for `keyline brief` (exit 1,
  one line): a pack that cannot be found, and a mode the pack does not list in
  `modes`.
- **B-5 (2026-09-27, audit 01).** The following are known limits of §4.4. They are
  pinned by tests and documented in `check.md`:
  - a day of the month ("27 September 2026" gives a significant `27`);
  - version strings ("v2.0.1" gives `2.0.1`);
  - "3 × 4" gives `3×`;
  - "$-5" gives `-5`.

  The skill writes month-year dates. A deck that needs a full date lists it as an
  evidence entry for that slide.
- **B-6 (2026-09-27, audit 01).** G-1 also covers opening both templates and both
  specimens in PowerPoint. PowerPoint for the web is enough. The report records which
  PowerPoint was used and whether it offered to repair any file.
- **B-7 (2026-09-27, audit 01).** Every render-dependent result records the LibreOffice
  version it ran on. This covers AC-13(b), AC-14 and the contact sheets.
  - AC-13(b) is judged on the installed version.
  - The implementer first measures line pitch and the wrap margin on that version.
    If they differ from §6.4's 24.2 values (1.2 em; wraps at 1.000× and 1.002×, not at
    1.005×), the report says so, and the auditor rules before any constant changes.
    Constants are never tuned to make a test pass.

## Notes for A1 (not blocking)

- **Regions and pen shape boxes in A2.** A `figure()` makes two shapes (numeral and
  label) in one region. Both cannot be "the full region box" (§6.3) without
  overlapping. When A2 is planned, split the figure region into numeral and label
  sub-boxes that together fill the region.
- **T-01 baseline.** Commit the M1 baseline JSON before T-03 lands, in its own commit,
  so the audit can diff it against `main`'s output.
- **Report A1.** For each AC that skips in CI (AC-14, AC-14b), name the machine and
  the tool versions it passed on (LibreOffice, OfficeCLI).
