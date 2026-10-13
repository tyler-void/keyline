#!/usr/bin/env python3
"""keyline, as the skill runs it (spec 002 §8.1).

    python scripts/kl.py doctor                    # any keyline command and its flags
    python scripts/kl.py run SCRIPT.py [ARGS]      # a build script, with keyline importable

The script finds the skill's folder through its own location. In the packaged skill that
folder has a `lib/` with the keyline package, which goes first on the import path; in
development there is no `lib/`, and the installed package is used. `run` executes the
script as `__main__`, with `sys.argv` set to the script and its arguments, and with the
script's own folder on the import path, as `python SCRIPT.py` would.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
LIB = SKILL / "lib"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if LIB.is_dir():
        sys.path.insert(0, str(LIB))
    if args[:1] == ["run"]:
        if len(args) < 2:
            sys.stderr.write("kl.py: run needs a script: kl.py run SCRIPT.py [ARGS]\n")
            return 1
        script = Path(args[1])
        if not script.is_file():
            sys.stderr.write(f"kl.py: no such script: {args[1]}\n")
            return 1
        sys.argv = args[1:]
        # after lib/, as python puts a script's folder first
        sys.path.insert(1 if LIB.is_dir() else 0, str(script.resolve().parent))
        runpy.run_path(str(script), run_name="__main__")
        return 0
    try:
        from keyline.cli import main as keyline
    except ImportError as exc:
        sys.stderr.write(
            f"kl.py: the keyline package cannot be imported ({exc}). The packaged skill "
            "carries it in lib/; in development, install it with pip.\n"
        )
        return 1
    return keyline(args)


if __name__ == "__main__":
    sys.exit(main())
