"""Command-line entry point. Kept thin: all logic lives in importable modules.

Contract (spec §3): JSON on stdout (with --json), human-readable lines on stderr,
exit 0 clean / 2 findings at warning or error / 1 could not scan.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from keyline import __version__
from keyline.config import MODES
from keyline.findings import EXIT_SCAN_FAILED, to_human, to_json
from keyline.ooxml.package import ScanError


def _err(text: str) -> None:
    sys.stderr.write(text)
    sys.stderr.flush()


def _out(text: str) -> None:
    sys.stdout.write(text)
    sys.stdout.flush()


def _lint(path: str, mode: str):
    from keyline.lint import lint_path

    if not Path(path).is_file():
        raise ScanError(f"no such file: {path}")
    return lint_path(path, mode)


def cmd_lint(args: argparse.Namespace) -> int:
    try:
        result = _lint(args.deck, args.mode)
    except ScanError as exc:
        _err(f"keyline: cannot scan {args.deck}: {exc}\n")
        return EXIT_SCAN_FAILED
    if args.json:
        _out(to_json(result.findings))
    _err(to_human(result.findings))
    return result.exit_code


def cmd_rules(args: argparse.Namespace) -> int:
    from keyline.registry import all_rules
    from keyline.rules import load_all

    load_all()
    specs = all_rules()
    if args.json:
        _out(json.dumps([s.describe() for s in specs], ensure_ascii=False, indent=2) + "\n")
        return 0
    width = max(len(s.id) for s in specs)
    lines = []
    for s in specs:
        note = f" [{s.severity_notes}]" if s.severity_notes else ""
        lines.append(
            f"{s.id:<{width}}  {s.category:<7} {s.severity:<8} {s.basis:<9} {s.summary}{note}"
        )
    _out("\n".join(lines) + "\n")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    from keyline.render import RenderError, render

    try:
        result = render(args.deck, args.out)
    except RenderError as exc:
        _err(f"keyline: render failed: {exc}\n")
        return EXIT_SCAN_FAILED
    for p in result.slides:
        _out(f"{p}\n")
    _out(f"{result.contact}\n")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    from keyline.render import RenderError, render

    try:
        result = _lint(args.deck, args.mode)
    except ScanError as exc:
        _err(f"keyline: cannot scan {args.deck}: {exc}\n")
        return EXIT_SCAN_FAILED
    if args.json:
        _out(to_json(result.findings))
    _err(to_human(result.findings))
    out_dir = args.out or str(Path(args.deck).with_suffix("")) + "-render"
    try:
        rendered = render(args.deck, out_dir)
    except RenderError as exc:
        _err(f"render: skipped ({exc})\n")
        return EXIT_SCAN_FAILED if args.require_render else result.exit_code
    paths = [*rendered.slides, rendered.contact]
    listing = "".join(f"{p}\n" for p in paths)
    if args.json:
        _err(listing)
    else:
        _out(listing)
    return result.exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="keyline",
        description="Deterministic design checks for .pptx decks.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("lint", help="run the rule registry on a .pptx")
    p.add_argument("deck")
    p.add_argument("--mode", choices=MODES, default="presented")
    p.add_argument("--json", action="store_true", help="write findings as JSON to stdout")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("rules", help="list the rule registry")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_rules)

    p = sub.add_parser("render", help="PNG per slide and a contact sheet (needs OfficeCLI)")
    p.add_argument("deck")
    p.add_argument("-o", "--out", required=True, help="output directory")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("check", help="lint, then a best-effort render")
    p.add_argument("deck")
    p.add_argument("--mode", choices=MODES, default="presented")
    p.add_argument("-o", "--out", help="render directory (default: <deck>-render)")
    p.add_argument("--json", action="store_true")
    p.add_argument(
        "--require-render", action="store_true", help="exit 1 when the render step fails"
    )
    p.set_defaults(func=cmd_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help(sys.stderr)
        return 1
    return args.func(args)
