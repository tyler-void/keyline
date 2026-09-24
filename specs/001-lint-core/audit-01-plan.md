# Audit 01: plan for spec 001

- **Auditor:** an external Claude session. It did not see the implementing session.
- **Date:** 2026-09-24
- **Scope:** `ce21744` (bootstrap on `main`) and `705edc1` (`plan.md`, `tasks.md` on
  `001-lint-core`)

**Method**
- Cloned the public repo.
- Diffed the bootstrap commit against the delivered bundle.
- Read `plan.md` and `tasks.md` in full.
- Independently re-derived the facts the plan relies on:
  - the python-pptx 1.0.2 default template: geometry, `txStyles` sizes, master `p:bg`;
  - python-pptx's placeholder-matching code;
  - the golden boundary values;
  - the Python 3.10 end-of-life date (PEP 619).

## Verdict

**Approved with amendments.** Implementation may start once three things are done:
- A-1 … A-10 are appended to the spec's amendment log;
- D-012 … D-014 are appended to `docs/decisions.md`;
- the CLAUDE.md change in F-1 is applied.

Nothing is waiting on Tyler: D-014 was decided on 2026-09-24.

The bootstrap commit matches the bundle byte for byte (17/17 files). The branch adds
only `plan.md` and `tasks.md`.

## What the plan does well

- It stopped at the identity gate and again after planning, as instructed.
- It surfaced 30 real ambiguities. At least four were defects in the spec (Q2, Q19,
  Q24, Q26).
- It uses exact arithmetic (integer EMU, `Fraction`, `Decimal`) because several golden
  values sit on a threshold: 2.00, 25.2%, 4.58:1, 1.25 cm, 0.10 cm.
- python-pptx is an independent oracle for AC-5. Its values were confirmed here:
  - title: 457200 / 274638 / 8229600 / 1143000 EMU
  - body: 457200 / 1600200 / 8229600 / 4525963 EMU
  - `txStyles`: title 44 pt, body 32 pt
  - the master has `p:bg`
- It parses XML safely (no entities, no network, size caps) and snapshots the JSON output.

## Rulings on the open questions

"Accept" means the plan's proposal becomes the spec, as written in the plan.

