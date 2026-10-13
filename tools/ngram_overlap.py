"""Count the word sequences two folders share (spec 002 AC-23; plan Q-56 as ruled):

    python tools/ngram_overlap.py A B [--n 8] [--show 20]

Every text file under A is compared with every text file under B. A sequence is `n`
consecutive words (8 by default), lower-cased, with punctuation dropped. The tool prints
how many distinct sequences occur on both sides, and the first `--show` of them with the
files they come from.

It is a generic tool: it holds no third-party text and makes no network call. Point it
at two folders you already have, for example this repository's `skill/` and a clone of
another skill repository. Exit 0 when nothing is shared, 1 when something is, 2 on a
usage error. Dev only; stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

WORD = re.compile(r"[^\W_]+(?:['’][^\W_]+)*")
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv"}


def words(text: str) -> list[str]:
    return WORD.findall(text.lower())


def texts(folder: Path):
    """(relative path, text) for every file under `folder` that reads as UTF-8 text."""
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or SKIP_DIRS & set(path.relative_to(folder).parts):
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if b"\0" in data[:4096]:
            continue
        try:
            yield path.relative_to(folder).as_posix(), data.decode("utf-8")
        except UnicodeDecodeError:
            continue


def sequences(folder: Path, n: int) -> dict[tuple[str, ...], str]:
    """Every n-word sequence under `folder`, with the first file it occurs in."""
    found: dict[tuple[str, ...], str] = {}
    for name, text in texts(folder):
        ws = words(text)
        for i in range(len(ws) - n + 1):
            found.setdefault(tuple(ws[i : i + n]), name)
    return found


def shared(a: Path, b: Path, n: int = 8) -> list[tuple[str, str, str]]:
    """(the sequence, its file under a, its file under b), in the order b is read."""
    left = sequences(a, n)
    out, seen = [], set()
    for name, text in texts(b):
        ws = words(text)
        for i in range(len(ws) - n + 1):
            key = tuple(ws[i : i + n])
            if key in left and key not in seen:
                seen.add(key)
                out.append((" ".join(key), left[key], name))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="count the word sequences two folders share")
    parser.add_argument("a", type=Path)
    parser.add_argument("b", type=Path)
    parser.add_argument("--n", type=int, default=8, help="words per sequence (default 8)")
    parser.add_argument("--show", type=int, default=20, help="sequences to print (default 20)")
    args = parser.parse_args(argv)
    for folder in (args.a, args.b):
        if not folder.is_dir():
            sys.stderr.write(f"ngram_overlap: not a folder: {folder}\n")
            return 2
    if args.n < 1:
        sys.stderr.write("ngram_overlap: --n must be at least 1\n")
        return 2
    found = shared(args.a, args.b, args.n)
    print(f"{len(found)} shared sequences of {args.n} words between {args.a} and {args.b}")
    for text, left, right in found[: args.show]:
        print(f"  {left} | {right}: {text}")
    if len(found) > args.show:
        print(f"  … and {len(found) - args.show} more")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
