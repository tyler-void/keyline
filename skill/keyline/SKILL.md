---
name: keyline
description: Make PowerPoint decks that look designed, not generated. A brief with a thesis, a pen that writes only pack tokens, and a deterministic check. Use to make, check or revise a .pptx deck.
license: Apache-2.0
compatibility: Python 3.11+ with lxml, Pillow and python-pptx 1.0.2 (the pen needs python-pptx; checking a deck does not). LibreOffice or OfficeCLI are optional, for previews. Runs in Claude Code, and on claude.ai and Claude desktop with code execution on.
---

# keyline

## Stance

A deck is an argument before it is a design. The brief decides what is said, the pack
decides how it looks, and `check` decides when it is done. You write the content and
choose among the pack's tokens. You never place a shape, pick a size or type a colour
by hand.

## Where things are

Every path in this skill is relative to **the skill folder**: the folder that holds this
file. You know it from the path you loaded this file from.

- Claude Code: the `keyline` folder inside your skills directory.
- claude.ai and Claude desktop: the folder the uploaded skill was unpacked into, in the
  code sandbox.

Run every command as `python <skill folder>/scripts/kl.py …`. `kl.py` finds the keyline
library by itself. Write your files in the user's working folder, never in the skill
folder.

| Read | When |
|---|---|
| `references/brief.md` | before writing a brief, and at the voice step |
| `references/craft-floor.md` | right before every build |
| `references/pen.md` | while writing a build script, and when the pen refuses |
| `references/check.md` | when `check` or `brief` reports a finding |
| `references/anti-tells.md` | when the user asks why a rule exists |

## Setup

Run `kl.py doctor` once per session. It prints one line per check; each starts with a
token.

| Token | What to do |
|---|---|
| `PYTHON_OK`, `LXML_OK`, `PILLOW_OK`, `PPTX_OK` | Nothing. |
| `PYTHON_OLD` | Stop. keyline needs Python 3.11 or later; tell the user. |
| `NO_LXML`, `NO_PILLOW` | Run the install line it prints. Without them nothing runs. |
| `NO_PPTX` | Run `pip install python-pptx==1.0.2`. If that fails (no network), the pen cannot build a deck: offer route 2 only, and say why. |
| `RENDER_LIBREOFFICE`, `RENDER_OFFICECLI` | `check` will render a contact sheet. Look at it at step 9. |
| `NO_RENDERER` | No preview. `check` still lints. Say in the report that nothing was rendered. |
| `RASTER_PDFIUM`, `RASTER_PDFTOPPM` | Nothing. |
| `NO_RASTER` | Run the install line it prints, or go on without a LibreOffice preview. |
| `VALIDATE_OFFICECLI` | `check` also validates the file's schema. |
| `NO_VALIDATOR` | Validation is skipped. Say so in the report. |
| `FONT_OK` | Nothing. |
| `FONT_SUBSTITUTED` | The preview sets that family in another font, so its line breaks can differ from PowerPoint's. Prefer a `FONT_OK` family for the voice, or say so in the report. |

## Routes

1. **New deck.** Follow the loop.
2. **Check a deck.** Run `kl.py check DECK.pptx` on any deck, with `--brief BRIEF` when it
   has one. Read `references/check.md`, explain each finding in the user's words, and
   propose fixes. Do not rebuild a deck you did not build unless the user asks.
3. **Revise.** Edit the build script, never the `.pptx`. Rebuild with `kl.py run`, then
   check again.

## The loop

1. **Mode.** `presented` (shown live, few words) or `read` (read alone, denser). If the
   user has not said how the deck will be used, ask that one question.
2. **Evidence.** Every number on a slide needs a source. Write the evidence file, or use
   the user's. If their file is read-only or theirs to keep, add a second file with
   only `[[evidence]]` entries. Record a number the user gave you with the source
   `user, <date>`. A value holds digits, signs and unit words; the rest goes in its
   label.
3. **Brief.** Read `references/brief.md`. Write `<deck>.brief.toml`: the direction
   (audience, decision, thesis, `own_world`, motif), then one entry per slide with its
   role, headline and reads. The headlines alone must tell the story.
4. **Voice.** Derive the deck's look from its subject, not from habit. In the brief,
   write an inline `[voice]`: two font families and one hex colour per palette role,
   each with a `[voice.why]` line that names the thing in `own_world` it comes from.
   - Pick the families from the coverage table in `references/brief.md`, so the font
     has every letter the deck's language needs.
   - The stock voices (`neutral`, `night`, `field`) are fallbacks. Use one only when the
     user asks for a plain look, or when there is no subject world to draw from.
5. **Spine.** Run `kl.py brief <deck>.brief.toml`. Fix what it reports, then show the
   user the spine it prints.
6. **Approval.** If the user is present, wait until they approve the spine. If they are
   not, go on and say that you did.
7. **Build.** Read `references/craft-floor.md`, then `references/pen.md`. Write
   `build_<deck>.py` with `Deck.from_brief`, one `deck.next()` per slide, and run it:
   `kl.py run build_<deck>.py`.
8. **Check.** Run `kl.py check <deck>.pptx --brief <deck>.brief.toml`. Exit 0 is clean,
   2 means findings, 1 means it could not read the deck. `-o DIR` chooses the folder
   for the preview.
9. **Look.** If `check` rendered a contact sheet and you can view images, look at it:
   does each slide say its headline at a glance?
10. **Fix once.** Apply one batch of fixes in the build script or the brief, rebuild,
    and run `check` one more time. Then stop: do not loop.
11. **Report.** See below.

## Priority

- The user decides the content. The skill decides the method.
- If the user asks for something the method forbids, do it, and name the rule it breaks:
  `check` will flag it.
- When the pen refuses with `DoesNotFit`, change the content: shorten it, or split the
  slide. Never change a token to make text fit.
- When the pen prints `keyline pen: warning:`, the fit does not cover some characters.
  Change the voice's font, or the wording, before you trust the preview.
- Never write deck content with raw python-pptx or OfficeCLI.

## Report

End with:

- the files: the deck, its brief, its build script;
- the mode, the pack and the voice, with where the voice came from;
- the exit code of the last `check`;
- each finding that remains, and why it stays;
- whether a preview was rendered, with which engine, and whether the schema was
  validated;
- the known limits: fonts are not embedded, so the voice's families (or their metric
  twins) must be on the machine that opens the deck.
