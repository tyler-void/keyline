# keyline

Deterministic design checks and a render loop for AI-generated PowerPoint decks.

**Status: pre-alpha. Nothing here is usable yet.** Work in progress:
[`specs/001-lint-core`](specs/001-lint-core/spec.md).

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
