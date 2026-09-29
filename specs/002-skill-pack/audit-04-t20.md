# Audit 04 of spec 002: fix round 2 and the T-20 stop

- **Audited:** branch `002-skill-pack` at `2c3dbf3`, fresh clone, 2026-09-29.
- **Auditor:** the external session. **Decides:** Tyler.
- **Verdict:**
  - **Round 2 (FX-9 … FX-15): ACCEPTED.** Every audit 03 repro now behaves as
    B-16 … B-20 require.
  - **T-20: the stop was correct, and the "DIFFERS" is my error, not a LibreOffice
    change.** Keep the 0.99 wrap margin and `line_pitch_em = 1.2`, with a per-line
    rounding allowance (B-21). Continue A2 once the widened measurement passes on 26.8.

## 1. Round 2, checked

| check | result |
|---|---|
| Identity, trailers | 10 commits, all `Tyler <code@tyler-void.dev>`, one Claude trailer each |
| Docs append-only | spec, decisions, lessons: 0 removed lines; B-16 … B-20 identical to audit 03's text (2,139 characters) |
| Hashes | audit 03 `645e4620…` equals the auditor's; product `9b0fea6e…`, oracle `af534e21…`; goldens untouched |
| Fixtures | only `expect.toml`, one message (FX-14: the file is named once) |
| ruff | clean, 155 files |
| pytest | **718 passed, 2 skipped**. The skips are the engine-selection test (no browser on its PATH here, by design since FX-15) and the non-root FX-13 test, which passes when run as `nobody` |
| M1 baseline | no differences |
| Regression | main vs branch: 308 pairs, 0 differing, 0 tracebacks |
| Fuzz | brief 2,023 cases, 0 bad; pack and voice (in process), 0 bad |

| item | repro | now |
|---|---|---|
| FX-9 | a symlinked deck; a deck named `deck.` | 4 PNGs each |
| FX-10 | `check "clean v1.2"`; `check deck.pptx.bak` | no `ooxml-invalid` |
| FX-11 | a shim officecli writing `\xfc` | `validate: skipped (officecli could not run: Fehler: �berlauf)`; doctor `NO_VALIDATOR` |
| FX-11 | `timeout 0.9 … 2.0 keyline check` | no `/tmp/keyline-oc-*`, no `/tmp/keyline-lo-*`, no resident, no soffice |
| FX-11 | SIGINT to the group mid-render (120 slides) | exit 130, "engine processes stopped"; soffice.bin is killed (reaped as `<defunct>`); the temp directory is gone |
| FX-11 | validate `TIMEOUT_S = 0.4` | no orphaned `officecli validate`, no resident |
| FX-11 | `render -o ''` | exit 1, "cannot use '' as the output directory"; planted files untouched |
| FX-12 | `accepted` after `[why]`; an unknown top-level key | "why.accepted: accepted belongs before [fonts]"; "unknown key 'wobble' (allowed: …)" |
| FX-13 | as `nobody`: locked pack; locked voice | "pack directory … cannot be read: Permission denied", exit 1 |
| FX-14 | `schema = true`; a `​` reason; `--pack $'swiss\nkeyline: all clear'` | refused; refused; one line, with `\n` escaped |

- **FX-15's deviation is accepted.** The L-002 note stays next to "officecli is not
  installed", because spec 001's `test_render_without_officecli_exits_1` requires it.

## 2. T-20: what the measurement means

### The same tool on LibreOffice 24.2

I ran `tools/measure_lo.py` unchanged in the auditor's sandbox: LibreOffice
24.2.7.2, with all six twins installed, and every `fc-match` gave `ok`.

- **Output:** `evidence/measure_lo-on-24.2.7.2.txt`.
- **Against Tyler's 26.8.0.3 file:**
  - The pitch table is identical.
  - The four-factor wrap table is identical. 24.2 also prints `DIFFERS`.
  - 11 of the 18 scan thresholds move by one step (0.0005): 10 of them need a box one
    step wider on 26.8, and 1 needs one step less. The other 7 are identical.

So nothing changed between 24.2 and 26.8. §6.4's sentence, "wraps at 1.000× and
1.002×, not at 1.005×", was one label's result written as if it were general. That is
my error; T-20 stopping on it was the right call.

### The wider test that the margin needs

The T-20 probes are three labels at 14 pt with no tracking. The Swiss pack goes down to
**9 pt** (read `source`) and to **10 pt caps with +8 % tracking** (read `label`). That is
where per-glyph rounding weighs most. So I ran a stress test.

- **Script:** `evidence/audit04_stress_fit.py`. It runs from `tools/` and imports
  `measure_lo`'s helpers.
