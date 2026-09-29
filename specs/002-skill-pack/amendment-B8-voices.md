# Amendment B-8 to spec 002: systems and voices

- **Decided by:** Tyler, 2026-09-29. Output must fit many topics, fields, ideas and
  audiences, and must not collapse into one look. Web design has already fallen into
  that trap once: the "Claude look".
- **Written by:** the auditor.
- **Append** the text under "Amendment (verbatim)" to the amendment log of
  `specs/002-skill-pack/spec.md`.
- **Append** D-020 to `docs/decisions.md`.

## Why now

T-08 already names colors by role (`paper`, `ink`, `muted`, `hairline`, `accent`,
`accent_on_ink`), and every style refers to those names. So moving the palette and
fonts out of the pack is a data change. The work is confined to T-08, T-09 and T-10.
Once templates exist, the same change would cost far more.

## Evidence used (checked 2026-09-29)

- **Fonts on every desktop.** Arial, Courier New, Georgia, Times New Roman, Trebuchet
  MS and Verdana ship with Windows, and with macOS 10.4 and later. Source: Wikipedia,
  "Core fonts for the Web".
- **Office fonts.** Calibri and Cambria come with Microsoft Office on Windows and Mac.
  Google Slides offers Calibri (BrightCarbon). Cambria in Google Slides, and both
  fonts on a Mac without Office, were not checked.
- **Metric-compatible open fonts** (same glyph widths). These are what make fit tables
  and LibreOffice renders honest:
  - Liberation Sans / Serif / Mono for Arial, Times New Roman and Courier New
    (Croscore Arimo, Tinos and Cousine are equivalent).
  - Gelasio for Georgia. Its README states it "is metrics compatible with Georgia in
    its Regular, Bold, Italic and Bold Italic weights" (OFL-1.1).
  - Carlito for Calibri and Caladea for Cambria (Crosextra).
- **Verdana and Trebuchet MS** have no open metric-compatible font, so they stay out
  until one exists.
- **What the sandbox substitutes.** `fc-match` in the auditor's sandbox maps
  Georgia → DejaVu Serif, because Gelasio is not installed. Calibri → Carlito and
  Cambria → Caladea are already mapped.
- **Installing Gelasio is enough.** fontconfig's stock `30-metric-aliases.conf`
  already aliases Georgia to Gelasio, so once Gelasio is installed, LibreOffice renders
  Georgia with the right widths.
- **The three stock voices below** were computed by the auditor, with the WCAG 2.x
  contrast and CIELAB/HSL definitions of §3.3.

## Amendment (verbatim)

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

## Decision to append

- **D-020 · Systems and voices (Tyler, 2026-09-29).** A pack is one system (structure)
  plus voices (palette and fonts). Each deck picks or derives its voice from its brief,
  under measured checks (B-8).
  - This supersedes D-017's "Swiss v1 uses Arial only". Voices may use any family in
    `portable_fonts`: those present with Windows, macOS or Office that also have an
    open metric-compatible twin.
  - Why: a single fixed look becomes a tell at scale. Web design shows this with the
    "Claude look". Diversity has to come from each deck's subject, not from a catalog
    or chance.

## Tasks this touches

A1 is at T-09 part 1 (`4da8304`).

- **T-08 (rework):**
  - move `[palette]` and `fonts` from `packs/swiss/pack.toml` into `voices/neutral.toml`;
  - add `palette_roles` and a `font` field per style;
  - add `voices/night.toml` and `voices/field.toml`;
  - run the invariant tests per voice.
- **T-09:** the template builder takes a voice. Only the neutral templates are
  committed.
- **T-10:** the pack rules resolve the voice; add `--voice`; add the `voice` key to
  `expect.toml` cases.
- **T-12:** the brief's voice (name or inline), the voice checks, and the three new
  registry entries.
- **T-17:** the doctor font check per portable family.
- **T-18:** AC-1 and AC-2 now expect 35 entries.
- **A2:** fit tables for all six families; specimens in three voices.
- **B:** the voice step in the skill; the BonsaiHub inline voices.
