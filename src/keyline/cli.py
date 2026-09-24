"""Command-line entry point. Kept thin: all logic lives in importable modules."""

from __future__ import annotations

import argparse

from keyline import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="keyline",
        description="Deterministic design checks for .pptx decks.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0
