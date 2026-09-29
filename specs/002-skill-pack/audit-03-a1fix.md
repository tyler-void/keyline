# Audit 03 of spec 002: the A1 fix round (FX-1 … FX-8)

- **Audited:** branch `002-skill-pack` at `b7d58c2`, fresh clone, 2026-09-29.
- **Auditor:** the external session. **Decides:** Tyler.
- **Verdict: FX-1 … FX-8 ACCEPTED. Then a short FIX round (FX-9 … FX-15), then A2.**
  Every audit 02 repro now behaves as B-9 … B-15 require. A deeper adversarial pass
  found seven new items, all minor or trivial, in the same code (engines, schema,
  messages). None affects the pen. They land first, as "A1 fixes, round 2", and A2
  starts after them without another audit stop. The A2 audit re-checks them.

## 1. What was checked, and how

| check | command (auditor's sandbox) | result |
|---|---|---|
| Identity | `git log 447017a..HEAD --format='%an <%ae> %cn <%ce>'` | 13 commits, all `Tyler <code@tyler-void.dev>`, each with one Claude trailer (D-013, D-014) |
| Docs append-only | `git diff 447017a..HEAD -- spec.md docs/decisions.md docs/lessons-learned.md \| grep '^-[^-]'` | no removed lines |
| B-9 … B-15 verbatim | compared with audit 02 | identical text, dated, in order; "B-12 continued" is its own entry |
| Audit 02 file | `sha256sum` | `2bb1ee02…` in the repo equals the auditor's copy |
| Protected files | `sha256sum product.toml numbers_ref.py`; `git diff 447017a..HEAD -- fixtures/golden` | `9b0fea6e…`, `af534e21…`; goldens untouched |
| Fixture changes | `git diff 447017a..HEAD -- fixtures/` | three rebuilt decks, one new brief; each justified below |
| Lint | `ruff check` and `ruff format --check` on `src tests fixtures tools` | clean, 147 files |
| Tests | `pytest -q` | **669 passed, 1 failed**: the failure depends on the environment (FX-15) |
| M1 baseline | `python tools/m1_baseline.py` | `baseline: no differences` |
| Regression | main vs branch, `lint --json`, 154 decks × 2 modes | 308 pairs, 0 differing, 0 tracebacks |
| Brief fuzz | type mutation of every key in the brief and evidence files (subprocess) | 2,023 cases, 0 internal errors, 0 multi-line errors |
| Pack and voice fuzz | the same, in process, on `pack.toml` and `neutral.toml` | 0 internal errors (audit 02: many) |

### Fixture changes, justified

- `off-pack-font--pos` gains "Arial Black" and "Arial Narrow". This is B-11's reason,
  now under test.
- `off-pack-font--neg` replaces "Arial Bold" with `"  ARIAL "`. The negative case now
  tests casefold and whitespace collapse, which B-11 keeps.
- `pack-voice-night` is rebuilt with B-9's ink.
- `voice-accepted-gate.brief.toml` is new. It is B-10's gate case in `expect.toml`.
- Changed assertions in older tests all follow a ruling: B-9 replaces Q-34's pinned
  test; B-10 replaces the `dead-band` example; X-17 changes one path to `./swiss`. None
  of them weakens a check.

## 2. Audit 02's repros, re-run

| item | repro | before | now |
|---|---|---|---|
| X-1 (FX-1) | `stale_validate.sh`, sequences A and B | A: 0 then 0; B: 1 then 1 | A: 0 then 1; B: 1 then 0. No resident left |
| X-2 (FX-2) | inline voice accepting `fiction-undisclosed`, then lint `drift-undisclosed` | exit 0 | brief exits 1, one line naming `acceptable_rules` |
| Hidden slide (FX-3) | render `hidden 2 of 4 – ảnh.pptx`, both engines | LibreOffice skipped slide 2 | 4 PNGs in each engine, slide 2 is the hidden one |
| Stale PNGs (FX-3) | a planted `slide-09.png` and `contact.png` | kept | deleted; an unrelated `keep.txt` survives |
| Zero slides (FX-3) | `render zero.pptx`; `check zero.pptx` | a bogus PDF note | exit 1 "deck has no slides"; check prints `render: skipped (…)`, exit 0 |
| Padding (FX-3) | 400-slide deck | two digits | `slide-001` … `slide-400` |
| Timeout (FX-3) | `LO_TIMEOUT_S = 0.7` on 400 slides | soffice left running | RenderError after 0.9 s; no soffice, no temp directory |
| X-4 | `check -o <file>` | traceback | `render: skipped (… not a directory)`, lint's exit kept |
| X-5 | directory, deep nesting, wrong types, a latin-1 `pack.toml` | internal errors | one line each, exit 1 |
| X-6 | `--pack … --mode read` on a presented-only pack | exit 0 | exit 1, "pack swiss has no read mode" |
| X-7 | brief `voice = "../…/neutral.toml"` | resolved against the CWD | "is a path; a brief names a voice of its pack" |
| X-8 | evidence id with a trailing `\n` | accepted | exit 1 |
| X-9 (FX-4) | a deck OfficeCLI cannot open | JSON envelope dumped | one `ooxml-invalid` finding carrying the message |
| X-9b (FX-4) | `officecli` present but `node` missing | exit 2 | `validate: skipped (officecli could not run: …)`, exit 0; doctor `NO_VALIDATOR` |
| X-13, X-14 (FX-6) | NBSP before the colon; an invisible "Source: " run | missed; hid a number | detected; `unsourced-number` fires |
| X-15 | `\n` in a headline | forged spine lines | "must be one line" |
| X-17 | a local `./swiss` with a broken `pack.toml`, then `--pack swiss` | local directory won | bundled pack used; `--pack ./swiss` reads the local one |
| B-9 | inline voice: paper `16181B`, ink `F3EBDD`, accent_on_ink `B5533A` | not checked | `voice-claude-look` warning names the ink; accepting it with a reason makes it advisory |

## 3. New findings

A separate adversarial agent attacked B-9 … B-15. It had not seen this audit's work.
I re-ran each item below myself before listing it. Severity follows audit 02:
nothing here gives a false pass on a gate.

### FX-9 · Minor · LibreOffice cannot render a symlinked deck, or a name ending in "."

- **Repro:**
  ```
  ln -s real-target.pptx link.pptx
  keyline render link.pptx -o out --engine libreoffice
  ```
  - Observed: exit 1, "libreoffice wrote no PDF: convert …/real-target.pptx … -> …/real-target.pdf".
  - A copy named `deck.` fails the same way.
- **Cause:** soffice converts `deck.resolve()`, but keyline looks for `{deck.stem}.pdf`.
- **Fix (B-19):** LibreOffice also converts a private copy. It lives in the render's
  temp directory under a fixed name (`deck.pptx`, or `deck.pptm`), and keyline reads
  `deck.pdf`. The user's path then never reaches either engine.

### FX-10 · Minor · The OfficeCLI copy keeps the user's suffix

- **Repro:** `keyline check "clean v1.2" -o o`, where "clean v1.2" is `golden/editorial.pptx`.
  - Observed: `ooxml-invalid · Unsupported file type: .2`.
  - `clean.pptx` gives no such finding. `deck.pptx.bak` fails the same way.
- **Principle III** (accept every .pptx) is about the file's content, not its name.
- **Fix (B-19):** the copy is named `deck-<uuid>.pptx`. It is `.pptm` only when the
  user's suffix is `.pptm`, compared case-insensitively.

### FX-11 · Minor · Engine hygiene under odd output, signals and an empty `-o`

1. **Output that is not UTF-8 crashes keyline.**
   - A shim `officecli` that writes `Fehler: \xfcberlauf` to stderr and exits 1 makes
     `check` and `doctor` print "internal error … UnicodeDecodeError".
   - The message also names the wrong context ("while reading rule title-underline").
   - Cause: `text=True` in `officecli.status()`, `validate.py` and `render.py`.
2. **A validate timeout orphans the native process.**
   - `subprocess.run(timeout=…)` kills only the node launcher.
   - With `TIMEOUT_S = 0.4`, the native `officecli validate` is re-parented to PID 1.
     It then starts `__resident-serve__` on the copy after keyline has run `close`.
   - B-14's guarantee still holds, because the copy's name is unique. But the resident
     outlives the run.
3. **SIGTERM and SIGINT skip the cleanup.**
   - `timeout 0.9 … check` (and 1.2, 1.5) left one `/tmp/keyline-oc-*/deck-<uuid>.pptx`
     per run. Python's default SIGTERM does not run `finally`.
   - SIGINT to keyline's process group (a terminal Ctrl-C) during a 120-slide
     LibreOffice render: keyline dies with −2, `soffice.bin` keeps running (it is in
     its own session), and `/tmp/keyline-lo-*/profile` is left behind.
4. **`render -o ''` means the current directory.**
   - It deleted a planted `slide-99.png` and overwrote `contact.png` there.
- **Fix (B-19):**
  - Decode every engine's output as UTF-8 with `errors="replace"`.
  - `validate` runs in its own process group, like `render`, and a timeout kills the
    group.
  - SIGINT and SIGTERM take the timeout path: kill the child's group, `officecli close`
    the copy, remove the temp directories, then exit 130 or 143.
  - An empty `-o` is an unusable `-o` (B-13).

### FX-12 · Minor · A voice's `accepted` written as the spec shows it does nothing

- **My error.** B-8.2's example puts `accepted = []` after `[why]`. TOML reads that
  line as `why.accepted`. Plan Q-30, which I accepted, says `[why]` keys that are not
  roles are ignored.
- **Repro:** `neutral.toml` renamed `spec.toml`, with these lines at the end:
  ```
  accepted = [{ rule = "unsourced-number", reason = "" }]
  wobble = "x"
  ```
  `keyline lint base.pptx --pack swiss --voice ./spec.toml` exits 0 in silence.
- **Impact:** it fails safe, since nothing gets waived. But a list with a banned rule
  and an empty reason passes every B-10 check. Anyone who copies the example gets a
  list that does nothing.
- **Fix (B-18):**
  - A voice schema is closed, in a voice file and in an inline `[voice]`. The allowed
    keys are:
    - top level: `schema`, `name` (file only) and `accepted`;
    - `[fonts]`: `display` and `text`;
    - `[palette]` and `[why]`: exactly the palette roles.
  - Any other key is a schema error that names it. A key called `accepted` inside
    `why` gets the hint "accepted belongs before [fonts]".
  - This supersedes Q-30's "ignored" clause. Evidence files keep §4.1's
    unknown-keys rule, because they hold material for the brief.

### FX-13 · Minor · An unreadable pack or voice path is an internal error

- **Repro:** run as `nobody`, with `locked/` at mode 700:
  - `keyline lint base.pptx --pack ./locked/pk --voice neutral`
  - `--voice ./locked/pk/voices/neutral.toml`
  - Both give "internal error while reading the deck: PermissionError".
  - A brief in the same place already gives one line.
- **Cause:** `Path.exists()` in `packs.resolve` and `voices.load` runs outside
  `read_toml`'s error handling.
- **Fix:** B-12 item 7 already covers it. Route those checks through the same handler,
  and give the error context its real name.

### FX-14 · Trivial · Schema and message details

- **An invisible reason passes.** A reason of `"​"` or `"﻿"` counts as
  non-empty.
  - Fix (B-20): a reason needs at least one character outside categories Zs, Cc and Cf.
- **`schema = true` and `schema = 1.0` pass.** Python treats both as equal to 1.
  - Fix (B-20): `schema` is an integer and not a bool, in briefs, evidence, packs and
    voices.
- **User values can break the one-line rule.**
  - `--pack $'swiss\nkeyline: all clear'` prints a forged second line.
  - A brief with `pack = "swiss\n"` prints a blank line.
  - Fix (B-20): every user-supplied value in a message is escaped (`repr`-style), so
    one error is always one line.
- **Garbled messages:**
  - "pack.toml: acceptedpack.toml: top level: missing key 'accepted'";
  - `theme.dk1 = 5` gives "must be a list of strings";
  - "p-deep/pack.toml pack.toml nests too deeply";
  - "tmp: brief tmp is a directory".
  - Fix: name the file once, then the key.

### FX-15 · Test and docs

- **`test_auto_falls_back_to_officecli_without_soffice` depends on the machine.**
  - Its PATH holds only `officecli` and `node`. OfficeCLI finds its headless browser
    through PATH here (the `playwright` CLI), so the screenshot fails: "No headless
    browser available".
  - The test means to check engine *selection*. Assert that the L-002 note appears.
    Skip when OfficeCLI itself reports "No headless browser".
  - CI skips it anyway, because CI has no OfficeCLI.
- **Noise.** `render` prints the L-002 note even when OfficeCLI cannot start and the
  render is skipped. Print the note only when OfficeCLI actually renders.
- **Known limit** for the `numtokens` docstring and Phase B's `check.md`:
  - "inked" means a run with a fill, as §4.4 defines it;
  - a "Source: " run in a fully transparent or background-coloured fill still counts
    as a source line.
  - This is the M1 stance on adversarial decks (principle VIII: the gate targets
    accidents, not an author gaming it). Record it; do not fix it.

### Tried and held

These were attacked and held:
- B-14: every argv a logging shim recorded was a `/tmp/keyline-oc-*` copy. Odd names,
  `.PPTX`, no suffix, a symlink, three concurrent checks of one deck, and a rebuild
  inside 60 s all behaved.
- B-13:
  - a reversed `sldIdLst`, with both pypdfium2 and pdftoppm;
  - `-o` set to a file, `file/sub`, `/proc`, `/dev/null`, or an unwritable directory;
  - a symlinked stale PNG: only the link is removed.
- B-10:
  - case variants of a rule id, a U+2010 lookalike, a trailing space;
  - tab or ideographic-space reasons;
  - a table given instead of a list.
- B-12:
  - `fullmatch` on fullwidth digits;
  - every line break;
  - a voice path given with a backslash;
  - an accent equal to ink, in any case.
- B-12 continued: all 17 Zs characters and a tab before the colon, NFD input, a hidden
  colon.
- B-11: flags a fullwidth "Arial" and "Arial" with a zero-width space; passes "ARIAL"
  and "Arial" with a trailing NBSP.

## 4. Claude Code's two questions

1. **X-17 in the log.** Yes, record it. B-12 is already appended verbatim and the log
   is append-only, so X-17 becomes its own entry, **B-16**. The miss is mine: audit 02
   wrote X-17 as a bullet, not as a "B-n (to append)" paragraph.
2. **The line-break set.** Accept the superset, and record it as **B-17**.
   - The rule's intent is "one line per slide".
   - Every character `str.splitlines()` breaks on is a break somewhere: python-pptx
     turns `\v` into `<a:br/>`, and U+0085 is NEL. `\x1c` … `\x1e` are not even legal
     in XML 1.0.
   - B-12's list of five was my under-count.

## 5. Rulings on A2 (T-20 … T-32, Q-42 … Q-46)

The tasks carry everything from audit 02's "Carry into A2": B-7 first, figure sub-boxes,
the pen refusing error-level voices, and AC-8 on a pen-built deck. LibreOffice 26.8 was
released in August 2026 (9to5Linux, Phoronix), so T-20's target version exists.

| Q | Ruling |
|---|---|
| 42 | **Accept, with one change:** every stem names its voice (`swiss-specimen-presented-neutral`, `-presented-night`, `-read-field`), so a fourth voice never forces a rename. They share one evidence file |
| 43 | **Accept, with three additions:** (a) both boxes span the region's full width, and the label is top-anchored; (b) a region shorter than the numeral's rows plus one label line raises `DoesNotFit`, naming both; (c) the two boxes touch but do not overlap, so `box-overlap` stays silent (a test asserts it) |
| 44 | **Accept, with two additions:** (a) the probe decks name the **portable family** (Arial, Georgia, …), not the twin, so the measurement goes through fontconfig's substitution exactly as a pen deck does. The script prints `fc-match <family>` for each family and stops if any does not resolve to its twin. (b) Every measured constant is stored with the LibreOffice version that produced it (principle IV) |
| 45 | Accept |
| 46 | **Accept, with one test:** the in-memory template for (neutral, mode) is byte-identical to the committed file, so the files never drift from what the pen uses |

- **T-22.** AC-13(a) passes between 0.995 and 1.25. The report also gives the largest
  ratio per twin. Any plain-Latin string above 1.05 is flagged: that would be an
  estimator refusing text that fits. This is informational, not a failure.
- **T-20.** Record the actual `soffice --version` at run time. If it is not 26.8.0.3,
  say so; the stop-and-report rule applies unchanged.

## 6. Auditor's own errors this round

1. B-8.2's TOML example placed `accepted` after `[why]`. That is the trap Claude Code
   had already logged twice. My Q-30 ruling then made the mistake silent (FX-12).
2. B-12 item 2 listed five line-break characters; `splitlines()` breaks on ten.
3. Audit 02 gave X-17 no "to append" paragraph, so it had no place in the log.

## Amendments to append (verbatim)

- **B-16 (2026-09-29, audit 03).** `--pack NAME`: a bare name always means the bundled
  pack. A pack directory needs a path separator or a leading `.`, so a local directory
  can never shadow a bundled pack (X-17, implemented in `275082a`).
- **B-17 (2026-09-29, audit 03).** B-12 item 2's line breaks are every character that
  `str.splitlines()` breaks on: `\n`, `\r`, `\v`, `\f`, `\x1c`, `\x1d`, `\x1e`,
  U+0085, U+2028 and U+2029. This supersedes the list of five.
- **B-18 (2026-09-29, audit 03).** A voice's schema is closed, in a voice file and in an
  inline `[voice]`.
  - Allowed keys:
    - top level: `schema`, `name` (file only), `accepted`;
    - `[fonts]`: `display`, `text`;
    - `[palette]` and `[why]`: exactly the palette roles.
  - Any other key is a schema error naming it. This supersedes plan Q-30's "`[why]`
    keys that are not roles are ignored".
  - B-8.2's example is corrected: `accepted` goes before `[fonts]`, because a key
    written after a table header belongs to that table:

    ```toml
    schema = 1
    name = "…"
    accepted = []   # optional { rule, reason }; B-10 limits the rules
    [fonts]
    display = "…"
    text = "…"
    [palette]       # exactly the system's palette_roles, 6-digit hex
    [why]           # role → one line naming where the colour comes from
    ```
- **B-19 (2026-09-29, audit 03).** Engine hygiene, extending B-13 and B-14:
  - LibreOffice also converts a private copy, with a fixed name, in the render's temp
    directory.
  - OfficeCLI copies are named `.pptx` (`.pptm` only for a `.pptm` deck), whatever the
    user's file name.
  - Engine output is decoded as UTF-8 with replacement.
  - `validate` runs in its own process group, and a timeout kills the group.
  - SIGINT and SIGTERM run the timeout cleanup, then exit 130 or 143.
  - An empty `-o` is an unusable `-o`.
- **B-20 (2026-09-29, audit 03).**
  - An `accepted` reason needs at least one character outside Unicode categories Zs, Cc
    and Cf.
  - `schema` is an integer, not a bool or float, in every file.
  - Every user-supplied value in an error message is escaped, so one error is one line.
