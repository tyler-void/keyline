# Audit 02: phase A1 of spec 002

- **Auditor:** an external Claude session, plus a separate adversarial tester agent.
  Neither saw the implementing session.
- **Date:** 2026-09-29
- **Scope:** branch `002-skill-pack` at `447017a`, 30 commits over `main` `678c69a`.
  Report A1, with B-1 … B-8.

## Verdict

**FIX, then start A2.** A1 is solid work, and the regression evidence is clean. But one
defect breaks the gate's re-check loop (FX-1), and one hole lets an agent switch off
any gate (FX-2). The second hole comes from my own ruling. A2 starts after FX-1 …
FX-8 land, with B-9 … B-15 appended.

## What was verified and holds

- **Identity.** All 30 commits are `Tyler <code@tyler-void.dev>` as author and
  committer, each with the Claude trailer (D-013, D-014).
- **Integrity:**
  - `product.toml` hashes to `9b0fea6e…`, `numbers_ref.py` to `af534e21…`, and
    `amendment-B8-voices.md` to `b83deb22…`; all three match the handoff.
  - `spec.md` +188/−0 since `926ab7f` (the amendment log only).
  - `docs/decisions.md` +81/−0, `docs/lessons-learned.md` +21/−0, `docs/adapter.md`
    +24/−0.
  - `thresholds.toml`: no line removed.
- **Fixtures.** Every fixture file on `main`, all `.pptx` included (golden, rule,
  foreign, stress), is byte-identical at HEAD. The only changed files are the builders
  `expect.toml`, `_deck.py` and `build_rules.py`, and `expect.toml` has no removed
  line. The T-05 incident (`3e8f270`) left no trace.
- **Changes to spec 001 tests** are exactly AC-2's list: the listing (35 ids, `since`
  in {0.1.0, 0.2.0}), the harness (`pack`, `voice`, `brief`), and `--engine officecli`
  on the two OfficeCLI tests. `test_config.py` only adds tests.
- **Checks.**
  - `ruff check .` and `ruff format --check .` are clean.
  - `tools/m1_baseline.py` reports no differences.
  - `pytest` gives **610 passed, 1 failed** in the auditor's sandbox (LibreOffice
    24.2.7.2, OfficeCLI 1.0.152).
  - The failure is environmental. `test_auto_falls_back_to_officecli_without_soffice`
    builds a PATH that holds only the `officecli` symlink, and here `officecli` is the
    npm launcher (`#!/usr/bin/env node`), so node isn't found. See FX-4.
- **Regression, main against branch.** 308 (deck, mode) pairs:
  - the whole stress corpus: 131 files, including the malformed ones;
  - the 23 LibreOffice template decks from A-006.

  JSON and exit codes are **byte-identical** in all 308, with 0 tracebacks.
- **Adversarial pass** (separate agent, about 35 min, 115 tool calls). What held:
  - 1,000,000 seeded strings through `numtokens`, with 0 disagreements with the oracle;
  - 2,023 type mutations of briefs and evidence files, all clean exits except the
    directory-path cases in FX-5;
  - byte-identical output under 6 hash seeds and under `ascii`, `cp1252` and
    `LC_ALL=C`;
  - all three voices × two modes × seven layouts with 0 pack findings;
  - 300-error validate output parsed;
  - a 400-slide render.

  Its findings drive FX-1 … FX-8.
- **B-8.** The three stock voices' checks match the amendment's table to the printed
  precision. The neutral templates rebuild byte-identically. `keyline rules` lists 35
  entries. A LibreOffice preview of all three voices on four layouts (auditor-built
  with python-pptx, so no pen and no keyline rule) shows the voices apply to
  background, text, section inversion and fonts. Georgia renders as a substitute here
  because Gelasio is missing.

## Fix items

### FX-1 · Blocker · OfficeCLI's resident process makes validate and render stale

- **Evidence.**
  - `officecli validate` and `view … screenshot` start a resident process that keeps
    the deck in memory for about 60 s. A second call on the same path in that window
    reads memory, not disk.
  - Auditor's re-run of the tester's repro:
    - (A) clean deck checked, file replaced with the AC-14b bogus deck, checked again:
      `ooxml-invalid = 0`, expected 1.
    - (B) the reverse: 1, expected 0.
  - The officecli render is stale the same way.
  - The skill loop is build, check, fix, rebuild, re-check. So the re-check validates
    the old deck.
  - Spec 001's `keyline render` has had the same latent bug since M1.
- **B-14 (to append).** Every OfficeCLI invocation (validate, screenshot):
  - works on a private temp copy with a unique file name;
  - runs `officecli close <copy>` in a `finally`;
  - deletes the copy.

  keyline never passes the user's deck path to OfficeCLI.
- **Test:** sequences A and B as an `officecli` test, each run twice in a row inside
  60 s.