| Q | Topic | Ruling |
|---|---|---|
| 1 | Title without placeholders [P-18] | Accept, with **A-1** |
| 2 | Title excluded from body [P-25] | Accept, with **A-2** (one body definition) |
| 3 | KPI numeral | Accept: per shape, max run size ≥ 48 pt, whole text ≤ 5 words |
| 4 | Own fill as background; inclusive containment [P-26, P-27] | Accept both |
| 5 | Per-finding severity [P-14] | Accept |
| 6 | Bleed: no double report [P-20] | Accept |
| 7 | edge-margin one per shape, worst side; background = area test [P-21, P-17] | Accept |
| 8 | Pictures/charts/tables [P-19, P-16] | P-16 accepted. P-19 **amended by A-3** |
| 9 | Sort ties [P-13] | Accept |
| 10 | `measured` / `threshold` types [P-12] | Accept |
| 11 | Text-size cascade [P-5, P-6] | **A-4** |
| 12 | Other properties, fallback color [P-4, P-7] | Accept (fallback `tx1` via clrMap) |
| 13 | `clrMapOvr` [P-8] | Accept. The spec's "master's clrMap" was too narrow |
| 14 | alpha and other color models [P-9] | Accept |
| 15 | Background defaults [P-10] | `bgRef` solid → solid: accept. Missing `p:bg` and `noFill`: **A-5** |
| 16 | Placeholder matching [P-2] | **A-6** |
| 17 | Group rotation and flips [P-3] | Accept. Include the rotated inner group in the AC-6 fixture |
| 18 | dead-band scope [P-22] | Accept. Top and bottom bands count. The kpi slide-4 middle band (3.20 to 8.00 cm) firing is correct |
| 19 | box-overlap exemption [P-23] | Accept. The exemption could never apply and is removed (spec error) |
| 20 | body-too-small granularity [P-24] | Accept per shape. Word counting: **A-7** |
| 21 | font-count normalization [P-28] | **A-8** |
| 22 | title-underline window [P-29] | `content_width` accepted. Window: **A-9**. Outline-only lines are out of scope for M1 (backlog) |
| 23 | equal-card-row [P-30, P-31, P-32] | Accept all. "Linked" means every member is in one connected component |
| 24 | TOML on 3.10 [R-6] | **D-012**. Two `large_text` keys: accept |
| 25 | Adapter findings in the registry [P-15] | Accept |
| 26 | `check` without OfficeCLI [P-33] | P-33 accepted for JSON. Exit code: **A-10** |
| 27 | editorial-fixed re-spacing | Accept. Compressing gaps inside the bottom block counts as re-spacing. "No new warning" is judged in read mode (AC-4's mode). The candidate numbers are fine |
| 28 | AC-5 oracle | Accept (re-derived above) |
| 29 | `has_notes` text [P-1] | Accept |
| 30 | AC-9 scope | Accept: the whole process, including interpreter start |
| 31 | Commit identity [R-12] | **D-013** (trailers allowed) and **D-014** (current identity kept, no rewrite) |

## Amendments to append to the spec (verbatim)

- **A-1 (2026-09-24, audit 01).** Title selection. If a slide has a `title` or
  `ctrTitle` placeholder with text, that shape is the title. Otherwise use the plan's
  P-18 heuristic: the largest max run size among non-KPI text-bearing shapes, with
  ties going to the earliest in z-order.
- **A-2 (2026-09-24, audit 01).** One body definition. A body paragraph is a paragraph
  with `words > caption_exempt_words`. It applies to both `body-too-small` and
  `title-not-dominant`, and replaces the hard-coded "> 4 words". The title shape is
  never body.
- **A-3 (2026-09-24, audit 01).** `edge-margin` candidates are the plan's *visible*
  shapes: text-bearing, fill ≠ none, `pic`, or any `graphicFrame`. Background shapes
  and connectors are excluded. The plan's P-19 keyed on fill ≠ none, which excluded
  charts: a chart 0.5 cm from an edge would have passed.
- **A-4 (2026-09-24, audit 01).** Text property cascade:
  1. the run's `rPr`
  2. the shape's `lstStyle`
  3. the layout placeholder's `lstStyle`
  4. the master placeholder's `lstStyle`
  5. the master `txStyles` (`titleStyle` for title and ctrTitle, `bodyStyle` for
     other placeholders, `otherStyle` for non-placeholders)
  6. `presentation.xml` `defaultTextStyle`

  `a:pPr/a:defRPr` is dropped from the cascade (plan R-1). This follows the plan's
  statement of PowerPoint behavior, which the auditor could not verify against
  PowerPoint. `docs/adapter.md` records it as unverified.
- **A-5 (2026-09-24, audit 01).** Background default. If no `p:bg` exists on the
  slide, layout or master, or if `p:bgPr/a:noFill` is set, the background is
  `#FFFFFF`, plus one `adapter-unresolved` advisory (`what = background-default`).
  Reason: `unknown` would silently switch off `text-contrast` on every deck without
  an explicit background. PowerPoint paints these white.
- **A-6 (2026-09-24, audit 01).** Placeholder matching.
  - Slide to layout: match by `idx` first. If there is no idx match, fall back to the
    same `type`.
  - Layout to master: match by type, using the plan's type map.

  This is python-pptx 1.0.2's behavior (`SlidePlaceholder._base_placeholder` uses
  `layout.placeholders.get(idx=…)`; `LayoutPlaceholder._base_placeholder` maps the
  type). The AC-5 oracle and the adapter must share the same semantics, or AC-5 only
  tests python-pptx. The type fallback is keyline-only; document it.
- **A-7 (2026-09-24, audit 01).** Word counting. `words(text)` counts
  whitespace-separated tokens that contain at least one letter or digit, so
  separators such as `·`, `|`, `—` are not words.
