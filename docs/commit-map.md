# Commit map: the move to tyler-void

On 2026-10-26 the repository moved to `tyler-void/keyline`. The move rewrote every commit,
so each one has a new hash. The reports, plans and audits written before it cite the old
short hashes. This table maps each cited hash to its commit now.

- **How it was built.**
  - Most rows match by subject. The old hash and its subject come from the git output
    recorded in the implementation session's log, which is not in the repository. Each
    subject names exactly one commit now.
  - For three rows, the doc that cites the hash also states its subject.
  - Four rows match by position: the audits give a branch head as the first commit, or
    as N commits over `main`, and the spec 001 report names the first and second T-33
    perf commits.
  - One hash is undetermined (below).
- **Not commits:** `c5b296f` is the end of a SHA-256 in
  `fixtures/foreign/stress/README.md`, and `e0881d2` is an impeccable commit cited in
  `docs/research.md`.
- **CI runs** cited before the move, such as 36245821572, belonged to the old repository.
  They are not in the new one.
- **Undetermined: `4b991fa`.** The spec 001 report gives it as the head of the last CI run
  after T-33's second perf commit. That is one of `e4f6bb3`, `a09247d` and `1fe68ed`, and
  nothing left says which.

115 rows, in the order of the commits now.

| Old | New | Subject | Matched by |
|---|---|---|---|
| `ce21744` | `49fd70b` | chore: bootstrap docs, spec 001, golden fixtures | subject |
| `705edc1` | `1350c46` | docs: plan and tasks for spec 001 (lint core) | position: the first commit on `001-lint-core` (audit 01) |
| `589d693` | `d2a31a5` | docs: report for spec 001 (T-25) | subject, as the doc states it |
| `564cd05` | `aab2721` | docs: apply audit 02 | subject, as the doc states it |
| `e1a3113` | `67c5c32` | perf: integer sweep for box-overlap, integer fast paths, XML-only size cap (T-33, A-18) | position: the first T-33 perf commit (spec 001 report) |
| `ec7ff14` | `41268bf` | perf: Clark-notation finds, cached text-bearing, integer coverage checks (T-33, A-18) | position: the second T-33 perf commit (spec 001 report) |
| `85e1285` | `026848b` | docs: report round 2, correct the list of local files | position: the head 45 commits over `main` (audit 03) |
| `24cb91e` | `d0353d9` | docs: apply audit 03 | subject, as the doc states it |
| `678c69a` | `7c2d3cd` | Merge pull request #1: Spec 001: lint core (M1) | subject |
| `926ab7f` | `cc33c29` | docs: add spec 002 and BonsaiHub product truth | subject |
| `bb27a9b` | `c3d80f5` | docs: record D-015..D-019 and L-011..L-015; spec 002 is active | subject |
| `28fcd93` | `415fe61` | ci: keep auditor evidence scripts under specs/ out of ruff | subject |
| `b349766` | `b59f6f7` | docs: plan and tasks for spec 002 (skill, brief, Swiss pack) | subject |
| `c46622f` | `9996afd` | test: M1 baseline of rule, foreign and stress deck output (T-01) | subject |
| `25fb094` | `1c7b1a6` | build: pen and render extras, dev tools for fit tables, Liberation fonts in CI (T-02) | subject |
| `54d1d31` | `a458398` | feat: registry requires field, lint context, three-argument rule checks (T-03) | subject |
| `d2335fd` | `9eaeac7` | feat: typed config with the spec 002 thresholds and string-list keys (T-04) | subject |
| `797fca8` | `dd8a4f4` | feat: slide roles from keyline layout names; role-aware dead-band and notes-missing (T-05) | subject |
| `3e8f270` | `f14170b` | fix: restore the spec 001 rule decks rebuilt by T-05; add --only to build_rules | subject |
| `2ba9e09` | `6f3c1bc` | feat: source and note lines leave body; own floor in body-too-small (T-06, B-2) | subject |
| `ca148f6` | `2f3dcba` | feat: colour spaces; claude-look-palette, title-too-long, closing-cliche (T-07) | subject |
| `ea659b7` | `49e0af8` | feat: pack format and loader; Swiss pack v1 data; keyline packs (T-08) | subject |
| `4da8304` | `270832c` | feat: byte-stable zip writer for templates, pen and skill builds (T-09, part 1) | subject |
| `b35ff05` | `46191e4` | feat: Swiss templates from raw OOXML (T-09, part 2) | subject |
| `c753c12` | `98d3463` | docs: amendment B-8 (systems and voices); D-020 | subject |
| `4a3b299` | `6f27ac0` | feat: Swiss as system plus voices; neutral, night, field (T-08r, B-8) | subject |
| `dff39b0` | `afa0278` | feat: templates per voice; theme fonts display/text (T-09r, B-8.9) | subject |
| `5c227ea` | `7294fb2` | feat: pack rules resolve the voice; --pack and --voice (T-10, B-8.8) | subject |
| `5f696e3` | `1ed7d36` | feat: numeric tokens and table text (T-11) | subject |
| `ff1717f` | `95fe2ff` | feat: briefs, evidence and keyline brief, with the brief's voice (T-12) | subject |
| `e1ea9e5` | `c5bef4d` | feat: deck vs brief; --brief, --mode default None, conflicts (T-13) | subject |
| `7fb1253` | `e80ca8f` | test: AC-8 on the fixture-built drift decks (T-14, B-3) | subject |
| `fe43a33` | `6c30e58` | feat: LibreOffice render engine; --engine auto\|libreoffice\|officecli (T-15) | subject |
| `c297d46` | `c9ddb41` | feat: validate step in check; ooxml-invalid (T-16) | subject |
| `13f2af2` | `65ac62a` | feat: keyline doctor, with a font check per portable family (T-17) | subject |
| `ba905c7` | `31a7a10` | test: A1 acceptance sweep; docs for roles, table text and voices (T-18) | subject |
| `c335e18` | `b3b80b4` | fix: build_templates.py creates its output directory | subject |
| `447017a` | `18f31a9` | docs: report A1 for spec 002 (T-19) | subject |
| `59360d1` | `7d0a7eb` | docs: audit 02 of A1; amendments B-9..B-15; L-016 | subject |
| `5ed1fb6` | `683bdf1` | fix: OfficeCLI always works on a private copy (FX-1, B-14) | subject |
| `9ad763d` | `6d85476` | fix: accepted may list only acceptable_rules, with a reason (FX-2, B-10) | subject |
| `6efe82f` | `af829e6` | fix: render numbering and hygiene (FX-3, B-13) | subject |
| `af571f3` | `444260b` | fix: the validate step's error paths (FX-4, B-15) | subject |
| `275082a` | `d251687` | fix: schema tightening and one-line errors (FX-5, B-12 items 1-7, X-17) | subject |
| `3477af7` | `fe9bd0f` | fix: voice-claude-look checks every background; night ink; exact fonts (FX-7, B-9, B-11) | subject |
| `a910810` | `041023a` | docs: record the tokenizer's known limits; pin python-pptx for the drift builder (FX-8) | subject |
| `525ccb2` | `50892ce` | docs: A2 tasks; audit 02 rulings in the plan; metric twins installed | subject |
| `ecc017f` | `0f16875` | fix: render checks the deck and -o before the engine (FX-3 follow-up) | subject |
| `b7d58c2` | `224a7bd` | docs: record the FX-3 follow-up and its CI failures in report.md | subject |
| `3e635cc` | `5dbb294` | docs: audit 03; amendments B-16..B-20; A2 rulings | subject |
| `f43b9cf` | `a4b64cc` | fix: LibreOffice converts a private copy with a fixed name (FX-9, B-19) | subject |
| `636965f` | `4e32762` | fix: the OfficeCLI copy is named .pptx whatever the user's name (FX-10, B-19) | subject |
| `2848e28` | `4c76a19` | fix: engine hygiene under odd output, timeouts, signals and an empty -o (FX-11, B-19) | subject |
| `a3c141b` | `d0ea0cb` | fix: a voice's schema is closed (FX-12, B-18) | subject |
| `97b4e8c` | `77051ad` | fix: an unreadable pack or voice path is one line, not an internal error (FX-13) | subject |
| `e9ed928` | `7380b67` | fix: reasons, schema types and one-line messages (FX-14, B-20) | subject |
| `126fc59` | `e5374cb` | fix: engine-selection test, L-002 only where it applies, one known limit (FX-15) | subject |
| `2c3dbf3` | `b80a8bf` | test: measure LibreOffice 26.8.0.3 line pitch and wrap margin (T-20, B-7) | subject |
| `cf567ee` | `8f70ac5` | docs: audit 04; amendment B-21 | subject |
| `e93fa4a` | `1ad1cab` | test: B-21's measurement on LibreOffice 26.8.0.3: both criteria hold (T-20 addendum) | subject |
| `ef05c36` | `588db46` | docs: fold audit 04's rulings into T-21, T-22 and T-32 | subject |
| `452a480` | `b0505f8` | feat: fit tables for the six metric twins (T-21, B-8.11, B-21) | subject |
| `384c695` | `0e170eb` | feat: the fit estimator (T-22, §6.4 with B-21); AC-13(a) | subject |
| `c204ee2` | `6196adc` | feat: the pen's skeleton and writer isolation (T-23, §6.1, D-015) | subject |
| `8c0f946` | `b6219c0` | feat: the pen's text verbs (T-24, §6.1–§6.2) | subject |
| `4508af4` | `3b47811` | feat: table, chart_bar and image verbs (T-26, §6.1, §6.4, §6.6) | subject |
| `b411a92` | `f18166e` | feat: byte-identical pen saves, charts included (T-27, §6.5, L-013) | subject |
| `a30a754` | `c00f75d` | feat: Swiss specimens in three voices (T-28, §11.13, AC-11, AC-12) | subject |
| `5cb9db7` | `a2e24e6` | test: AC-8 on a pen-built base, and core purity (T-29, B-3, AC-15) | subject |
| `4e74905` | `0bfb511` | feat: AC-13(b) fit stress, and fit tables cached before the config (T-30) | subject |
| `658962c` | `771683f` | docs: the pen in README and A2 in CHANGELOG; the A2 sweep (T-31) | subject |
| `e4a2f26` | `ef825ed` | test: stand-in engine tests skip when there is no sleep binary | subject |
| `6ed849d` | `97427c0` | test: fit stress covers tables, figures and attributions; AC-13(b) fails at the left edge | subject |
| `ad17fa9` | `45dfcd0` | test: the pen's coverage warning, once per deck (T-22, audit 04) | subject |
| `0f8cc5a` | `7de637f` | test: write the FX-14 test's invisible characters as escapes | subject |
| `792902e` | `7082bc2` | fix: the estimator and the writer see the same text (FX-16, B-22 items 1-3) | subject |
| `fa6c30b` | `d5509e5` | fix: no line break before closing punctuation (FX-17, B-22 item 4) | subject |
| `18f80ba` | `e577796` | test: measure table-cell pitch, fallback advances and line breaks on 26.8.0.3 | subject |
| `2b85812` | `853ef39` | test: FX-17's LibreOffice check, in both line conditions | subject |
| `36a1bf6` | `3dfdcf3` | fix: table cells at max(1.2, hhea), and 0.01 mm more per row (FX-18, B-22 item 5) | subject |
| `cfec9e0` | `e62c405` | fix: a missing glyph counts as missing_glyph_em at least (FX-19, B-22 item 6) | subject |
| `4e879a6` | `2752225` | fix: inputs checked at the verb; images read once; save() atomic and typed (FX-20, B-23) | subject |
| `352a750` | `388f951` | fix: a style below the body minimum sets captions only (FX-21, B-23) | subject |
| `9f63c65` | `0618863` | test: T-24's does-not-fit case uses a lede (after FX-21) | subject |
| `e7c8f49` | `04a996d` | fix: refused verbs change nothing; footer, flags, next() and bullets (FX-22, FX-23, B-23) | subject |
| `a7ae6c1` | `4e2e974` | fix: the numeral box is one numeral line (Q-48, audit 05) | subject |
| `4a992d9` | `64115cf` | fix: keep room under a region's last line for the twin's descent (A2 fixes) | subject |
| `224ad9d` | `64d9afc` | feat: a vertical anchor per region; titles sit on the rule or the lede (FX-24) | subject |
| `0b8802a` | `561210c` | test: AC-13(b) as amended by B-24, over the six portable families (Q-47) | subject |
| `1dd6216` | `ec5926a` | docs: A2 fixes (audit 05) in report.md; CHANGELOG | subject |
| `dce55ad` | `532c36b` | fix: B-25's measured set, one definition and one warning (B-25 item 1, Q-51) | subject |
| `98483bc` | `7f7ba3e` | fix: positive kerning widens the estimate (FX-26, B-25 item 4) | subject |
| `f9c9453` | `a138800` | fix: no line break after opening punctuation (FX-27, B-25 item 5) | subject |
| `fa0e8c0` | `ad2e409` | fix: measured cell data, per version (FX-28, FX-31, B-25 item 6) | subject |
| `9c31d5c` | `bc3f902` | fix: complex scripts in the voice's family (FX-29, B-25 item 7) | subject |
| `b74c0ae` | `ca3e048` | fix: chart series and invisible text checked at the verb (FX-30) | subject |
| `51fe28f` | `03488c2` | fix: top allowance for stacked capitals (FX-25, B-25 item 2) | subject |
| `b6ef63a` | `9c04263` | fix: the numeral set (FX-25, B-26) | subject |
| `d758589` | `4957a6a` | docs: measure_lo and fit_stress on 26.8.0.3 (A2 fixes, round 2) | subject |
| `6ba6487` | `1f1e8de` | docs: A2 fixes, round 2 (audit 06) in report.md; Phase B tasks T-33 … T-49 | subject |
| `e6d3a77` | `c3984d6` | fix: U+2212 joins the measured set (B-27 item 1, Q-53) | subject |
| `2e4d38d` | `5c80891` | fix: the last glyph's right reach widens a line (FX-32, B-27 item 2) | subject |
| `4cc267c` | `7665018` | fix: kerning pairs across default-ignorable code points (FX-34, B-27 item 4) | subject |
| `9856b27` | `1493298` | docs: B-28, G-1 passed; G-2 judges correctness, the soul verdict moves to spec 003 | subject |
| `172903e` | `ed718c7` | fix: measured break sets (FX-33, B-27 item 3) | subject |
| `73e577e` | `91ee26f` | fix: missing_* over every environment measured (FX-35, B-27 item 5) | subject |
| `53a579d` | `5ad8c03` | docs: measure_lo and fit_stress on 26.8.1.1 (Phase B prelude, B-27) | subject |
| `b3e6ab1` | `145d710` | docs: Phase B prelude (B-27) in report.md; Q-60, Q-61 | subject |
| `66b7af5` | `a6ab80f` | fix: a refused headline names its slide; kl.py run prints a refusal in one line | subject |
| `f793a0e` | `9c8407e` | docs: headlines are checked against their titles before the spine is shown | subject |
| `d5c90f9` | `0db5e1f` | feat: demo.py sets up and records the BonsaiHub demo (T-46, tooling) | subject |
| `3566cb4` | `5943384` | docs: report B, in progress; Q-62; the steps for T-46 and T-47 | subject |
| `f523a1a` | `91dadb0` | docs: Q-60..Q-62 ruled; 24.2.7.2 break entry from the full probe | subject |
| `432ca4a` | `0a8ab92` | fix: probe the measured set's characters the twins lack (FX-36) | subject |
| `9816baf` | `fd82920` | test: FX-36's font choice runs only where the twins are installed | subject |

## After the move

On 2026-10-30 the snapshot commit was amended to drop five files that should never have
been committed, three of which hold the old work e-mail. The branch `002-skill-pack` was
force-pushed. The commits after the snapshot were re-applied on top of it.

| Old | New | Subject | Matched by |
|---|---|---|---|
| `322e706` | `fe60fd9` | Snapshot of the working tree before the move to tyler-void | the amend |
