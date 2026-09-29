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
- Decisions D-015 … D-019 were confirmed by Tyler on 2026-09-27 (spec 002 §0), with the
  sources checked that day:
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
- **D-020 · Systems and voices (Tyler, 2026-09-29).** A pack is one system (structure)
  plus voices (palette and fonts). Each deck picks or derives its voice from its brief,
  under measured checks (B-8).
  - This supersedes D-017's "Swiss v1 uses Arial only". Voices may use any family in
    `portable_fonts`: those present with Windows, macOS or Office that also have an
    open metric-compatible twin.
  - Why: a single fixed look becomes a tell at scale. Web design shows this with the
    "Claude look". Diversity has to come from each deck's subject, not from a catalog
    or chance.