- **A-8 (2026-09-24, audit 01).** Font family normalization.
  - Case-fold the name.
  - Strip one trailing token from `{thin, extralight, ultralight, light, regular,
    book, medium, semibold, demibold, bold, extrabold, ultrabold, black, heavy,
    condensed, narrow}`. Examples: "Calibri Light" → `calibri`, "Arial Narrow" →
    `arial`.

  Reason: weights and widths belong to one family. Counting them separately makes the
  Office default theme (Calibri Light + Calibri) look like two families before a
  second face has even been added.
- **A-9 (2026-09-24, audit 01).** `title-underline` window. The bar's top must lie in
  `[title.top + 0.5·title.h, title.bottom + 1.0 cm]`. That catches a bar drawn
  inside the lower half of an oversized title box. The other conditions are
  unchanged.
- **A-10 (2026-09-24, audit 01).** `check` exit code.
  - The exit code is lint's.
  - Render is best effort. If OfficeCLI is missing or render fails, print
    `render: skipped (<reason>)` to stderr and keep lint's code.
  - `--require-render` turns a render failure into exit 1.

  Reason: constitution II. The gate has to be passable where the skill runs.

## Decisions to append

- **D-012 · Python >= 3.11.** Use stdlib `tomllib`, with no custom TOML reader.
  - CI runs Python 3.11 and 3.13.
  - This supersedes the ">= 3.10" in CLAUDE.md and spec §1.
  - Why: 3.10 reaches end of life in October 2026 (PEP 619). The auditor's Claude
    sandbox runs 3.11.15. A 60-line parser that exists only to support a version
    dying next month is risk with no return.
- **D-013 · Commit trailers.** `Co-Authored-By: Claude … <noreply@anthropic.com>`
  trailers are allowed. The identity rule covers personal names and personal emails,
  not tool attribution. The AC-12 allowlist includes these trailers.
- **D-014 · Commit identity (decided by Tyler, 2026-09-24).**
  - Author and committer name: `Tyler` or `tyler-void`.
  - Email: `code@tyler-void.dev`.
  - Existing commits `ce21744` and `705edc1` stay as they are. There is no history
    rewrite and no repo recreation.
  - Why: Tyler accepts that the GitHub handle and this email are public. Given that, a
    rewrite would cost effort and achieve nothing, because GitHub keeps rewritten
    commits reachable by SHA anyway.
  - AC-12 allowlist:
    - the names and email above;
    - Claude co-author trailers (D-013);
    - GitHub's web-UI committer, `GitHub <noreply@github.com>`, so that merging from
      the web UI does not fail the test.

## Auditor findings not raised by the plan

- **F-1 (auditor's own error).** The CLAUDE.md identity rule ("the only author
  identities allowed anywhere… are Tyler and @tyler-void") was too broad. It made the
  implementer treat the Claude co-author trailer as a violation. Replace the Identity
  bullet with:

  > **Identity.** This is a public repo. No personal name other than "Tyler" or
  > "tyler-void"/"@tyler-void" may appear anywhere (code, docs, fixtures, commit metadata).
  > Commits use the approved identity in D-014. Tool-attribution trailers
  > (`Co-Authored-By: Claude …`) are allowed (D-013). Before the first commit in any
  > clone, check `git config user.name` and `git config user.email` against D-014.

- **F-2 (resolved).** The auditor flagged the commit email as a possible conflict with
  the project's identity rule. The auditor also noted that force-pushing leaves
  commits reachable by SHA, and that GitHub Support does not purge non-sensitive data
  (GitHub docs, "Removing sensitive data from a repository"). Tyler decided to keep
  the email (D-014). No action is needed.
- **F-3.** Tasks T-01, T-02 and T-05 have to change for D-012: set the floor to
  Python 3.11, use the CI matrix 3.11 and 3.13, and drop the flat-TOML reader and its
  parity test.
- **F-4.** Local only: the untracked `research.md` in the working-tree root duplicates
  `docs/research.md` (the implementer checked this with `cmp`). It can be deleted.
