"""Shared helpers for the stress builders copied from audit 02's stress-corpus/src/.

The builders were adapted only where they must run from this repo: output paths, the
test photo, and the identity in docProps (AC-12: author and lastModifiedBy are "Tyler").

    python _stress.py retag FILE.pptx   # set creator/lastModifiedBy on any built deck
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE.parent  # fixtures/foreign/stress
IDENTITY = "Tyler"


def out_path(name: str, argv_index: int = 1) -> str:
    """sys.argv[argv_index] if given, else fixtures/foreign/stress/<name>."""
    if len(sys.argv) > argv_index:
        return sys.argv[argv_index]
    return str(OUT_DIR / name)


def tyler(prs) -> None:
    """python-pptx: the default template's core.xml carries a third-party name."""
    cp = prs.core_properties
    cp.author = IDENTITY
    cp.last_modified_by = IDENTITY


def photo() -> str:
    """The 800x500 test photo from stress-corpus/src/make_images.py, in a temp dir."""
    from PIL import Image, ImageDraw

    path = Path(tempfile.gettempdir()) / "keyline-stress" / "photo.png"  # descr="photo.png"
    path.parent.mkdir(exist_ok=True)
    if not path.exists():
        im = Image.new("RGB", (800, 500), (30, 90, 160))
        d = ImageDraw.Draw(im)
        for i in range(0, 800, 40):
            d.line([(i, 0), (800 - i, 500)], fill=(240, 200, 60), width=4)
        im.save(path)
    return str(path)


def retag(path: str) -> None:
    """Rewrite docProps/core.xml so dc:creator and cp:lastModifiedBy are the identity.
    For decks written by tools other than python-pptx (LibreOffice, pptxgenjs)."""
    src = zipfile.ZipFile(path)
    items = [(info, src.read(info.filename)) for info in src.infolist()]
    src.close()
    fd, tmp = tempfile.mkstemp(suffix=".pptx", dir=os.path.dirname(os.path.abspath(path)))
    os.close(fd)
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as out:
        for info, data in items:
            if info.filename == "docProps/core.xml":
                xml = data.decode("utf-8")
                for tag in ("dc:creator", "cp:lastModifiedBy"):
                    if re.search(rf"<{tag}\b", xml):
                        xml = re.sub(
                            rf"<{tag}\s*/>|<{tag}>.*?</{tag}>",
                            f"<{tag}>{IDENTITY}</{tag}>",
                            xml,
                            flags=re.S,
                        )
                    else:
                        xml = xml.replace(
                            "</cp:coreProperties>", f"<{tag}>{IDENTITY}</{tag}></cp:coreProperties>"
                        )
                data = xml.encode("utf-8")
            out.writestr(info, data)
    os.replace(tmp, path)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "retag":
        retag(sys.argv[2])
        print("retagged", sys.argv[2])
    else:
        sys.exit("usage: python _stress.py retag FILE.pptx")
