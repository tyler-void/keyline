# keyline

Deterministic design checks and a render loop for AI-generated PowerPoint decks.

**Status: pre-alpha.** Thresholds are uncalibrated, rule IDs may still change before
0.1.0 is released, and nothing is published to PyPI. Work in progress:
[`specs/001-lint-core`](specs/001-lint-core/spec.md).

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
| `keyline rules [--json]` | Lists every rule with its category, severity, basis and rationale |
| `keyline render deck.pptx -o DIR` | One PNG per slide plus `contact.png`, via [OfficeCLI](https://github.com/iOfficeAI/OfficeCLI) |
| `keyline check deck.pptx [--mode] [-o DIR]` | Lint, then a best-effort render. Exits with lint's code |

`keyline lint` needs only `lxml` and `Pillow`: no network, no model calls, no OfficeCLI.
Rendering needs `npm install -g @officecli/officecli`. JSON is always UTF-8, whatever the
terminal's encoding. An internal error prints one line and exits 1; add `--traceback`
to any command to see the full trace.

**Known limitation (L-002):** OfficeCLI screenshots fall back to a sans-serif font for
any font that isn't installed, so renders cannot verify typography yet.

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
