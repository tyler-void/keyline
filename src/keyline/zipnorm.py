"""Byte-stable OOXML packages (spec 002 §6.5).

Entries are written sorted, with `[Content_Types].xml` first, every entry dated
1980-01-01 00:00:00, with the same attributes and the same compression. The compression
is ZIP_STORED: deflate output depends on the zlib build (zlib and zlib-ng differ), so a
deflated package would be byte-stable on one machine but not across the machines that
rebuild it (the auditor's among them). Stdlib only; lint never imports this module.
"""

from __future__ import annotations

import io
import zipfile
from collections.abc import Iterable
from pathlib import Path

EPOCH = (1980, 1, 1, 0, 0, 0)
FIRST = "[Content_Types].xml"


def _order(name: str) -> tuple[int, str]:
    return (0 if name == FIRST else 1, name)


def pack_bytes(entries: Iterable[tuple[str, bytes]]) -> bytes:
    """A normalised zip of (name, data) pairs. Duplicate names are an error."""
    items = list(entries)
    names = [n for n, _ in items]
    if len(names) != len(set(names)):
        raise ValueError("duplicate zip entry names")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        for name, data in sorted(items, key=lambda item: _order(item[0])):
            info = zipfile.ZipInfo(name, date_time=EPOCH)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 0
            info.external_attr = 0
            zf.writestr(info, data)
    return buf.getvalue()


def write(path: str | Path, entries: Iterable[tuple[str, bytes]]) -> Path:
    path = Path(path)
    path.write_bytes(pack_bytes(entries))
    return path


def read_entries(data: bytes) -> list[tuple[str, bytes]]:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return [(i.filename, zf.read(i.filename)) for i in zf.infolist() if not i.is_dir()]


def normalise(path: str | Path) -> Path:
    """Rewrite an existing package in place under the rules above."""
    path = Path(path)
    return write(path, read_entries(path.read_bytes()))
