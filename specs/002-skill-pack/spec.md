# Spec 002: skill, brief and the Swiss pack

- **Milestone:** M2 (vision: "Skill: brief, craft floor, ANTI-TELLS, first style pack").
- **Status:** approved for planning once Tyler confirms D-015 … D-019 (§0). Stop after
  `plan.md` and `tasks.md`.
- **Decides:** Tyler · **Audits:** an external session, by cloning the repo.
- **Append-only:** amendments go in the log at the bottom, with a date.
- **Builds on:** spec 001 as amended (A-1 … A-19). "A-n" below always means a spec 001
  amendment.

## Goal

An agent on claude.ai web, Claude desktop or Claude Code can take a subject and produce
an editable `.pptx` that looks designed. It gets there by:

1. **A brief** that fixes the direction before any slide exists: mode, thesis, own
   world, motif, and the headline spine with each slide's "reads".
2. **Evidence on hand**: every number the deck shows comes from a file, with a source.
3. **A pen** that builds slides only from a style pack's tokens and refuses content
   that does not fit, instead of shrinking it.
4. **The first style pack, Swiss**, with guards against the "Claude look" (L-007).
5. **The gate** (`keyline check`), now aware of the pack and the brief, with a render
   engine that exists where the skill runs.
6. **One skill**, packaged as a ZIP, with a thin router and short playbooks.

The canonical demo is **BonsaiHub**, a fictional parody product (D-019), built twice:
a presented pitch and a read pre-read (D-018).

## Out of scope

Font embedding and `@font-face` renders (M3), Claude Code hooks (M3), a finish-reviewer
subagent, commands beyond the three routes in §8 (polish, bolder, quieter …), a second
pack, `.potx` corporate templates, MCP, render-based rules, calibration and any
benchmark. Lint 0.2 P1 items from spec 001's backlog (FP-2 layout/master shapes, CJK
word counting) stay in the backlog; §5 keeps the pack clear of FP-2. Do not build ahead.

## 0. Decisions this spec depends on

Append these to `docs/decisions.md` in the first task, after Tyler confirms them.

