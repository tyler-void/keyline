"""Build the skill package (spec 002 §9; task T-43; AC-19):

    python tools/build_skill.py [OUT]      # default: dist/keyline.zip

The zip root holds exactly one folder, `keyline/`:
- `SKILL.md`, `references/` and `scripts/`, from `skill/keyline/`;
- `lib/keyline/`: the package from `src/keyline`, with its packs and fit tables, without
  caches or tests;
- `LICENSE` and `NOTICE`.
It is written through `keyline.zipnorm` (§6.5): sorted entries, fixed dates, stored, so
two builds are byte-identical. `dist/` is not committed. Dev only.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from keyline import zipnorm  # noqa: E402

NAME = "keyline"
SKILL = ROOT / "skill" / NAME
PACKAGE = ROOT / "src" / NAME
OUT = ROOT / "dist" / f"{NAME}.zip"
SKIP_DIRS = {"__pycache__", "tests"}
SKIP_SUFFIXES = {".pyc", ".pyo"}


def _files(folder: Path) -> list[Path]:
    return [
        p
        for p in sorted(folder.rglob("*"))
        if p.is_file()
        and not SKIP_DIRS & set(p.relative_to(folder).parts)
        and p.suffix not in SKIP_SUFFIXES
    ]


def entries() -> list[tuple[str, bytes]]:
    """(name in the zip, bytes) for every file of the package."""
    found = [(f"{NAME}/{p.relative_to(SKILL).as_posix()}", p) for p in _files(SKILL)]
    found += [
        (f"{NAME}/lib/{NAME}/{p.relative_to(PACKAGE).as_posix()}", p) for p in _files(PACKAGE)
    ]
    found += [(f"{NAME}/{name}", ROOT / name) for name in ("LICENSE", "NOTICE")]
    return [(name, path.read_bytes()) for name, path in found]


def build(out: Path = OUT) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    return zipnorm.write(out, entries())


if __name__ == "__main__":
    path = build(Path(sys.argv[1]) if len(sys.argv) > 1 else OUT)
    print(f"{path} ({path.stat().st_size / 1024:.0f} KiB)")