- **Lesson L-016:** OfficeCLI caches documents in a resident process; always work on
  copies.

### FX-2 · Major · `accepted` can switch off any gate

- **Evidence.**
  - A brief whose inline voice lists `fiction-undisclosed`, `unsourced-number`,
    `brief-slide-count` or `voice-contrast` in `accepted` turns those findings into
    advisories. `drift-undisclosed.pptx` then exits 0 (auditor re-ran it).
  - The agent writes the brief, so it can waive its own gates.
  - This is my error: B-8.2 added `accepted` to voices without a limit, and my Q-24
    ruling ("any registry id") set the precedent. Q-31 followed it.
- **B-10 (to append).**
  - `accepted` in a pack, a pack voice or an inline voice may list only the rules in
    `acceptable_rules`. This is new data in `thresholds.toml` `[common]`: `claude-look-palette`,
    `voice-claude-look`, `closing-cliche`, `accent-overuse`, `equal-card-row`,
    `title-underline`.
  - Each entry needs a non-empty `reason`.
  - Anything else is a schema error (exit 1).
  - This supersedes the Q-24 and Q-31 rulings.

### FX-3 · Major · Render numbering and render hygiene

- **Hidden slides.** LibreOffice drops hidden slides from the PDF, so `slide-02.png`
  can show deck slide 3, while the officecli engine renders every slide.
  - The auditor checked on LibreOffice 24.2 that the PDF filter option
    `ExportHiddenSlides=true` restores them: a 4-slide deck with one hidden slide gave
    4 pages instead of 3. The option is passed as
    `--convert-to 'pdf:impress_pdf_Export:{"ExportHiddenSlides":{"type":"boolean","value":"true"}}'`.
- **Other gaps:**
  - a 0-slide deck gives a blank PNG under LibreOffice but exit 1 under OfficeCLI;
  - old `slide-*.png` files survive in a reused output directory;
  - a timeout kills only `soffice`, not `soffice.bin`, and leaves its temp directory
    behind;
  - a `-o` that is a file makes `check` exit 1, with a message blaming a lint rule.
- **B-13 (to append):**
  - `slide-NN.png` is deck slide NN in every engine; LibreOffice exports hidden slides
    with the option above.
  - A deck with no slides makes `render` exit 1 ("deck has no slides"), and `check`
    prints `render: skipped (deck has no slides)`.
  - `render` deletes existing `slide-*.png` and `contact.png` in the output directory
    before writing.
  - PNG names are zero-padded to max(2, number of digits in the slide count).
  - A timeout kills the whole process group and removes the temp directory.
  - An unusable `-o` is a render failure: `render` exits 1 with one line, and `check`
    prints `render: skipped (…)` and keeps lint's exit code (A-10).

### FX-4 · Major · The validate step's error paths

