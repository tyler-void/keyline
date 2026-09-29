"""Build fixtures/validate/editorial-bogus.pptx (spec 002 AC-14b):

    python fixtures/validate/src/build_bogus.py [OUT_DIR]

The golden editorial.pptx with one unknown element, <p:bogus/>, injected into slide 1's
p:cSld, so that `officecli validate` reports a schema error. The golden deck itself is
never edited; every other part is copied byte for byte.
"""

from __future__ import annotations

import sys
from pathlib import Path

from keyline import zipnorm

ROOT = Path(__file__).resolve().parents[3]
GOLDEN = ROOT / "fixtures" / "golden" / "editorial.pptx"
PART = "ppt/slides/slide1.xml"


def build(out_dir: Path) -> Path:
    entries = []
    for name, data in zipnorm.read_entries(GOLDEN.read_bytes()):
        if name == PART:
            assert data.count(b"</p:cSld>") == 1
            data = data.replace(b"</p:cSld>", b"<p:bogus/></p:cSld>")
        entries.append((name, data))
    out_dir.mkdir(parents=True, exist_ok=True)
    return zipnorm.write(out_dir / "editorial-bogus.pptx", entries)


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "fixtures" / "validate"
    print(build(out))
