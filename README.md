# keyline

Deterministic design checks and a render loop for AI-generated PowerPoint decks.

**Status: pre-alpha.** Thresholds are uncalibrated, rule IDs may still change before
0.1.0 is released, and nothing is published to PyPI. Work in progress:
[`specs/002-skill-pack`](specs/002-skill-pack/spec.md) (the lint core of
[`specs/001-lint-core`](specs/001-lint-core/spec.md) is done).

## Install (from source)

Python 3.11 or newer.

```sh
git clone https://github.com/tyler-void/keyline && cd keyline
python -m pip install -e '.[dev]'
```

## Commands

| command | what it does |
|---|---|
| `keyline lint deck.pptx [--mode presented\|read] [--json]` | Reads the `.pptx` directly and runs the rule registry. JSON findings go to stdout, readable lines to stderr. Exit 0 = clean, 2 = warnings or errors, 1 = could not scan |
| `keyline lint deck.pptx --brief deck.brief.toml` | Also checks the deck against its brief (slide count, roles, headlines, sourced numbers, disclosure). The brief supplies the mode, the pack and the voice |
| `keyline lint deck.pptx --pack swiss --voice neutral` | Also runs the pack rules: colours, sizes, fonts and accents must come from the pack's system and the voice |
| `keyline brief deck.brief.toml [--json]` | Validates a brief and its evidence, prints the spine, and reports brief and voice findings |
| `keyline packs [--json]` | Lists the bundled packs and their voices |
| `keyline rules [--json]` | Lists every rule with its category, severity, basis, `requires` and rationale |
| `keyline render deck.pptx -o DIR [--engine auto\|libreoffice\|officecli]` | One PNG per slide plus `contact.png` |
| `keyline check deck.pptx [--brief …] [-o DIR] [--no-validate]` | Lint, then `officecli validate` when OfficeCLI is installed, then a best-effort render. Exits with lint's code unless validation finds errors |
| `keyline doctor [--json]` | What this machine can run: Python, lxml, Pillow, python-pptx, render engine, rasterizer, validator, and each portable font |

`keyline lint` needs only `lxml` and `Pillow`: no network, no model calls, no OfficeCLI.
JSON is always UTF-8, whatever the terminal's encoding. An internal error prints one
line and exits 1; add `--traceback` to any command to see the full trace.

**Rendering** uses LibreOffice with a rasterizer (`pip install pypdfium2`, or poppler's
`pdftoppm`) when both are present, else [OfficeCLI](https://github.com/iOfficeAI/OfficeCLI)
(`npm install -g @officecli/officecli`). Each engine prints its known limits: LibreOffice
re-fits stored autofit and substitutes fonts through fontconfig (L-010); OfficeCLI
screenshots fall back to sans-serif for fonts that are not installed (L-002). Renders are
closest to PowerPoint when each voice font's metric twin is installed (`keyline doctor`).

## Packs and voices

A pack is one **system** (grid, type scale, roles, regions, colours named by role) plus
**voices** (the colour values and a display and a text font). Swiss ships three voices:
`neutral`, `night` and `field`; a brief may name one or define its own, derived from the
subject's world. Voice fonts come from families that ship with Windows, macOS or Office
and have an open metric-compatible twin (D-020).

## The pen

`keyline.pen` writes decks from tokens: roles, style names, region names and evidence
ids. No parameter takes a colour, a font, a size or a position. Every text is checked
against its region before it is written, and text that would not fit raises `DoesNotFit`
instead of shrinking. The pen needs python-pptx (`pip install -e '.[pen]'`); `keyline
lint` never imports it. From the repository root:

```python
from keyline.pen import Deck

deck = Deck.from_brief("fixtures/briefs/drift/base.brief.toml")  # pack, mode, voice, evidence
deck.next().text("A slow dating app for trees and their keepers", style="lede")
deck.next()  # a statement: its headline is the slide
deck.next().figure("waitlist_trees").source()
deck.next().text("71% of keepers are still active after 90 days").source()
deck.next().text("Join the waitlist as a keeper this season", style="lede").note()
deck.save("bonsaihub.pptx")
```

`keyline check bonsaihub.pptx --brief fixtures/briefs/drift/base.brief.toml` then passes.
The same script and inputs give byte-identical files. The Swiss specimens in
[`fixtures/packs`](fixtures/packs), in three voices, are built this way by
`fixtures/packs/src/build_specimens.py`.

## Why

AI agents can already produce `.pptx` files, and many skills tell them in prose which
"AI tells" to avoid. None of them check. In testing, OfficeCLI's own `view issues`
reported zero problems on a deck with 37–42% of its content slides left empty. The same
tool's KPI-card recipe produced exactly the look people now call AI slop.

keyline turns that prose into rules: stable IDs, fixtures, and a gate an agent has to
pass before it hands over a deck.

- [Vision](docs/vision.md)
- [Research notes](docs/research.md) (September 2026)
- [Constitution](docs/constitution.md)

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