- **Output:** `evidence/audit04-stress-lo-24.2.txt`. A second run was identical.
- **Wrap: 420 cases,** from 6 families × 2 weights × sizes 9, 10, 12, 14 and 24 pt × 7
  strings.
  - The strings: narrow glyphs, wide caps, digits and %, Vietnamese, a sentence, and
    two caps strings with +8 % tracking.
  - Each string sits in a box at 0.995×, 1.000×, 1.003×, 1.006× and **1/0.99 = 1.0101×**
    §6.4's estimate: the advance sum, upper-cased for caps, plus tracking × size per
    character.
  - **0 cases wrap at 1.0101×.** The worst one-line threshold is 1.003×, and it occurs
    only at 14 pt. At 9, 10, 12 and 24 pt, every string fits at 1.000× or less.
  - Tracked caps fit at 1.000× or less. This suggests LibreOffice does not add
    tracking after the last character (INFERRED), which leaves the estimate
    conservative.
- **Pitch at every (size, line spacing) the Swiss pack uses,** six twins, regular. The
  sizes run from 9 to 120 pt, at line spacing 1.0 and 1.1.
  - The measured pitch ÷ (size × 1.2 × line spacing) lies between **0.9986 and 1.0026**.
  - The worst case is 9 pt: 10.828 pt against 10.800 pt, which is +0.028 pt, one
    LibreOffice layout unit (0.01 mm).
  - Every measured pitch is ≤ size × 1.2 × spacing **+ 0.01 mm**.
  - The first baseline sits at 1.00 em below the box top at spacing 1.0, and at
    1.12 em at spacing 1.1. So the extra spacing is added above the first line too,
    and n × pitch already counts it.

### A finding the stress test surfaced: Caladea has no Vietnamese

- **Coverage.** Caladea 1.001, Cambria's twin, lacks **88 of 134** Vietnamese letters:
  Ơ, Ư and every letter with a dot below or a hook above. The other five twins cover
  all 134.
- **Upstream.** Caladea's latest release is still 1.001 (2013, WGL glyph list), per its
  repository (VERIFIED).
- **Effect on output.**
  - PowerPoint uses real Cambria, which covers Vietnamese, so the delivered deck is
    fine.
  - LibreOffice's render substitutes a fallback font for those letters, so the check
    render of a Vietnamese deck in a Cambria voice is not faithful.
  - The estimator gives them the maximum advance, which stays conservative.
- **Why it matters.** Tyler's own audience includes Vietnamese, and the skill's voice
  step should know this.

## 3. Rulings

1. **Wrap margin:** keep §6.4's rule: a line fits when its estimate ≤ 0.99 × the
   available width.
2. **Line pitch:** `line_pitch_em = 1.2` for all six twins, stored with the
   LibreOffice version that measured it. The height test adds **0.01 mm per line**,
   LibreOffice's layout unit. That bound holds for every pitch measured.
3. **Before T-21, one more measurement, and no stop if it passes.** Fold the auditor's
   stress set into `tools/measure_lo.py`, then run it on 26.8.0.3 and commit the
   output as evidence. It passes when **both** of these hold:
   - no case wraps at 1/0.99;
   - every pitch is ≤ size × 1.2 × spacing + 0.01 mm.

   The tool's verdict becomes these two criteria, replacing the old sentence, so a
   re-run exits 0. If either criterion fails, stop and report as before.
4. **Coverage:**
   - The fit tables (T-21) record which of the 134 Vietnamese letters each twin lacks.
   - When the estimator meets characters missing from the voice's twin, the pen prints
     one warning per deck: "Caladea (for Cambria) lacks: …; LibreOffice renders them in
     a fallback font, so the check render is not faithful". The build goes ahead.
   - This is a warning, not a registry entry.
   - The limit goes into Phase B's `check.md` and the voice step: prefer another
     family for Vietnamese text.
   - Spec 003 gets a script-coverage check per voice (backlog).

## 4. Auditor's own errors this round

1. §6.4's wrap sentence generalized one label's result. It also named no string, so it
   could not be compared like for like.

## Amendment to append (verbatim)

- **B-21 (2026-09-29, audit 04).** §6.4's fit constants, as measured on LibreOffice
  24.2.7.2 (auditor) and 26.8.0.3 (T-20). The two agree within one 0.0005 scan step.
  - **Wrap:** the one-line threshold of a string is 0.998× … 1.003× its advance sum. It
    varies with the string, family and size.
    - The rule stays: a line fits when its estimate ≤ 0.99 × the available width.
    - No case wrapped at 1/0.99 in 420 stress cases: 9–24 pt, regular and bold,
      tracked caps, Vietnamese.
    - This replaces §6.4's sentence "LibreOffice wrapped a bold 14 pt label to 2 lines
      at 1.000× and 1.002× its advance sum, but not at 1.005×".
  - **Pitch:** `line_pitch_em = 1.2` for every twin. A region holds n lines when
    n × (size × 1.2 × line spacing + 0.01 mm) plus the paragraph spacing ≤ its height.
    Every pitch measured, 9–120 pt at spacing 1.0 and 1.1, is within that bound.
  - **Coverage:** Caladea (for Cambria) lacks 88 of 134 Vietnamese letters. The pen
    warns when a deck uses them, and LibreOffice renders them in a fallback font.
