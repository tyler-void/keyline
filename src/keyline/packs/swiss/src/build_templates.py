"""Build the Swiss pack's templates from its pack.toml (spec 002 §5.1, §5.3).

    python src/keyline/packs/swiss/src/build_templates.py [OUT_DIR]

Writes swiss-presented.pptx and swiss-read.pptx into the pack directory (or OUT_DIR).
The output is byte-stable: rebuilding from the same pack.toml gives identical files.
"""

from __future__ import annotations

import sys
from pathlib import Path

from keyline.packs import load
from keyline.packs.templates import write_all

PACK_DIR = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    for path in write_all(load(PACK_DIR), out):
        print(path)