- **OfficeCLI's error envelope.** When OfficeCLI cannot open a deck, it returns
  `{"success": false, "error": {"error": "…"}}`. keyline reports this as "output not
  understood: {".
- **OfficeCLI that cannot run.** If `officecli` is on PATH but cannot start (no node
  for the npm launcher):
  - `check` adds an `ooxml-invalid` finding, so a clean deck exits 2;
  - doctor still says `VALIDATE_OFFICECLI`.
- **B-15 (to append):**
  - An error envelope becomes one `ooxml-invalid` finding that carries its message.
  - An OfficeCLI that cannot start counts as absent:
    `validate: skipped (officecli could not run: <first line>)`, with the exit code
    unchanged.
  - doctor reports `NO_VALIDATOR` with that reason.
- **Test fix:** `test_auto_falls_back_to_officecli_without_soffice` also puts node's
  directory on its PATH, or skips when `officecli` is a node script and node is not
  reachable from the constructed PATH.

### FX-5 · Minor (many) · Schema tightening and one-line errors

This covers X-5 … X-8, X-15, X-17 and Q-32.

- **B-12 (to append).** All of these are schema errors (exit 1, one line, naming the
  file and key), never "internal error":
  1. Ids, hex values and names use full-string matches (`fullmatch`). For example, a
     trailing `\n` must not pass.
  2. A headline or a `reads` item containing a line break (`\n`, `\r`, `\v`, U+2028 or
     U+2029). The spine is one line per slide.
  3. A brief's `voice` value with a path separator, or ending in `.toml`, per B-8.4.
     `--voice` on the CLI may still be a file (Q-35).
  4. An accent role with the same hex as a non-accent role (Q-32, accepted).
  5. In `pack.toml`: an empty `modes`; any table or value of the wrong type (every table
     in the loader is type-checked); `grid.columns < 1`; non-finite numbers.
  6. `lint` or `check` with `--pack … --mode M` where the pack lacks M. This is B-4 on
     the CLI path.
  7. A brief, evidence, pack or voice path that is a directory, cannot be read, is not
     UTF-8, or nests beyond the parser's limit.
- **`--pack NAME` resolution** (X-17). A bare name means the bundled pack. A path needs
  a separator or a leading `.`. So a local directory can no longer shadow a bundled
  pack.

### FX-6 · Minor · Source and note line detection

- **What goes wrong:**
  - A no-break space (or narrow no-break space) between "Source" and the colon defeats
    detection. That is the French typographic form.
  - Classification reads `p.text`, including invisible runs, while §4.4 scans only
    inked text. So an invisible "Source: " prefix hides a visible number from the scan.
- **B-12 (continued):**
  - The "optional spaces" of §3.1 are any Unicode space separators (category Zs) and
    tabs.
  - Classification uses the paragraph's inked text, the same text §4.4 scans.
  - Source lines inside table cells are out of scope for now; document this in
    `check.md`.

### FX-7 · Minor · The `night` voice and exact font names

- **Q-34, overruled.** `night`'s ink `ECECE8` (C\* 2.06, h 110) is inside the cream band,
  and it *is* a background: the section surface. My pick was careless, and B-8.5
  checked only `paper`.
- **B-9 (to append):**
  - `voice-claude-look` tests every palette role that a system surface uses as a
    background (Swiss: `paper` and `ink`).
  - `night`'s ink becomes **`ECECEC`**. Auditor's checks: C\* 0.00; ink/paper 15.06;
    paper/ink 15.06; accent_on_ink/ink 5.02. No stock voice then has any `voice-*`
    finding.
- **B-11 (to append).** `off-pack-font` compares family names exactly, after casefold
  and whitespace collapse, as voice fonts already do (deviation 7).
  - The reason: A-8's weight stripping let "Arial Black" and "Arial Narrow" pass as
    Arial.
  - `font-count` keeps A-8.

### FX-8 · Minor · Record the limits

- **Tokenizer.** Extend B-5's known limits (for `check.md`):
  - "B2B" gives `2B`, "4K" gives `4K`, "COVID-19" gives `19`, "iPhone 15" gives `15`;
  - "5 %" with a no-break space gives a non-significant `5`.
- **Lesson L-016** (FX-1) goes in `docs/lessons-learned.md`.

## Rulings on Q-26 … Q-41

| Q | Ruling |
|---|---|
| 26 | Accept |
| 27 | Accept |
| 28 | Accept |
| 29 | Accept (a), (b) and (d). (c) stands, with one addition for A2: the pen **refuses** (`PenError`) to build with a voice that has an error-level `voice-*` finding |
| 30 | Accept, with FX-5 item 1 (`fullmatch`) |
| 31 | **Overruled** by B-10 |
| 32 | Accept. It becomes a schema error under B-12 |
| 33 | Accept. Checked in PowerPoint at G-1 with the `night` specimen: a new text box must be readable |
| 34 | **Overruled** by B-9 |
| 35 | Accept for the CLI. A brief's `voice` is a name only (B-12 item 3) |
| 36 | Accept |
| 37 | Accept |
| 38 | Accept |
| 39 | Accept |
| 40 | Accept |
| 41 | **Install the twins before A2**, so AC-13(a) covers all six families on Tyler's machine. Commands are in the handoff note |

## Rulings on the deviations

All nine are accepted.

- **Deviation 2** (slide = position in `sldIdLst`) is better than the spec's wording.
- **Deviation 4** relies on python-pptx's private `rel._target`. That is acceptable for
  a fixture builder, but pin the python-pptx version in the builder's docstring.

## Auditor's own errors this round

1. B-8.2 put `accepted` in voices without a limit, and my Q-24 ruling allowed any
   registry id. Together they opened FX-2.
2. The `night` ink value, and B-8.5 testing only `paper` (FX-7).
3. B-8 said nothing about OfficeCLI's resident process. The spec 001 render audit also
   missed it. Nobody tested a re-run inside 60 s.

## Amendments to append (verbatim)

B-9 … B-15, as written in FX-1 … FX-7 above:
- B-9: FX-7, `voice-claude-look` and `night`'s ink;
- B-10: FX-2, `accepted`;
- B-11: FX-7, `off-pack-font`;
- B-12: FX-5 and FX-6, schema tightening and source-line detection;
- B-13: FX-3, render;
- B-14: FX-1, OfficeCLI copies;
- B-15: FX-4, the validate step.

Each is dated 2026-09-29, audit 02.

## Carry into A2

- **B-7 first:** measure line pitch and the wrap margin on LibreOffice 26.8.0.3 before
  any fit constant is used.
- **Figure sub-boxes:** the numeral and the label each get their own box inside the
  figure region (audit 01 note).
- **The pen refuses error-level voices** (Q-29 addition).
- **AC-8 again,** on a pen-built deck (B-3).