- **D-015 · The pen is a token API independent of its writer. The M2 writer is
  python-pptx, on every surface. OfficeCLI renders, validates and edits.**
  Supersedes the "OfficeCLI builds decks" half of D-003. Tyler chose this over two
  writers (option A, 2026-09-27).
  - **One writer everywhere.** python-pptx writes on claude.ai, on Claude desktop, and
    on Claude Code on Tyler's machine. The agent only ever calls the pen, so the
    writer underneath is invisible to it.
  - **OfficeCLI's roles:**
    - a render engine (§7);
    - `officecli validate` in `check` wherever OfficeCLI is installed (§7);
    - later, a second writer for features only it has, such as morph transitions;
    - later, editing existing decks that the pen did not build (M3, route "check a
      deck → fix").
  - The lint core is unchanged (constitution VII): it never imports python-pptx or
    calls OfficeCLI.
  - Why:
    - python-pptx (with lxml and Pillow) is pre-installed in the Claude API's
      code-execution container, which runs Python 3.11. That list is documented.
      claude.ai does not publish its own list, but it allows installs from PyPI by
      default (sources below).
    - OfficeCLI's npm package downloads a 34 MB binary at install time
      (`install-binary.js`: `d.officecli.ai`, with GitHub releases as fallback). On
      claude.ai that happens again in every fresh sandbox, and it fails where network
      access is off.
    - The pen needs layout and placeholder control. python-pptx exposes it directly and
      avoids the positional-path quirk (L-001).
    - OfficeCLI 1.0.152 output is not byte-stable. Two identical runs gave different
      files, because relationship ids are random (`R93086a6bc0…`) and
      `docProps/custom.xml` records the build time. python-pptx differs only in zip
      timestamps and chart workbooks, and both are normalizable (§6.5). (Auditor's
      test, 2026-09-27.)
    - A second writer in M2 would add no M2 feature. The cost would be the writer
      twice, an id-renumbering pass and parity tests.
  - LibreOffice 24.2 rendered the editorial golden deck to PNG through
    PDF in the auditor's sandbox (about 1.2 s warm). That it is available on claude.ai
    is inferred, not verified: Anthropic's own pptx skill calls `soffice`. `doctor`
    (§7) reports what is present.
- **D-016 · Briefs and evidence are TOML; slide roles live in layout names.**
  `tomllib` is stdlib (D-012), so no new dependency. A pen-built slide carries its
  role in its layout name (`keyline:<role>`, §2). The role therefore survives editing
  in PowerPoint, and lint needs no sidecar file to read it.
- **D-017 · Swiss pack v1 uses Arial only.** Until M3 can embed fonts, the pack uses a
  family that PowerPoint on Windows and Mac, Keynote and Google Slides all have. Liberation Sans is
  metric-compatible (OFL), so LibreOffice renders and the pen's fit estimate come
  close to PowerPoint's line breaks. §6.4 keeps a 1 % safety margin because they are
  not identical. Revisit when M3 font embedding lands.
- **D-018 · Modes: both (Tyler, 2026-09-27).** Internal decks are sometimes presented
  and sometimes sent to be read. The skill has no default mode: every brief declares
  one. If the user did not say, the skill asks exactly one question: "Will this be
  presented live, or sent to be read?" The CLI default stays `presented` (D-008).
- **Sources for D-015 and §8** (checked 2026-09-27):
  - pre-installed libraries and Python 3.11 in the code-execution container:
    https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool
  - claude.ai network access (package managers, including PyPI, npm and GitHub, are
    allowed by default):
    https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude
  - custom skills (ZIP holding one folder, 200-character description, Customize →
    Skills): https://support.claude.com/en/articles/12512198-how-to-create-custom-skills
  - SKILL.md format (name regex, 1024-character description, 500 lines):
    https://agentskills.io/specification
  - Claude Code skills (locations; for synced skills, substitution and shell injection
    are disabled): https://code.claude.com/docs/en/skills
- **D-019 · Canonical demo product: BonsaiHub (Tyler, 2026-09-27).** A fictional parody:
  a swipe-dating app and a "hub" photo feed, both for bonsai trees.
  - The auditor provides `examples/bonsaihub/product.toml`. It is read-only, like the
    golden decks.
  - Every deck built from it carries the disclosure line on its cover or its last
    slide.
  - It stays safe for work.
  - It never imitates a real brand's marks or interface (`[product.brand].must_not`).

## 1. Layout

The plan may refine this layout, with reasons.

```
src/keyline/
  roles.py                 # §2
  brief.py                 # §4: brief + evidence schema, validation, spine
  briefcheck.py            # §4: deck-vs-brief findings
  numbers.py               # §4.4: numeric tokens (pure function, shared)
  colorspace.py            # §3.3: sRGB → CIELAB / HSL (pure function)
  packs/__init__.py        # §5: load by name or directory, validate
  packs/swiss/             # pack.toml, README.md, templates, src/ (template builders)
  pen/                     # §6 (imports python-pptx; never imported by lint)
  fit/                     # §6.4: advance-width tables + estimator (no python-pptx)
  render.py                # §7: engines libreoffice | officecli
  doctor.py                # §7
  rules/                   # + the seven new rules of §3
skill/keyline/             # §8: SKILL.md, references/, scripts/kl.py
tools/build_skill.py       # §9
tools/gen_docs.py          # §8.3
examples/bonsaihub/        # §10
fixtures/briefs/  fixtures/pen/  fixtures/packs/   # new fixture families
```

`pyproject.toml`:
- Runtime deps stay `lxml` and `Pillow`.
- Add the extras `pen = ["python-pptx>=1.0.2"]` and `render = ["pypdfium2"]`.
  `pypdfium2` is imported only by `render.py`.
- Dev deps gain `pypdfium2` and `fontTools`. `fontTools` is used only by the
  generator of the fit tables (§6.4), never at runtime.
- CI adds `apt-get install fonts-liberation`. LibreOffice is not installed in CI, so
  render tests skip there.

## 2. Slide roles

- **Roles:** `cover`, `section`, `statement`, `evidence`, `quote`, `close`.
- **Parsing.** A slide's role comes from its layout name. The whole name must match
  `^keyline:(cover|section|statement|evidence|quote|close)(:[a-z0-9-]+)?$`. The
  optional third field names a variant (for example `keyline:evidence:two-col`). If
  the name does not match, the slide has no role.
- **Where roles change lint** (slides without a role keep M1 behavior, including
  "slide 1 is the cover"):

| Rule | With a role |
|---|---|
| `dead-band` | Runs only on `evidence` slides |
| `notes-missing` | Exempts `cover` and `section` |
| `title-too-long` (§3) | Exempts `quote` |

## 3. Lint 0.2 changes

### 3.1 Source and note lines

- **Definition.**
  - A *source paragraph* is an inked paragraph whose text, after NFC, a left strip and
    casefold, starts with a prefix from `source_prefixes`, followed by optional spaces
    and then `:` or `：`.
  - A *note paragraph* is the same with a prefix from `note_prefixes`.
  - Example: "Source code matters …" is neither, because no colon follows the prefix.
- **In `body-too-small`**, source and note paragraphs are not body. Instead, the rule
  fires if any inked run in one of them is smaller than `source_min_pt`, with the
  message "source line" or "note line".
- **Everywhere else**, both count as text as before (contrast, fonts, pack rules).
- Only source paragraphs satisfy `source-missing` (§4.5) and leave the numeric scan
  (§4.4). A note can make a claim, so its numbers are still checked.

### 3.2 New thresholds (`thresholds.toml`, `calibrated = false`)

| Key | presented | read |
|---|---|---|
| `title_words_max` | 10 | 15 |
| `source_min_pt` | 12 | 9 |
| `reads_max` (brief) | 3 | 5 |
| `bullets_max` (pen) | 4 | 6 |
| `numerals_max` (pen: `figure()` calls per slide) | 1 | 2 |

Common keys, with these initial values:

```toml
source_prefixes = ["source", "sources", "nguồn"]
note_prefixes = ["note", "notes", "ghi chú"]
neutral_chroma_max = 1.5          # CIELAB C*; pack paper must be at or below
cream_lightness_min = 88          # CIELAB L*
cream_chroma_max = 20             # cream: neutral_chroma_max < C* <= this
cream_hue_min = 60                # CIELAB h, degrees
cream_hue_max = 115
cream_slide_ratio = 0.5
terracotta_hue_min = 10           # HSL hue, degrees
terracotta_hue_max = 25
terracotta_sat_min = 0.35         # HSL saturation
terracotta_sat_max = 0.90
terracotta_light_min = 0.35       # HSL lightness
terracotta_light_max = 0.70
closing_cliches = ["thank you", "thanks", "thank you for listening", "questions",
  "any questions", "q&a", "key takeaways", "in conclusion", "the end",
  "cảm ơn", "xin cảm ơn", "cám ơn", "cảm ơn đã lắng nghe", "hỏi đáp"]
mood_words = ["clean", "modern", "elegant", "premium", "sleek", "minimal", "minimalist",
  "bold", "vibrant", "professional", "innovative", "dynamic", "cutting-edge",
  "seamless", "fresh", "stylish"]
statement_min_slides = 6          # brief-no-statement applies at or above this length
```

### 3.3 Color spaces (normative)

- **CIELAB.** sRGB (IEC 61966-2-1) → linear → XYZ (D65) → CIELAB, with reference white
  (0.95047, 1.0, 1.08883). C\* = √(a\*² + b\*²). h = atan2(b\*, a\*) in degrees,
  in [0, 360).
- **HSL.** CSS Color 4 definition; saturation and lightness in [0, 1].
- **Test anchors** (auditor's computation, 2026-09-27; assert within ±0.02):

| Color | L\* | C\* | h (Lab) | HSL h | Meaning |
|---|---|---|---|---|---|
| `F2F2F0` | 95.44 | 1.02 | 110.10 | 60.00 | keyline paper: neutral |
| `f4f3ee` | 95.79 | 2.58 | 102.06 | — | cream |
| `FAF9F5` | 97.90 | 2.06 | 100.17 | — | cream |
| `F5F5DC` | 95.95 | 12.76 | 109.19 | — | cream |
| `EFF1F5` | 95.10 | 2.16 | 271.43 | — | cool, not cream |
| `CC3322` | — | — | — | 6.00 | signal red, not terracotta |
| `c96442` | — | — | — | 15.11 | terracotta |
| `D20F39` | — | — | — | 347.08 | red, not terracotta |

  HSL saturation cannot tell near-whites apart: `F2F2F0` has S = 7.1 %. That is why
  paper uses C\* and accents use HSL hue. The draft guard in `docs/research.md` (§ on
  the Claude look: "HSL saturation ≤ 4%") would reject keyline's own paper. Record
  this as lesson L-011.

### 3.4 New rules

Every rule has `since = "0.2.0"`. The registry gains a field `requires`, with values
`none | pack | brief | officecli`. The M1 rules get `requires = "none"`.

| id | cat | severity | scope | basis | requires | fires when |
|---|---|---|---|---|---|---|
| `claude-look-palette` | slop | warning | deck | color | none | At least `cream_slide_ratio` of the slides have a cream resolved background (L\* ≥ `cream_lightness_min`, `neutral_chroma_max` < C\* ≤ `cream_chroma_max`, `cream_hue_min` ≤ h ≤ `cream_hue_max`), **and** some inked run color, visible solid fill or resolved slide background falls in the terracotta band (HSL hue, saturation and lightness within the `terracotta_*` bounds). If only the cream condition holds, the finding is `advisory` |
| `title-too-long` | quality | warning | slide | text | none | The title (A-1) has more than `title_words_max` words (A-7). Exempt: `quote` role |
| `closing-cliche` | slop | warning | slide | text | none | The last slide's title text is in `closing_cliches` after NFC, casefold, whitespace collapse and stripping of `.!?…:;-–—` and spaces at both ends |
| `off-palette-color` | quality | warning | slide | color | pack | An inked run color, the solid fill of a visible shape, or a solid resolved slide background is not in the pack palette (hex, case-insensitive). One finding per shape (its first offending value) and one per slide background |
| `off-scale-size` | quality | warning | slide | text | pack | An inked run's effective size (after autofit, A-14) is not in the pack's type scale for the mode. One finding per shape |
| `off-pack-font` | quality | warning | deck | text | pack | A resolved latin family (A-8 normalized) is not in the pack's fonts. One finding per offending family; the message lists up to 5 slide numbers |
| `accent-overuse` | slop | warning | slide | color | pack | The number of accent elements on a slide exceeds the pack's `accent_budget`. An accent element is a text-bearing shape with at least one inked run in a pack accent color (counted once per shape), or a visible shape whose solid fill is a pack accent color |

- Hidden shapes are excluded, as in A-12.
- Pack rules run only when a pack is given (§3.5).
- Chart and table internals remain outside the lint model (spec 001). The pen
  guarantees token use there (§6).
- **Table text** stays out of `Shape.paragraphs`. The adapter adds a separate
  `Shape.table_text` (plain cell text, row-major), read only by `numbers.py` (§4.4).
  If table text went into `paragraphs`, `font-count` and the pack rules would start
  seeing it and M1 results would change (the stress deck `d20_pgx_slop` has a table).
  The M1 advisory "table text is not read" stays.
- **Registry and rule signature.** Rules move to `check(deck, cfg, ctx)`, where `ctx`
  carries the resolved pack, the brief and the evidence (each may be None). M1 rules
  ignore `ctx`.
  - Every §4 id is a registry entry with the full field set: category, severity,
    scope, basis, `requires = "brief"`, `since = "0.2.0"`, summary and rationale.
  - §4.3 ids run in `keyline brief`. §4.5 ids run in `lint` and `check` with a brief.
- **Config.** `config.py` today rejects list values and unknown keys. Extend its
  schema to accept the §3.2 keys, including lists of strings.

### 3.5 CLI

- `keyline lint DECK [--mode M] [--pack NAME|DIR] [--brief FILE] [--json]`
- `keyline check DECK [--mode M] [--pack …] [--brief …] [-o DIR]
  [--engine auto|libreoffice|officecli] [--require-render] [--json]`
- `keyline render DECK -o DIR [--engine …]`
- `keyline brief FILE [--json]` (§4.3)
- `keyline doctor [--json]` (§7)
- `keyline packs [--json]`: lists the packs found (name, version, modes).

**Resolving mode and pack:**
- `--brief` supplies both.
- An explicit `--mode` or `--pack` that disagrees with the brief is an error: exit 1
  with a one-line reason, for example `mode conflict: --mode read, brief says
  presented`.
- With neither a flag nor a brief, the mode is `presented` (D-008) and no pack
  applies. The parser's default for `--mode` becomes None, so that an explicit flag
  can be told apart from the default.
- `--pack` takes a pack name (from the bundled packs) or a directory path.

**Output contract:** unchanged (spec 001 §3; A-16). `keyline rules --json` gains the
`requires` key.

## 4. Brief and evidence

### 4.1 Evidence file (`product.toml` or any name)

```toml
schema = 1
[product]                      # required table
name = "…"                     # required, non-empty
fictional = false              # optional, default false
disclosure = "…"               # required when fictional = true
[[evidence]]                   # zero or more
id = "…"                       # required, ^[a-z0-9_]+$, unique
label = "…"                    # required, 1 to caption_exempt_words words (A-7)
source = "…"                   # required, non-empty
value = "…"                    # exactly one of value | series
series = [["Apr", 410], …]     # [category string, number] pairs; numbers int or float
aliases = ["…"]                # optional: other accepted renderings of value
```

- **Unknown keys are ignored** at every level, including inside `[product]` and
  `[[evidence]]`. Examples: `one_liner`, `tone`, `[product.world]`, `[[feature]]`,
  `[[audience]]`, `[[profile]]`. They are material for the brief.
- **Several files.** A brief may name several evidence files (§4.2).
  - The first is the *primary* file, and only it needs `[product]`.
  - Later files hold `[[evidence]]` only. They are how an agent adds numbers when
    the primary file is read-only, as it is for the demo.
  - Evidence ids are unique across all the files.

### 4.2 Brief file (`<deck>.brief.toml`)

```toml
schema = 1
mode = "presented"              # required: presented | read
pack = "swiss"                  # required: pack name or directory
evidence = ["product.toml"]     # required: a path or a list of paths, relative to the brief file; the first is primary

[direction]                     # all required, non-empty
audience = "…"                  # who is in the room, or who reads it
decision = "…"                  # what they should decide or do afterwards
thesis = "…"                    # one sentence someone could disagree with
own_world = ["…", "…", "…"]     # 3 to 7 concrete nouns from the subject's own world
motif = "…"                     # one device that repeats and escalates; the close rhymes with the cover

[[slides]]                      # at least 1; the first has role "cover"; at most one cover
role = "evidence"               # §2 role
headline = "…"                  # required: for a quote slide, the quote itself
reads = ["…"]                   # 1+ items: what the audience must understand, in order
evidence = ["waitlist_trees"]   # optional: evidence ids shown on this slide
notes = "…"                     # optional here; see brief-notes
```

### 4.3 `keyline brief FILE`

- **Output.** Validates the brief and its evidence file, then prints the **spine** to
  stderr: one line per slide, `NN role  headline`. With `--json`, stdout carries
  `{"spine": [...], "findings": [...]}`, where findings use the spec 001 contract.
- **Exit 1** with a one-line reason on a schema error:
  - a missing or mistyped key;
  - an unknown role;
  - an unknown evidence id;
  - an evidence file that is missing or invalid;
  - a duplicate evidence id (across all files);
  - a first slide that is not `cover`, or more than one cover;
  - an `own_world` with fewer than 3 or more than 7 items;
  - `evidence` listed on a `section` or `quote` slide. Neither role has room for a
    source line (§5.2), so numbers there have no legal place;
  - an evidence label with more than `caption_exempt_words` words.
- **Exit 2** when there are findings at warning or error severity. **Exit 0**
  otherwise.

| id | severity | fires when |
|---|---|---|
| `brief-reads` | warning | a slide has more than `reads_max[mode]` reads |
| `brief-mood` | warning | an `own_world` item consists only of `mood_words`, after casefolding, splitting on whitespace and stripping `.,;:!?` from each token |
| `brief-notes` | warning | presented mode, and a `statement`, `evidence`, `quote` or `close` slide has empty `notes` |
| `brief-headline-long` | warning | a headline has more than `title_words_max[mode]` words, except on `quote` slides |
| `brief-no-statement` | advisory | presented mode, at least `statement_min_slides` slides, and no `statement` slide |

For these findings, `slide` is the 1-based brief slide index, or 0 for brief-level
findings, and `shape_id` and `shape_name` are null.

### 4.4 Numeric tokens (normative; `numbers.py`)

1. **Text in scope.** After NFC:
   - the inked text of each paragraph of each non-hidden shape;
   - the `Shape.table_text` of tables (§3.4).

   Excluded:
   - source paragraphs (§3.1);
   - placeholders of type `sldNum`, `dt` and `ftr`;
   - chart parts;
   - notes.
2. **Token.** Built in three steps; the token string has no spaces:
   1. **Core:** a maximal match of `\d+(?:[.,]\d+)*`.
   2. **Prefix** (immediately before the core): an optional currency symbol from
      `$€£¥₫`, optionally preceded by a sign (`-`, `−`, `+`). Or a sign alone. `−`
      is normalized to `-`. A sign counts only at the start of the text or after a
      character that is not a letter or digit. So in "10-20" and "Q3-2026" the
      hyphen is not a sign.
   3. **Suffix:**
      - `%` or `×` immediately after the core or after one space; or
      - one of `bn`, `k`, `K`, `M`, `B`, `x` immediately after the core, when the
        next character is not a letter.
3. **Significant token.** It has a prefix or a suffix, or its core has at least 2
   digits.
   - **Exception:** a bare 4-digit core from 1900 to 2099, with no prefix or suffix,
     is a year and is not significant.
   - Test anchors (auditor's reference implementation, 2026-09-27):

| Text | Tokens (significant marked *) |
|---|---|
| `12,400 trees are waiting` | `12,400`* |
| `$1.2M seed round` | `$1.2M`* |
| `$1.2B` · `$1.2 million` | `$1.2B`* · `$1.2`* |
| `3.2% of swipes` · `71 %` | `3.2%`* · `71%`* |
| `3x faster` · `3.2 x` | `3x`* · `3.2`* |
| `-71% churn` · `−0.4%` | `-71%`* · `-0.4%`* |
| `12.4k keepers` | `12.4k`* |
| `Q4 2026` · `Sep 2026` | `4`, `2026` · `2026` |
| `2 pilot cities` · `5kg` | `2` · `5` |
| `90-day keeper retention` · `212-year-old` | `90`* · `212`* |
| `10-20 trees` | `10`*, `20`* |
| `4.99 USD` · `$4.99` | `4.99`* · `$4.99`* |
4. **Tokens of an evidence entry:**
   - the tokens of `value`, of each alias and of `label`, built by the same
     procedure. So "$1.2M" stays "$1.2M", and a label such as "90-day keeper
     retention" is part of the evidence;
   - for `series`, each number formatted as Python `f"{n:,}"` (integers) or
     `f"{n:,.1f}"` (floats), plus the tokens of the category strings.
5. **Known limits:**
   - Units are not compared: "38 days" matches "38 years".
   - Spaces used as thousands separators ("12 400") are not supported; use
     `aliases`.
   - "24/7" yields a significant "24".

### 4.5 Deck-vs-brief findings (`check` or `lint` with `--brief`)

| id | severity | scope | fires when |
|---|---|---|---|
| `brief-slide-count` | error | deck | the deck's slide count ≠ the number of brief slides |
| `brief-role` | warning | slide | the slide's role (§2) ≠ the brief's role, or the slide has no role |
| `brief-headline` | warning | slide | the title (A-1) text ≠ the brief headline, compared after NFC and whitespace collapse (case-sensitive) |
| `unsourced-number` | warning | slide | a significant token on the slide is not among the tokens of that slide's brief `evidence` entries (string equality) |
| `source-missing` | warning | slide | the brief slide lists evidence, the slide has no source paragraph, and the slide either shows at least one significant token or contains a `graphicFrame:chart` or `graphicFrame:table` |
| `fiction-undisclosed` | warning | deck | the evidence file says `fictional = true`, and neither slide 1 nor the last slide contains the disclosure (NFC, whitespace-collapsed substring of the slide's inked text) |

- The slide-level brief findings pair slides by index. When the counts differ, they
  are computed for the common prefix only.
- `keyline brief` findings (§4.3) are not repeated by `check`. Run `keyline brief`
  before building.

## 5. Packs

### 5.1 Format

A pack is a directory with these files:

- **`pack.toml`** (schema below).
- **`README.md`**: the direction, and why. Examples are marked "one idea, not a
  template".
- **The templates**: one `.pptx` per mode. Each template's `txStyles` carry that
  mode's sizes, so a single shared template cannot work.
- **`src/`**: the scripts that build the templates (byte-stable output; §6.5).

`pack.toml` keys (the plan fixes the exact shape; every value is data):

- `schema`, `name`, `version`, `modes`, `templates`.
- `fonts`: list.
- `palette`: name → hex. Every text color, fill, line color and theme color the pack
  uses comes from it.
- `accents`: the palette names that count as accent.
- `accent_budget`: an integer.
- `containers`: `rules | boxes | none`.
- `alignment`: `left | center`.
- `accepted`: a list of `{ rule, reason }`. These are deliberately accepted defaults,
  which `lint` reports as `advisory`.
- `surfaces`: name → background, plus the allowed text colors.
- `styles.<mode>.<style>`: size_pt, weight, color, caps, tracking, line spacing.
- `roles.<role>`: surface, layout name(s), and the styles allowed on that role in each
  mode.
- `regions.<layout>`: named regions in grid units (§6.3).

### 5.2 Swiss pack v1 (`packs/swiss`)

**Direction** (for `README.md`): grid, flush-left, ragged-right. One sans family. Paper,
ink and one signal red. Hairlines, not boxes. Confident emptiness on statement slides.
Its one recurring device is *the keyline*: a single strong rule at a fixed height on
every `evidence` slide. The pack is a sibling of the editorial golden deck, and keeps
that deck's fixes (L-006).

**The keyline device** (so that lint sees it predictably):
- It is a filled rectangle in ink, spanning the full content width, at a fixed y.
- The pen draws it automatically on every `evidence` slide. The author does not call
  it, and there is no `keyline()` verb.
- Because it is at least 50 % of the content width, `title-underline` exempts it. It
  is ink, so it never counts toward `accent-overuse`.

**Palette** (contrast ratios computed by the auditor, WCAG 2.x):

| Name | Hex | Use | Contrast |
|---|---|---|---|
| paper | `F2F2F0` | default surface | C\* 1.02: neutral |
| ink | `111111` | text; section surface | 16.85 : 1 on paper |
| muted | `5C5C5A` | labels, source lines | 5.98 : 1 on paper |
| hairline | `B8B8B4` | light rules only, never text | 1.78 : 1 (decorative) |
| accent | `CC3322` | on paper, any size | 4.61 : 1 on paper; HSL hue 6.0 |
| accent_on_ink | `E8422E` | on ink, any size | 4.72 : 1 on ink |

`CC3322` on ink is only 3.65 : 1, which is why the ink surface has its own accent
value. Both reds count as accents; `accent_budget = 1`, `containers = "rules"`,
`alignment = "left"`, `accepted = []`.

**Type:** Arial (D-017), regular and bold. Initial scale, in pt:

| Style | presented | read | Weight / case | Color | Used on |
|---|---|---|---|---|---|
| `cover_title` | 66 | 40 | bold | ink | cover, close |
| `statement` | 60 | 36 | bold | ink | statement |
| `headline` | 48 | 28 | bold | ink (paper on ink) | evidence, section |
| `quote` | 44 | 24 | regular | ink | quote |
| `lede` | 28 | 16 | regular | ink | cover, close, statement; read mode also evidence |
| `body` | 24 | 13 | regular | ink | evidence, statement |
| `numeral` | 120 | 60 | bold | ink or accent | `figure()` |
| `label` | 14 | 10 | bold, caps, tracking +8 % | muted on paper; accent_on_ink on ink | table headers, figure labels, attributions: ≤ `caption_exempt_words` words (the pen enforces it) |
| `source` | 12 | 9 | regular | muted | source and note lines |

The plan may change sizes only if the invariants in §5.4 still hold. It records every
change with a reason.

**Components allowed per role** (the pen enforces this; `pack.toml` holds it as data):

| Role | Surface | Title style | Components |
|---|---|---|---|
| cover | paper | `cover_title` | `text` (lede), `source`, `note` (disclosure) |
| section | ink | `headline` (paper) | `text` (label, accent_on_ink). No source or note: muted on ink is 2.82 : 1 |
| statement | paper | `statement` | `text` (lede or body), `figure`, `source`, `note` |
| evidence | paper | `headline` | one of `text`/`bullets` (body; read mode also lede), `figure`, `table`, `chart_bar`, `image`; plus `source`, `note` |
| quote | paper | `quote` (the quote itself) | `attribution` (label) |
| close | paper | `cover_title` | `text` (lede), `figure`, `source`, `note` |

**Evidence layouts** offer a figure region at least 8 of 12 columns wide. "212 years"
at 120 pt bold measures about 19.3 cm, which is 7.4 columns (reviewer's measurement).

### 5.3 Template constraints

- 16:9, 12192000 × 6858000 EMU. No slides.
- The master has a solid `p:bg` in paper. The `section` layout has a solid `p:bg` in
  ink.
- **Layouts and the master contain placeholders only.** Decorative devices such as
  the keyline rule are drawn by the pen on the slide. Reason: spec 001 does not lint
  layout or master shapes (FP-2, backlog P1).
- **Section placeholders** carry paper as their text color (in `lstStyle`). Without
  it, text typed there by hand would inherit ink on the ink background.
- Every placeholder keeps at least `edge_margin_cm` from every edge.
- Theme fonts: major and minor are both Arial. All 12 theme colors are palette values
  (dk1 = ink, lt1 = paper, accent1 = accent; the plan maps the rest).
- `txStyles` and the placeholder `lstStyle`s carry the pack sizes for the template's
  mode. So text typed into a placeholder by hand in PowerPoint still lands on scale.
- Layout names follow §2. Every role exists in every mode. The read template offers
  at least one two-region `evidence` variant.

### 5.4 Invariants (tested; AC-9)

For each mode, a style **could be body** unless it is `label`, `numeral` or `source`.
Those three are safe only because the pen writes each as its own shape and caps its
words: labels at `caption_exempt_words`, numerals at `kpi_numeral_max_words`.
Source and note lines are exempt by §3.1.

1. **Hierarchy.** For every role, and every pair of (title style, text style) that the
   role allows, title size ≥ `title_ratio_min` × size of every style that could be
   body. The comparison is non-strict: the rule fires on `<`, so evidence in presented
   mode sits exactly at 48 / 24 = 2.00 and passes.
2. **Body floor.** Every style that could be body is ≥ `body_min_pt`.
3. **Source floor.** `source` ≥ `source_min_pt`.
4. **Contrast.** Every (text color, surface) pair a style allows reaches
   `contrast_normal` at every size (not only `contrast_large`).
5. **Neutral paper.** Paper C\* ≤ `neutral_chroma_max`. No palette color falls in the
   terracotta band.
6. **Fonts.** The number of families is ≤ `font_family_max`.
7. **KPI numerals.** Numeral size ≥ `kpi_numeral_min_pt`, so numerals are never
   title-like (spec 001).

## 6. Pen

### 6.1 Contract

Style lives in the engine, not in prose (`docs/research.md`, § on the Opus 5.5 trend,
riso-rooms). The pen is the only supported way for the skill to put content on a
slide.

- **Writer independence (D-015).**
  - The public pen API exposes no writer types: no python-pptx object goes in or comes
    out.
  - All python-pptx calls live in one writer module behind an internal interface, so
    a second writer (OfficeCLI) can be added later without changing any build script.
  - A test inspects the public signatures and the return types.
- **Import and entry points.** `from keyline.pen import Deck`.
  - `Deck.from_brief(path)` loads the mode, pack and evidence.
  - `Deck(pack=…, mode=…, evidence=None)` builds without a brief (the specimen, tests).
- **Slides.**
  - `deck.next()` returns a builder for the next brief slide, with its role, headline
    and notes already applied. It raises when the brief is exhausted.
  - `deck.add(role, headline, notes=None)` is the brief-less form.
- **Component verbs.** Each fills exactly one named region:
  - `text(content, style="body", region=…)`
  - `bullets(items, region=…)`: at most `bullets_max[mode]` items.
  - `figure(evidence_id, region=…, label=None, accent=False)`:
    - The numeral is the evidence `value`.
    - The label defaults to the evidence label.
    - The numeral and the label are **two separate shapes**, so that neither becomes
      body text.
    - A `series` entry raises `PenError`; use `chart_bar` for those.
    - At most `numerals_max[mode]` figures per slide.
  - `table(rows, header=True, region=…)`:
    - Rows are lists of strings.
    - Hairline rules, no fills.
    - The header uses the `label` style, and each header cell is capped at
      `caption_exempt_words` words.
  - `chart_bar(evidence_id, region=…, highlight=None)`: a bar chart from a `series`
    entry.
    - No legend, no gridlines except light horizontal rules, and direct data labels.
    - Bars are muted. At most one highlighted category is in accent.
    - Chart fonts and colors come from the pack.
  - `image(path, region=…, alt=…)`: fitted inside the region without cropping or
    distortion. `alt` is required and is written to `descr`.
  - `attribution(text)`: on `quote` slides, in the `label` style, in its own
    placeholder.
    - The quote itself is the brief headline. `next()` writes it into the title
      placeholder in the `quote` style, with no added quote marks, so `brief-headline`
      compares it exactly.
  - `source(text=None)`: the source line in the fixed bottom region.
    - With no text, it is built from the `source` of each of the brief slide's
      evidence entries, de-duplicated in first-seen order, joined with "; " and
      prefixed "Source: ".
    - Without a brief, it uses the evidence ids the slide's verbs used.
  - `note(text=None)`: a note line in the `source` style.
    - With no text on a `cover` or `close` slide, it writes the primary evidence
      file's `disclosure`.
    - A text without a note prefix gets "Note: " added.
    - The fixed bottom region holds up to two paragraphs: the source line first, then
      the note line. `source()` and `note()` may both be used on one slide.
  - `notes(text)`: speaker notes.
- **Automatic.** The keyline rule is drawn on every `evidence` slide (§5.2).
- **Accent budget.** The pen enforces `accent_budget` per slide. It counts
  `figure(accent=True)`, a chart highlight and any other accent use, and raises
  `PenError` over budget. The chart highlight is invisible to lint, so the pen is its
  only guard.
- **Save.** `deck.save(path, author="")`.

### 6.2 Token-only

- No public pen function or method accepts a color, a font name, a size, a length, a
  coordinate or an alignment. Parameters are style names, region names, evidence ids
  and content.
- A string that looks like a raw value where a token is expected, such as `#CC3322`,
  `24pt` or `2cm`, raises `PenError`.
- So does an unknown style, region or role, or a style the pack does not allow on the
  role in this mode (§5.1 `roles`).
- The pen never writes italic runs, never centers text, and never writes gradients,
  shadows, glow, rounded rectangles or icons.
- The pen never enables autofit. Its text bodies get `a:noAutofit` and
  `wrap="square"`, and its text boxes and placeholders get zero insets. python-pptx
  text boxes otherwise default to no wrapping.
- Label, attribution and header-cell text over `caption_exempt_words` words raises
  `PenError`. So does a numeral over `kpi_numeral_max_words` words.

### 6.3 Regions

- The pack defines named regions per layout on a grid: 12 columns and fixed outer
  margins, all inside `edge_margin_cm` + `edge_margin_tolerance_cm`.
- A region holds at most one component. A second component in an occupied region
  raises `PenError`.
- Regions within one layout do not overlap.
- The source/note region and the keyline rule have fixed positions.
- A pen shape's box is its full region box, not the height of its text. So
  `dead-band` measures the layout's composition, which the pack designs, rather than
  how full each region happens to be.

### 6.4 Fit: refuse, never shrink

- **Method.** Before writing, the pen estimates whether the text fits its region at
  its token size.
- **Width.**
  - Use per-glyph advance widths for each pack font weight, taken from a
    metric-compatible OFL font (Liberation Sans for Arial). Kerning is ignored.
  - Measure the string as rendered: upper-cased for caps styles, plus tracking × size
    per character.
  - Subtract the paragraph indent (`marL`) and, in tables, the cell margins from the
    available width.
  - Wrap greedily. A line fits when its width ≤ 0.99 × the available width.
    LibreOffice wrapped a bold 14 pt label to 2 lines at 1.000× and 1.002× its
    advance sum, but not at 1.005× (reviewer's measurement).
  - A single word wider than the region does not fit.
- **Height.**
  - Line pitch = size × `line_pitch_em` × the style's line spacing.
  - `line_pitch_em` = 1.2 for Liberation Sans. It is stored with the width table.
    LibreOffice 24.2 set text at a pitch of exactly 1.20 × size at 13, 24, 48 and
    60 pt (reviewer's measurement). PowerPoint is reported to use 1.2 as well; that
    is unverified. The font's hhea factor, 1.15, underestimates it.
  - Paragraph `spcBef` and `spcAft` are added.
  - A region holds n lines when n × pitch plus the paragraph spacing is ≤ its height.
  - Swiss v1 styles use line spacing ≥ 1.0. Below 1.0, LibreOffice also shrinks the
    first line, and stacked Vietnamese capitals rise above the box.
- **Tables.** The same width and height rules apply per cell, with each column's width
  from its widest cell. Rows grow to their tallest cell, and the table must fit the
  region.
- **Bullets.** The bullet indent, marker and paragraph spacing are pack style data,
  and the estimate uses them.
- **Data.** The width tables are committed as data under `src/keyline/fit/`, with the
  OFL notice in `NOTICE`. A generator script (fontTools, dev only) rebuilds them from
  the TTFs. A character missing from the table uses the table's maximum advance.
- **On failure** the pen raises `DoesNotFit`, and the message says what does not fit.
  Example: "headline needs 3 lines, region holds 2: shorten it or split the slide".

### 6.5 Determinism

The same script and inputs produce byte-identical `.pptx`. The pen normalizes the zip
on save:

- entries are sorted, with `[Content_Types].xml` first;
- every entry carries the fixed timestamp 1980-01-01 00:00:00;
- compression is the same for every entry.

Core properties are also fixed: `created` and `modified` come from the template, and
`author` and `lastModifiedBy` from the argument.

**Embedded chart workbooks** get the same treatment. python-pptx embeds an XlsxWriter
workbook in every chart, and its `docProps/core.xml` holds the build time. So set the
workbook's `created` and `modified` to the template's `created`, and rewrite its inner
zip under the same rules.

Two checks back this:
- The auditor confirmed that, for a deck without charts, python-pptx 1.0.2 saves differ
  only in zip timestamps.
- The reviewer confirmed that with a chart, the embedded `.xlsx` also differs.

### 6.6 Schema validity

- Pen output passes `officecli validate` with 0 errors. The test skips when OfficeCLI
  is absent.
- **Chart axis ids.** python-pptx 1.0.2 writes chart axis ids as negative integers
  (`c:axId`/`c:crossAx val="-2068027336"`). `officecli validate` reports each one as a
  schema error: "not a valid 'UInt32' value". That gave 6 errors on a one-chart deck
  (auditor's test, 2026-09-27).
- The pen therefore rewrites every axis id in a chart to a positive, deterministic
  UInt32. It keeps each `c:axId` and its matching `c:crossAx` pointing at each other.
  The auditor checked that remapping the ids this way makes the same deck pass (0
  errors).

## 7. Render engines and doctor

**`libreoffice` engine.** Converts the deck to PDF, then rasterizes the PDF:

- The conversion command is `soffice --headless --norestore
  -env:UserInstallation=file://<private temp profile> --convert-to pdf --outdir <tmp>
  DECK`. Keep both the private profile and `--outdir`. In the auditor's sandbox, a
  first attempt without either wrote no PDF and printed nothing; with both, it
  worked. Which flag mattered was not isolated.
- Rasterizing uses `pypdfium2` if it can be imported, else `pdftoppm -png`. Output is
  1280 px wide.
- The timeout is 120 s.
- `soffice` is looked for on PATH, then in the standard install paths:
  `/Applications/LibreOffice.app/Contents/MacOS/soffice` and
  `C:\Program Files\LibreOffice\program\soffice.exe`.

**`officecli` engine.** As in spec 001.

**`auto`.** Uses `libreoffice` when both `soffice` and a rasterizer are found, else
`officecli`, else no engine is available:

- `render` then exits 1 and prints the install hints.
- `check` then prints `render: skipped (…)` and keeps lint's exit code (A-10).

**Validate step in `check`** (D-015):
- **When it runs.** After lint and before render, `check` runs
  `officecli validate DECK --json` when OfficeCLI is installed. The auditor timed it
  at about 2.2 s.
- **Findings.** Each schema error becomes one finding `ooxml-invalid` (quality,
  warning, basis structure, `requires = "officecli"`).
  - `slide` is N when the error's part is `/ppt/slides/slideN.xml`, and 0 otherwise.
  - `message` carries the part, the path and OfficeCLI's text.
- **Unreadable output.** If the output cannot be parsed, `check` emits one
  `ooxml-invalid` finding that carries its first line.
- **Without OfficeCLI**, `check` prints `validate: skipped (officecli is not
  installed)` and the exit code does not change.
- **`--no-validate`** turns the step off.
- **The check differs between machines.** `check` is stricter on a machine with
  OfficeCLI. The skill's final report must say whether validation ran.
- **Output shape.** The auditor observed this shape (OfficeCLI 1.0.152):
  - exit 0 with "Validation passed" when the deck is valid;
  - exit 1 with errors otherwise;
  - `--json` gives `{"success": false, "warnings": [...]}`, where each error spans
    three consecutive entries: the message, then `Path: …`, then `Part: …`.

**Known limits.** `render` always prints the known limits of the engine it used:

- LibreOffice re-fits stored autofit (L-010) and substitutes fonts through fontconfig.
- OfficeCLI falls back to sans-serif (L-002).

The contact sheet is unchanged.

**`keyline doctor`.** Prints one line per check and a directive token that the skill
reacts to:

| Check | Tokens |
|---|---|
| Python version | `PYTHON_OK` / `PYTHON_OLD` |
| lxml | `LXML_OK` / `NO_LXML` |
| Pillow | `PILLOW_OK` / `NO_PILLOW` |
| python-pptx (the pen cannot build without it) | `PPTX_OK` / `NO_PPTX` |
| Render engine | `RENDER_LIBREOFFICE` / `RENDER_OFFICECLI` / `NO_RENDERER` |
| Rasterizer (for LibreOffice) | `RASTER_PDFIUM` / `RASTER_PDFTOPPM` / `NO_RASTER` |
| Render font (`fc-match Arial`: Arial or Liberation Sans) | `FONT_OK` / `FONT_SUBSTITUTED` (renders may show false overflow) |
| Validator | `VALIDATE_OFFICECLI` / `NO_VALIDATOR` |
| Packs found | `PACKS: swiss` |

- For every missing piece, `doctor` prints the exact install command.
- Exit 0 when lint can run (Python ≥ 3.11 with lxml and Pillow). Exit 1 otherwise.
- `--json` gives the same content as an object.

## 8. Skill

### 8.1 Folder (`skill/keyline/`, the source of truth)

```
SKILL.md
references/brief.md  craft-floor.md  anti-tells.md  pen.md  check.md
scripts/kl.py
```

`kl.py` finds its own directory through `__file__`:

- It prepends `<skill>/lib` to `sys.path` when that folder exists (the packaged skill).
  Otherwise it uses the installed `keyline` package (development mode).
- `kl.py <keyline args>` dispatches to the CLI.
- `kl.py run SCRIPT.py` runs a build script with the same path set up (`runpy`).

### 8.2 `SKILL.md` contract

**Frontmatter** (the agentskills.io specification, plus claude.ai's stricter limit):

- `name: keyline`, matching the folder, per the spec's name regex.
- `description`: at most 200 characters, the limit on claude.ai. It says what the
  skill does and when to use it.
- `license: Apache-2.0`.
- `compatibility` (at most 500 characters) names Python 3.11+, lxml, Pillow and
  python-pptx, and says that LibreOffice or OfficeCLI are optional, for previews.

**Body** (at most 200 lines):

- No `${…}` substitutions, no `` !`…` `` shell injection and no absolute paths.
  Skills synced from claude.ai into Claude Code run with substitution and injection
  disabled (Claude Code docs, "Skills synced from claude.ai").
- **Stance:** at most 5 lines.
- **Setup:** run `kl.py doctor` and react to its tokens.
- **Routes:**
  1. *New deck:* the full loop.
  2. *Check a deck:* `check` on any `.pptx`, explain the findings, propose fixes.
  3. *Revise:* edit the build script, rebuild, check.
- **The loop:**
  1. Settle the mode (D-018: one question if unknown).
  2. Write the evidence file. When the primary file is read-only or belongs to the
     user, add a second one instead (§4.1). Numbers the user gave are recorded with
     their source as "user, <date>".
  3. Write the brief.
  4. Run `kl.py brief` and show the spine.
  5. If the user is present, wait for them to approve the spine. If not, proceed and
     say so.
  6. Read `craft-floor.md`, then write the build script with the pen and run it.
  7. Run `kl.py check DECK --brief BRIEF`.
  8. Look at the contact sheet if a render exists and the agent can view images.
  9. Apply one batch of fixes, then run one re-check (constitution IX).
  10. Report.
- **Priority:**
  - The user decides the content and the skill decides the method.
  - If the user asks for something the method forbids, do it, and say which rule it
    breaks: the check will flag it.
  - When the pen refuses, change the content (shorten or split). Never change the
    tokens.
  - Never write deck content with raw python-pptx or OfficeCLI.
- **Report:**
  - the file;
  - the mode and pack;
  - the check exit code;
  - each remaining finding, with the reason it stays;
  - the render status, and whether `officecli validate` ran;
  - the known limits: fonts are not embedded, and Arial must be present.

### 8.3 References

- **`craft-floor.md`:** read right before every build. It contains only items backed
  by a rule, the pen or the brief.
  - Every rule-backed sentence carries `<!-- rule:ID -->`, with a registry id or a
    §4.3 / §4.5 id.
  - Numeric tables (the type scale per mode, the budgets) are generated from
    `thresholds.toml` and `pack.toml` between `<!-- gen:begin NAME -->` and
    `<!-- gen:end -->`. `tools/gen_docs.py --check` fails when a table is stale.
- **`anti-tells.md` (v1):**
  - one row per tell: `id | tell | enforcement | Swiss policy`;
  - the enforcement is one of `rule:<id>`, `pen`, `brief:<id>` or `backlog:<id>`;
  - it starts from the seed in Appendix A;
  - rows may be added, never dropped;
  - it cites `docs/research.md` sections and never copies text from other skills.
- **`brief.md`:** what each brief field means, the test for each field, the headline
  test (read only the spine: it has to tell the story), and what "reads" are.
  - Thesis test: "If it reads like a mood or a topic, it is not a thesis yet."
  - `own_world`: nouns from the subject, not adjectives about the deck.
  - Examples are keyline's own. None is lifted from another skill.
- **`pen.md`:** every public pen verb, its parameters and its refusals. A test checks
  that every public verb is documented.
- **`check.md`:** how to read findings. It has one fix recipe per rule id at warning or
  error severity (including §4 ids). A test checks coverage.

## 9. Packaging

`python tools/build_skill.py` writes `dist/keyline.zip`. `dist/` is gitignored.

- **Structure.** The zip root holds exactly one folder, `keyline/`, containing:
  - `SKILL.md`, `references/` and `scripts/`;
  - `lib/keyline/`: the package from `src/keyline`, with packs and fit tables, but
    without `__pycache__` or tests;
  - `LICENSE` and `NOTICE`.
- **Determinism.** Built as in §6.5, so two builds are byte-identical.
- **Size.** Under 3 MB.
- **Install notes** (README):
  - claude.ai and Claude desktop: Customize → Skills → upload the ZIP. Code
    execution must be on.
  - Claude Code: unzip into `~/.claude/skills/`, or rely on claude.ai sync. For
    development, symlink `skill/keyline`; `kl.py` then uses the installed package.

## 10. BonsaiHub demo

- **`examples/bonsaihub/product.toml`** is provided by the auditor.
  - SHA-256 `9b0fea6ee7eac65dbb380b6d91128406772abed2caa5f23bdcf379eae1586f8b`.
  - Never edit it. A test asserts the hash.
- **Two decks.** Each is produced by running the skill as a user would, in a **fresh
  Claude Code session** that has not seen the implementation, with the skill
  installed from `dist/keyline.zip`. Use the prompts below:
  - **`pitch`**: presented, 8 to 12 slides, audience `demo-day`.
    - Prompt P-1: "Use the keyline skill. Make the demo-day pitch deck for BonsaiHub
      from examples/bonsaihub/product.toml (audience `demo-day`). It will be presented
      live. Work in examples/bonsaihub/ and name the files pitch.brief.toml,
      build_pitch.py and pitch.pptx. Put the render in render/pitch/. Pass
      author="Tyler" when saving. If you need numbers that product.toml lacks, put
      them in pitch.evidence.toml with a source. Never edit product.toml."
  - **`preread`**: read, 4 to 8 slides, audience `team-preread`.
    - Prompt P-2: the same as P-1, with "the Q4 pre-read for the BonsaiHub team
      (audience `team-preread`). They will read it on their own." and the names
      preread.brief.toml, build_preread.py, preread.pptx, render/preread/ and
      preread.evidence.toml.
- **Committed files per deck:** `<deck>.brief.toml`, `build_<deck>.py`,
  `<deck>.pptx`, and `render/<deck>/` (LibreOffice PNGs and the contact sheet).
  Build scripts pass `author="Tyler"`.
- **Spine gate.** Tyler approves each spine (`kl.py brief` output) before the build
  (gate G-2a, recorded in the report). This is the loop's own approval step, not an
  extra one.
- **The briefs must show the direction:**
  - a thesis;
  - an `own_world` drawn from `[product.world]`;
  - a motif that the close answers.
  - No mood words.

## 11. Phases and gates

- **Phase A1: lint and data.**
  - Covers §2 roles, §3 lint 0.2, §4 brief and evidence, §5 pack format and
    templates, and §7 render and doctor.
  - Report A1 goes in `report.md`, then the external audit A1.
  - No pen yet. AC-5 and the rule fixtures are built by scripts, as in spec 001.
- **Phase A2: pen.**
  - Covers §6 pen, fit and determinism.
  - It also builds the **pack specimens**:
    - `fixtures/packs/swiss-specimen-presented.pptx` and `-read.pptx`;
    - built with `Deck.from_brief` from the committed
      `fixtures/packs/swiss-specimen-{presented,read}.brief.toml`;
    - evidence from `fixtures/packs/swiss-specimen.evidence.toml`, which holds the
      series for `chart_bar` and every number the specimen text uses.
  - Each specimen has one slide per role, uses every verb at least once, and carries
    real sentences about the pack itself (no lorem ipsum).
  - Report A2 follows.
- **G-1 (Tyler): taste gate.** Tyler reviews the specimen contact sheets (LibreOffice
  renders) and records ship or fix, with at most 8 items. The external audit of
  A2 runs in parallel. Its fix items land as amendments before Phase B ends.
- **Phase B: skill.** §8 skill, §9 packaging, §10 demo (with gate G-2a), and the
  surface runs (AC-22). Report B follows.
- **G-2 (Tyler): soul gate.** Tyler reviews both BonsaiHub contact sheets and
  records ship or fix, with at most 8 items. Constitution VIII: no rule can pass
  this gate for him.
- Then the external audit of Phase B, and the PR.

## 12. Acceptance criteria

Each criterion needs evidence in `report.md`: the command, an output excerpt, and PASS
or FAIL. Criteria marked (manual) are recorded by Tyler.

### Phase A1 (AC-1 to AC-9, AC-14, AC-14b, AC-16) and A2 (AC-10 to AC-13, AC-15)

**AC-1 · Registry.**
- `keyline rules --json` lists 32 entries:
  - the 13 from M1 (11 rules and the 2 adapter ids);
  - `ooxml-invalid` (§7), with `requires = "officecli"`;
  - the 7 rules from §3.4;
  - the 11 ids from §4.3 and §4.5, with `requires = "brief"`.
- Every entry has a `requires` field.
- The M1 entries' ids, severities, categories and bases are unchanged.

**AC-2 · No regression.**
- Every spec 001 test passes, changed **only** in these ways, each listed in the
  report:
  - `test_rules_listing` accepts the 31 ids, and `since` in {"0.1.0", "0.2.0"}.
  - `expect.toml` cases gain optional `pack` and `brief` keys, and the fixture
    harness passes them to lint.
  - The tests marked `officecli` pass `--engine officecli`.
  - The no-engine messages still contain the npm hint and L-002, and gain the
    LibreOffice hint.
- The M1 golden and rule-fixture snapshots are byte-identical.
- The report re-lints the 13 stress fixtures and lists every changed finding with its
  cause. The auditor predicts none, and the reviewer confirmed it on the golden, rule,
  foreign and parsable stress decks.

**AC-3 · Rule fixtures.** Each new §3.4 rule has a `--pos` and a `--neg` deck in
`fixtures/rules/`, built by committed scripts, with `expect.toml` entries. Pack rules
set `pack = "swiss"` in their cases.

**AC-4 · Claude-look anchors.** Four decks:

| Background | Accent | Expected |
|---|---|---|
| `f4f3ee` | text in `c96442` | `claude-look-palette` warning |
| `F2F2F0` | `CC3322` | nothing |
| `FAF9F5` | none | advisory only |
| `EFF1F5` | `D20F39` | nothing |

**AC-5 · Roles.** A fixture script (not the pen) builds one slide three times with the
same shapes: a headline and a numeral that leave a band of about 60 % empty. It varies
only the layout name:
- on layout `keyline:statement`: no `dead-band`;
- on `keyline:evidence`: `dead-band`;
- on an untagged layout at index 2: `dead-band` (the M1 behavior).

A `keyline:section` slide without notes gets no `notes-missing`.

**AC-6 · Source lines.** In presented mode:
- "Source: BonsaiHub waitlist, September 2026 (fictional)" at 12 pt: no
  `body-too-small`.
- The same line at 10 pt: `body-too-small`, with "source line" in the message.
- A 10-word paragraph starting "Source code …" at 12 pt: `body-too-small` as body. It
  is not a source line, because no colon follows the prefix.
- "Note: BonsaiHub is a parody. Its trees and every number in this deck are
  fictional." at 12 pt: no `body-too-small`.

**AC-7 · Brief validation.**
- `fixtures/briefs/valid.brief.toml`: exit 0, and the spine is printed.
- Each schema error in §4.3 has one fixture: exit 1, one line, no traceback.
- Each §4.3 finding has a positive and a negative fixture.

**AC-8 · Deck vs brief.**
- A pen-built deck and its brief: `check --brief` exits 0.
- Six drifted copies each produce exactly their one expected finding. The drifts are
  pinned, so that no other rule moves:

| Drift | Expected finding |
|---|---|
| A headline edited, kept within `title_words_max` | `brief-headline` |
| A copy of the **close** slide appended (so the disclosure stays on the last slide) | `brief-slide-count` |
| "12.4k" instead of "12,400", in body text, not the headline | `unsourced-number` |
| On an evidence slide, the source line replaced by "Note: figures are illustrative", so the region stays occupied | `source-missing` |
| The disclosure note removed | `fiction-undisclosed` |
| A `statement` slide's layout swapped to `keyline:quote` | `brief-role` |

**AC-9 · Pack invariants.**
- `packs/swiss/pack.toml` validates.
- A test checks every §5.4 invariant for both modes.
- A test checks the §5.3 template constraints: size, no slides, `p:bg`, only
  placeholders in layouts, theme fonts and theme colors, placeholder margins, layout
  names, and every role in every mode.

**AC-10 · Token-only pen.**
- A test inspects every public pen signature and fails on a parameter that accepts a
  color, font, size, length, coordinate or alignment.
- Each of these raises the named error:
  - `PenError`:
    - a hex string, `24pt` or `2cm`;
    - an unknown style or region;
    - a style or component the role does not allow;
    - a second component in an occupied region;
    - a 6-word label;
    - `figure()` on a series entry;
    - a second accent over `accent_budget`;
    - a `numerals_max + 1`-th figure;
  - an unknown evidence id: `EvidenceError`;
  - an over-long headline: `DoesNotFit`, with the message naming lines needed against
    lines available.

**AC-11 · Pen determinism.** Building each specimen twice gives byte-identical files.

**AC-12 · Specimens pass.**
- `keyline brief` passes with exit 0 on both specimen briefs.
- `keyline check swiss-specimen-presented.pptx --brief
  fixtures/packs/swiss-specimen-presented.brief.toml` exits 0.
- The `read` specimen does the same with its brief.
- There are no `adapter-unresolved` advisories.
- With OfficeCLI present, `check` reports no `ooxml-invalid`, so the chart axis ids
  are fixed (§6.6).

**AC-13 · Fit is conservative.** Two parts:
- **(a)** For a committed set of test strings (Latin, Vietnamese with diacritics,
  digits, and caps with tracking), compare the estimator's width against Pillow's.
  - Pillow measures with Liberation Sans at 1000 px, using `layout_engine =
    ImageFont.Layout.BASIC` so the result doesn't depend on whether the wheel has
    raqm. The result is scaled by size / 1000.
  - The estimate must be ≥ 0.995 × and ≤ 1.25 × Pillow's width.
  - This part skips when the fonts are absent.
  - The reviewer measured a ratio of 0.999 with raqm at small pixel sizes, so a strict
    ≥ 1.0 would fail on rounding alone.
- **(b)** In a "fit stress" deck, every text sits at the longest length the estimator
  accepts for its region. Rendered with LibreOffice, no text ink falls outside its
  region's box by more than 2 px at 1280 px width. This part skips without
  LibreOffice.

**AC-14b · Validate step** (skipped without OfficeCLI).
- `check` on `editorial.pptx`: no `ooxml-invalid`, and the exit code equals lint's.
- A committed copy with an injected `<p:bogus/>` inside `p:cSld` of slide 1 gives
  exactly one `ooxml-invalid` on slide 1 naming `/ppt/slides/slide1.xml`, and exit 2.
- With OfficeCLI hidden from PATH, `check` prints `validate: skipped` and the exit
  code equals lint's.
- `--no-validate` skips the step.

**AC-14 · Render engines.**
- With LibreOffice present, `render --engine libreoffice` produces one PNG per slide
  and `contact.png`.
- `auto` picks LibreOffice when it is present.
- Forcing an absent engine exits 1 with the install hint.
- `check` without any engine prints `render: skipped` and keeps lint's exit code.

**AC-15 · Core purity.** A subprocess test runs `keyline lint --brief
fixtures/packs/swiss-specimen-presented.brief.toml` on the presented specimen, then
asserts that `pptx` and `pypdfium2` are not in `sys.modules`.

**AC-16 · Doctor.**
- `keyline doctor --json` reports every §7 check.
- With python-pptx hidden (for example, a venv without it), it reports `NO_PPTX` with
  `pip install python-pptx` and still exits 0.

**G-1** (manual): Tyler's verdict on the specimen contact sheets, with its date.

### Phase B

**AC-17 · SKILL.md.**
- A test validates the frontmatter against §8.2: the name regex and folder match,
  description ≤ 200 characters, compatibility ≤ 500 characters.
- The body is ≤ 200 lines, with no `${`, no `` !` ``, and no absolute path.

**AC-18 · Docs integrity.**
- Every `<!-- rule:ID -->` anchor resolves to a registry or §4 id.
- Every Appendix A seed id is present in `anti-tells.md`, with a valid enforcement:
  - `rule:<id>` and `brief:<id>` name registry ids;
  - `backlog:<id>` names an id listed in §13;
  - `pen` needs no id.
- `tools/gen_docs.py --check` passes.
- `pen.md` documents every public verb.
- `check.md` has a recipe for every warning- and error-level id.

**AC-19 · Package.**
- Two runs of `tools/build_skill.py` produce byte-identical `dist/keyline.zip`.
- The zip has the §9 structure and is under 3 MB.

**AC-20 · Sandbox smoke.** In a fresh venv with only `lxml`, `Pillow` and `python-pptx`
installed (keyline itself not installed), with the zip unpacked to a temp dir:
- `python keyline/scripts/kl.py doctor` exits 0;
- `kl.py run` of the specimen build script works, with the specimen briefs and
  evidence copied next to it;
- `kl.py check` on the result with its specimen brief exits 0.

This stands in for the claude.ai sandbox.

**AC-21 · BonsaiHub.**
- `product.toml` matches its hash.
- Both briefs pass `kl.py brief` with exit 0.
- Both decks pass `kl.py check <deck> --brief <brief>` with exit 0.
- Two builds of each deck are byte-identical.
- The disclosure is present.
- The slide counts are within §10.
- On a machine with OfficeCLI (Tyler's or the auditor's), both decks give no
  `ooxml-invalid`.
- G-2a is recorded.

**AC-22 · Surfaces** (manual).
- **(a) claude.ai web.**
  1. Upload `dist/keyline.zip`.
  2. Attach `product.toml`.
  3. Send prompt P-3: "Use the keyline skill to make a 6-slide deck for BonsaiHub's
     demo day from this file. It will be presented live."
  4. Record the `doctor` output, whether a render happened, the final `check` exit
     code, and the downloaded deck. Commit the deck under
     `examples/bonsaihub/surfaces/`.
- **(b) Claude Code.** Install the skill into `~/.claude/skills/`, then do the same
  with P-3.
- **(c) Claude desktop.** Optional.

**AC-23 · Hygiene and CI.**
- The identity checks follow D-014.
- `NOTICE` carries the Liberation Sans (OFL) attribution for the fit tables.
- No text is copied from `anthropics/skills`.
- CI is green on 3.11 and 3.13, with `fonts-liberation` installed. `ruff` is clean.

**G-2** (manual): Tyler's soul verdict on both BonsaiHub decks, with its date.

## 13. Backlog created by this spec

- Generic rules:
  - `eyebrow-caps`, `title-italic-insert`, `centered-body` (the pen prevents these
    today);
  - `language-tells`: hype words, "not X but Y", decorative em-dashes, emoji or
    checkmark bullets;
  - `number-without-source` (for decks without a brief);
  - `layout-twinning`;
  - `text-overflow` (using §6.4's tables, for any deck).
- Line colors in `off-palette-color`.
- Locale-aware numbers (`12.400` in Vietnamese). Aliases cover this until then.
- A second pack (Catppuccin Latte/Mocha as a tokens-only pack; Enhalation after a
  fidelity test).
- A control deck: the same `product.toml` built without keyline, linted as evidence
  (a README story, and later M6 data).
- A finish-reviewer subagent, and the commands polish, bolder, quieter and distill.
- OfficeCLI as a second pen writer, behind the same API, when a feature needs it
  (first candidate: morph transitions for presented decks). It must first solve
  OfficeCLI's random relationship ids for byte-stable output.
- The route "check a deck → fix" for decks the pen did not build, using OfficeCLI
  `get`/`set` in Claude Code and python-pptx elsewhere (M3).
- A CI job with OfficeCLI installed, so that the `officecli` tests run there, not only
  on Tyler's and the auditor's machines.

## Appendix A · ANTI-TELLS v1 seed

Sources are the sections of `docs/research.md` on the canon and on tells. `anti-tells.md`
must contain at least these rows.

| id | tell | enforcement |
|---|---|---|
| equal-cards | three or more equal cards whatever the item count | `rule:equal-card-row`; pen has no card verb |
| cards-everywhere | text inside filled boxes, nested boxes | pen (Swiss `containers = "rules"`) |
| stat-tile-row | a row of big numbers with small labels | pen (`numerals_max`) |
| everything-centered | centered body text | pen; `backlog:centered-body` |
| flat-hierarchy | title barely larger than body | `rule:title-not-dominant`; pack invariant 1 |
| position-drift | titles jump between slides | pen (layouts fix positions) |
| no-confident-emptiness | no slide is allowed to breathe | `brief:brief-no-statement` |
| dead-band | a large empty horizontal band on a content slide | `rule:dead-band` |
| title-underline | a short accent bar under the title | `rule:title-underline`; pen has no bar verb |
| icon-in-circle | small icons in colored circles, repeated | pen has no icon verb |
| eyebrow-caps | tracked caps above every heading | pen (caps only in `label`); `backlog:eyebrow-caps` |
| claude-look | cream paper plus terracotta accent | `rule:claude-look-palette`; pack invariant 5 |
| italic-insert | an italic phrase in another family inside a sans title | pen (no italic); `backlog:title-italic-insert` |
| effects | purple-blue gradients, identical shadows, glow | pen (none of these) |
| unsourced-numbers | numbers with no source | `brief:unsourced-number`, `brief:source-missing` |
| hype-language | hype words, "not X but Y", decorative em-dashes, emoji or checkmark bullets | `backlog:language-tells` |
| thank-you-closer | a "Thank you" or "Questions?" last slide | `rule:closing-cliche` |
| ticker-bar | a thin full-width band of caps items | pen has no such verb |
| topic-titles | long descriptive titles that claim nothing | `rule:title-too-long`; `brief:brief-headline-long` |
| cramming | text shrunk to fit | pen (`DoesNotFit`); `rule:off-scale-size` |
| font-soup | more than two families | `rule:font-count`, `rule:off-pack-font` |
| accent-everywhere | the accent on many elements per slide | `rule:accent-overuse` |
| tiny-body | body text below the mode's floor | `rule:body-too-small` |
| low-contrast | text below WCAG contrast | `rule:text-contrast` |
| no-notes | presented slides without speaker notes | `rule:notes-missing`; `brief:brief-notes` |
| visual-on-every-slide | a picture forced onto every slide | brief (statement slides are text-only by design) |
| mood-direction | a direction made of adjectives | `brief:brief-mood` |

## Lessons to append (first task)

- **L-011 · HSL saturation cannot judge near-white paper.** `F2F2F0` has HSL S = 7.1 %
  while its CIELAB C\* is 1.02. Use C\* for paper and HSL hue for saturated accents
  (§3.3).
- **L-012 · Line pitch is 1.2 em, not the font's hhea factor.** LibreOffice 24.2 sets
  Arial/Liberation text at 1.20 × size. The hhea factor (1.15) underestimates height
  and makes text overflow (§6.4).
- **L-013 · A python-pptx chart carries its build time.** The embedded XlsxWriter
  workbook's `core.xml` records `created`/`modified`, so a chart deck is not
  byte-stable until the workbook is normalized too (§6.5).
- **L-014 · python-pptx chart axis ids are not schema-valid.** They are negative
  integers, and `officecli validate` rejects them as UInt32. PowerPoint is widely
  reported to open such files anyway (unverified), but a validator will not.
  Normalize the ids (§6.6).
- **L-015 · OfficeCLI output is not byte-stable.** Relationship ids are random, and
  `docProps/custom.xml` records the build time. An OfficeCLI writer would need an
  id-renumbering pass before it could promise reproducible builds.

## Amendment log

- 2026-09-27: created. Before handoff, the auditor revised it after an independent
  review session that had not seen the drafting. That review raised 20 findings
  (4 blockers), and all of them are folded in: fit line pitch, chart determinism, the
  test changes AC-2 allows, the specimen briefs, the source/note region, `figure()`
  shapes, the quote headline, the tokenizer, the drift pins, doctor tokens, templates
  per mode, registry context, and the A1/A2 split.
- 2026-09-27, still before handoff: Tyler chose option A for D-015. The pen API is
  writer-independent and python-pptx is the writer on every surface. OfficeCLI renders
  and runs `officecli validate` in `check` (§7, AC-14b), and is kept for a later second
  writer and for the M3 editing route. The auditor's test found invalid chart axis ids
  in python-pptx output, which led to §6.6 and L-014, and non-deterministic OfficeCLI
  output, which led to L-015.
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
- **B-8 (2026-09-29, Tyler: output diversity).** A pack is one **system** plus one or
  more **voices**. A deck's voice comes from its brief, and ideally from its
  `own_world`.

  1. **System.** The system is `pack.toml` without `[palette]` and `fonts`.
     - It declares `palette_roles`: for Swiss, `paper`, `ink`, `muted`, `hairline`,
       `accent`, `accent_on_ink`.
     - Every style gains `font = "display" | "text"`.
     - Everything else stays in the system: grid, surfaces as role names, styles,
       roles, regions, `accent_budget`, `containers`, `alignment` and the keyline
       device.

  2. **Voice.** A voice lives in `packs/<pack>/voices/<name>.toml`:

     ```toml
     schema = 1
     name = "…"
     [fonts]
     display = "…"   # a family in portable_fonts
     text = "…"      # a family in portable_fonts; may equal display
     [palette]       # exactly the system's palette_roles, 6-digit hex
     [why]           # optional in a pack voice: role → one line naming where the color comes from
     accepted = []   # optional { rule, reason }
     ```

  3. **Portable fonts.** They go in `thresholds.toml` `[common]` as data:

     ```toml
     portable_fonts = [
       { family = "Arial",           metric_twin = "Liberation Sans" },
       { family = "Times New Roman", metric_twin = "Liberation Serif" },
       { family = "Courier New",     metric_twin = "Liberation Mono" },
       { family = "Georgia",         metric_twin = "Gelasio" },
       { family = "Calibri",         metric_twin = "Carlito" },
       { family = "Cambria",         metric_twin = "Caladea" },
     ]
     ```

     - A voice may use only these families.
     - The fit estimator (§6.4) uses each family's metric twin.
     - Verdana and Trebuchet MS are excluded until an open metric-compatible font
       exists.

  4. **Brief.** A brief names its voice in exactly one of two ways; neither, or both,
     is a schema error (exit 1):
     - `voice = "<name>"` names a voice of the brief's pack;
     - an inline `[voice]` table has the voice schema without `name`. An inline voice
       needs a `[voice.why]` line for every palette role.

  5. **Voice checks.** These run in `keyline brief`, and whenever a pack voice is
     loaded.
     - **Schema errors (exit 1):**
       - a missing or extra role;
       - a malformed hex value;
       - a font not in `portable_fonts`;
       - an unknown voice name.
     - **New registry entries,** each with `requires = "brief"`, category `quality`,
       scope `deck`, basis `color` (or `structure` for `voice-why`):

     | id | severity | fires when |
     |---|---|---|
     | `voice-contrast` | error | a (text color, surface) pair that the system allows is below `contrast_normal`. One finding per pair |
     | `voice-claude-look` | warning | the voice's `paper` is in the cream band and any voice color is in the terracotta band (the §3.2 bands). Advisory when only the cream condition holds, and advisory when the voice or pack lists it in `accepted` with a reason |
     | `voice-why` | warning | an inline voice lacks a `why` line for a palette role |

  6. **Counts.** AC-1 now expects **35** registry entries (32 + 3). AC-2's
     `test_rules_listing` accepts the same 35. This supersedes B-1's count.

  7. **Invariants.** §5.4 invariants 4 (contrast) and 6 (fonts) are checked **per
     voice**.
     - Invariant 5 (neutral paper, no terracotta) becomes a test of the `neutral`
       voice only. Every other voice is covered by `voice-claude-look` instead.
     - Invariants 1, 2, 3 and 7 stay on the system.

  8. **Pack rules resolve the voice.**
     - `off-palette-color`, `off-pack-font` and `accent-overuse` use the resolved
       voice's palette, fonts and accent roles.
     - `lint` and `check` gain `--voice NAME|FILE`. `--brief` supplies the voice.
     - A `--voice` that disagrees with the brief is exit 1, as for `--mode`.
     - `--pack` with no voice from either source is exit 1: "pack rules need a voice
       (--voice or --brief)".
     - `expect.toml` cases gain an optional `voice` key.

  9. **Templates.** They are built per (system, voice, mode) by the template builder,
     in memory and byte-stable.
     - Theme major font = display, minor font = text. Theme colors come from the
       roles, with the plan's mapping.
     - Only the `neutral` templates are committed, for inspection and AC-9. A test
       rebuilds them byte-identically.
     - The pen builds the template for its voice when it creates a `Deck`.

  10. **Stock voices for Swiss.** These three voices ship with the pack. The values
      are normative; the auditor computed the checks.

      | voice | fonts (display / text) | paper | ink | muted | hairline | accent | accent_on_ink |
      |---|---|---|---|---|---|---|---|
      | `neutral` | Arial / Arial | `F2F2F0` | `111111` | `5C5C5A` | `B8B8B4` | `CC3322` | `E8422E` |
      | `night` | Arial / Arial | `16181B` | `ECECE8` | `A3A7AC` | `3D4148` | `F0B429` | `8A5A00` |
      | `field` | Georgia / Georgia | `EEF2EE` | `16251D` | `4A5A51` | `B6C2BA` | `1D4FB8` | `8DB2FF` |

      Checks (contrast ratios, plus the paper's CIELAB values and the accent's HSL
      hue):

      | voice | ink/paper | muted/paper | accent/paper | paper/ink | accent_on_ink/ink | paper L\* / C\* / h | accent HSL h |
      |---|---|---|---|---|---|---|---|
      | `neutral` | 16.85 | 5.98 | 4.61 | 16.85 | 4.72 | 95.4 / 1.02 / 110 | 6 |
      | `night` | 15.02 | 7.35 | 9.54 | 15.02 | 5.00 | 8.2 / 2.44 / 267 | 42 |
      | `field` | 14.11 | 6.47 | 6.49 | 14.11 | 7.55 | 95.1 / 2.51 / 144 | 221 |

      - No voice has a cream paper, and no voice color is in the terracotta band.
      - In `night`, paper is the dark surface and ink the light one. The `section`
        role (`ink` surface) is therefore light, which is intended: sections invert
        in every voice.

  11. **Fit tables** (§6.4) cover every `portable_fonts` family, regular and bold,
      from its metric twin.
      - The generator records each source font's file name, version and license in
        `NOTICE`.
      - AC-13(a) runs for every twin whose TTF is present, and skips the rest by name.
      - CI installs `fonts-liberation`, `fonts-crosextra-carlito` and
        `fonts-crosextra-caladea`.
      - Gelasio comes from its upstream release, or AC-13(a) skips Georgia and the
        report says so.

  12. **doctor.** The render-font check covers every `portable_fonts` family: each is
      `FONT_OK` when `fc-match` returns the family or its metric twin, else
      `FONT_SUBSTITUTED`, listed by family.

  13. **Specimens** (Phase A2) are built in more than one voice:
      - `swiss-specimen-presented` in `neutral` and in `night`;
      - `swiss-specimen-read` in `field`.

      AC-11 and AC-12 apply to each of the three. G-1 reviews all three contact
      sheets.

  14. **BonsaiHub** (§10). Each brief defines an **inline voice** derived from
      `[product.world]`, with `[voice.why]`. Both decks may share it. `keyline brief`
      exits 0 on both briefs (no `voice-*` finding above advisory). G-2 judges the
      voice as part of the soul verdict.

  15. **Skill** (Phase B).
      - The loop gains a voice step after the direction: derive the voice from
        `own_world`, and record a `why` line per role.
      - The stock voices are fallbacks, used only when the user asks for a plain look
        or gives no subject world.
      - `craft-floor.md` states the voice checks with `<!-- rule:voice-* -->` anchors.
      - `anti-tells.md` gains the row `one-look-for-everything` → `brief:voice-why`,
        plus `backlog:diversity-fingerprint` (§13).

  16. **Backlog** (for spec 003, output diversity):
      - `diversity-fingerprint`: palette, fonts and role mix per deck, compared across
        decks with `keyline diversity`;
      - a recent-voice memory in the skill;
      - two or three more **systems** with different structure;
      - brand mode (a company template disables the diversity checks);
      - `office-default-font` (Calibri as a tell);
      - Verdana and Trebuchet MS, once a metric-compatible open font exists.
- **B-9 (2026-09-29, audit 02).**
  - `voice-claude-look` tests every palette role that a system surface uses as a
    background (Swiss: `paper` and `ink`).
  - `night`'s ink becomes **`ECECEC`**. Auditor's checks: C\* 0.00; ink/paper 15.06;
    paper/ink 15.06; accent_on_ink/ink 5.02. No stock voice then has any `voice-*`
    finding.
- **B-10 (2026-09-29, audit 02).**
  - `accepted` in a pack, a pack voice or an inline voice may list only the rules in
    `acceptable_rules`. This is new data in `thresholds.toml` `[common]`: `claude-look-palette`,
    `voice-claude-look`, `closing-cliche`, `accent-overuse`, `equal-card-row`,
    `title-underline`.
  - Each entry needs a non-empty `reason`.
  - Anything else is a schema error (exit 1).
  - This supersedes the Q-24 and Q-31 rulings.
- **B-11 (2026-09-29, audit 02).** `off-pack-font` compares family names exactly, after casefold
  and whitespace collapse, as voice fonts already do (deviation 7).
  - The reason: A-8's weight stripping let "Arial Black" and "Arial Narrow" pass as
    Arial.
  - `font-count` keeps A-8.
- **B-12 (2026-09-29, audit 02).** All of these are schema errors (exit 1, one line, naming the
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
- **B-12 (2026-09-29, audit 02), continued.**
  - The "optional spaces" of §3.1 are any Unicode space separators (category Zs) and
    tabs.
  - Classification uses the paragraph's inked text, the same text §4.4 scans.
  - Source lines inside table cells are out of scope for now; document this in
    `check.md`.
- **B-13 (2026-09-29, audit 02).**
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
- **B-14 (2026-09-29, audit 02).** Every OfficeCLI invocation (validate, screenshot):
  - works on a private temp copy with a unique file name;
  - runs `officecli close <copy>` in a `finally`;
  - deletes the copy.

  keyline never passes the user's deck path to OfficeCLI.
- **B-15 (2026-09-29, audit 02).**
  - An error envelope becomes one `ooxml-invalid` finding that carries its message.
  - An OfficeCLI that cannot start counts as absent:
    `validate: skipped (officecli could not run: <first line>)`, with the exit code
    unchanged.
  - doctor reports `NO_VALIDATOR` with that reason.
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
