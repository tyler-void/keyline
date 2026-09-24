"""Build every rule fixture deck: python fixtures/rules/src/build_rules.py [OUT_DIR]

Each builder makes one deck. Expectations for each deck live in fixtures/rules/expect.toml.
Dev dependency: python-pptx (pyproject extra `dev`).
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


DECKS: dict[str, Callable[[], object]] = {}


def deck(name: str):
    def wrap(fn):
        DECKS[name] = fn
        return fn

    return wrap


def build(out_dir: Path, names: list[str] | None = None) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name in names or sorted(DECKS):
        path = out_dir / f"{name}.pptx"
        DECKS[name]().save(path)
        written.append(path)
    return written


def main(argv: list[str]) -> int:
    out = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parents[1]
    for p in build(out):
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
