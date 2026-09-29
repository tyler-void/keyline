"""Build the Swiss pack's templates from its system and a voice (spec 002 §5.3, B-8.9).

    python src/keyline/packs/swiss/src/build_templates.py [OUT_DIR] [--voice NAME]

Writes swiss-<voice>-presented.pptx and swiss-<voice>-read.pptx into the pack directory
(or OUT_DIR). The voice defaults to neutral, whose templates are the committed ones (plan
Q-26). The output is byte-stable: rebuilding from the same data gives identical files.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from keyline.packs import load
from keyline.packs.templates import COMMITTED_VOICE, write_all

PACK_DIR = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("out_dir", nargs="?", type=Path)
    parser.add_argument("--voice", default=COMMITTED_VOICE)
    args = parser.parse_args()
    pack = load(PACK_DIR)
    for path in write_all(pack, pack.voice(args.voice), args.out_dir):
        print(path)
