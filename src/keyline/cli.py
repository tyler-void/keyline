"""Command-line entry point. Kept thin: all logic lives in importable modules.

Contract (spec §3): JSON on stdout (with --json), human-readable lines on stderr,
exit 0 clean / 2 findings at warning or error / 1 could not scan.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
import traceback
from pathlib import Path

from keyline import __version__, progress
from keyline.config import MODES
from keyline.findings import EXIT_SCAN_FAILED, to_human, to_json
from keyline.ooxml.package import ScanError


def _err(text: str) -> None:
    sys.stderr.write(text)
    sys.stderr.flush()


def _out(text: str) -> None:
    sys.stdout.write(text)
    sys.stdout.flush()


def _out_json(text: str) -> None:
    """A-16: JSON is UTF-8 bytes whatever the locale (a cp1252 pipe cannot hold "タイトル")."""
    sys.stdout.flush()
    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.buffer.flush()


def _tolerant_streams() -> None:
    """Human-readable text never crashes on an unencodable shape name."""
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):
            stream.reconfigure(errors="backslashreplace")


class UsageError(ValueError):
    """A flag combination or a pack/voice that cannot be used: exit 1, one line."""


def _context(args: argparse.Namespace):
    """The pack (system) and voice from --pack and --voice (spec 002 §3.5, B-8.8)."""
    from keyline.context import EMPTY, LintContext
    from keyline.packs import PackError, resolve

    if args.pack is None:
        if args.voice is not None:
            raise UsageError("--voice needs a pack (--pack or --brief)")
        return EMPTY
    if args.voice is None:
        raise UsageError("pack rules need a voice (--voice or --brief)")
    try:
        pack = resolve(args.pack, base=Path.cwd())
        voice = pack.voice(args.voice, base=Path.cwd())
    except PackError as exc:
        raise UsageError(str(exc)) from exc
    return LintContext(pack=pack, voice=voice)


def _voice_notices(ctx, mode: str) -> None:
    if ctx.voice is None:
        return
    from keyline import config
    from keyline.packs.voices import notices

    for line in notices(ctx.pack, ctx.voice, config.load(mode)):
        _err(f"{line}\n")


def _lint(path: str, mode: str, ctx=None):
    from keyline.context import EMPTY
    from keyline.lint import lint_path

    if not Path(path).is_file():
        raise ScanError(f"no such file: {path}")
    return lint_path(path, mode, EMPTY if ctx is None else ctx)


def _lint_command(args: argparse.Namespace):
    """Resolve the context, then lint; returns (result, None) or (None, exit code)."""
    try:
        ctx = _context(args)
    except UsageError as exc:
        _err(f"keyline: {exc}\n")
        return None, EXIT_SCAN_FAILED
    _voice_notices(ctx, args.mode)
    try:
        return _lint(args.deck, args.mode, ctx), None
    except ScanError as exc:
        _err(f"keyline: cannot scan {args.deck}: {exc}\n")
        return None, EXIT_SCAN_FAILED


def cmd_lint(args: argparse.Namespace) -> int:
    result, failed = _lint_command(args)
    if result is None:
        return failed
    if args.json:
        _out_json(to_json(result.findings))
    _err(to_human(result.findings))
    return result.exit_code


def cmd_rules(args: argparse.Namespace) -> int:
    from keyline.registry import all_rules
    from keyline.rules import load_all

    load_all()
    specs = all_rules()
    if args.json:
        _out_json(json.dumps([s.describe() for s in specs], ensure_ascii=False, indent=2) + "\n")
        return 0
    width = max(len(s.id) for s in specs)
    lines = []
    for s in specs:
        note = f" [{s.severity_notes}]" if s.severity_notes else ""
        lines.append(
            f"{s.id:<{width}}  {s.category:<7} {s.severity:<8} {s.basis:<9} "
            f"{s.requires:<9} {s.summary}{note}"
        )
    _out("\n".join(lines) + "\n")
    return 0


def cmd_packs(args: argparse.Namespace) -> int:
    from keyline.packs import bundled, resolve

    packs = [resolve(name) for name in bundled()]
    rows = []
    for p in packs:
        voices = [p.voice(v) for v in p.voices()]
        rows.append(
            {
                "name": p.name,
                "version": p.version,
                "modes": list(p.modes),
                "voices": [{"name": v.name, "display": v.display, "text": v.text} for v in voices],
            }
        )
    if args.json:
        _out_json(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    else:
        _out(
            "".join(
                f"{r['name']}  {r['version']}  {', '.join(r['modes'])}  voices: "
                f"{', '.join(v['name'] for v in r['voices'])}\n"
                for r in rows
            )
        )
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

    result, failed = _lint_command(args)
    if result is None:
        return failed
    if args.json:
        _out_json(to_json(result.findings))
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


def _pack_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument("--pack", metavar="NAME|DIR", help="a bundled pack name or a pack directory")
    p.add_argument(
        "--voice", metavar="NAME|FILE", help="a voice of the pack, or a voice file (.toml)"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="keyline",
        description="Deterministic design checks for .pptx decks.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--traceback", action="store_true", help="print the full trace on an internal error"
    )
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("lint", help="run the rule registry on a .pptx", parents=[common])
    p.add_argument("deck")
    p.add_argument("--mode", choices=MODES, default="presented")
    _pack_arguments(p)
    p.add_argument("--json", action="store_true", help="write findings as JSON to stdout")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("rules", help="list the rule registry", parents=[common])
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_rules)

    p = sub.add_parser("packs", help="list the style packs keyline ships", parents=[common])
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_packs)

    p = sub.add_parser(
        "render", help="PNG per slide and a contact sheet (needs OfficeCLI)", parents=[common]
    )
    p.add_argument("deck")
    p.add_argument("-o", "--out", required=True, help="output directory")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("check", help="lint, then a best-effort render", parents=[common])
    p.add_argument("deck")
    p.add_argument("--mode", choices=MODES, default="presented")
    _pack_arguments(p)
    p.add_argument("-o", "--out", help="render directory (default: <deck>-render)")
    p.add_argument("--json", action="store_true")
    p.add_argument(
        "--require-render", action="store_true", help="exit 1 when the render step fails"
    )
    p.set_defaults(func=cmd_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    _tolerant_streams()
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help(sys.stderr)
        return 1
    try:
        return args.func(args)
    except Exception as exc:  # A-17: never a bare traceback
        if args.traceback:
            traceback.print_exc()
        _err(
            f"keyline: internal error while reading {progress.reading.get()}: "
            f"{type(exc).__name__}; rerun with --traceback and report it\n"
        )
        return EXIT_SCAN_FAILED
