"""Slide roles (spec 002 §2, D-016): a pen-built slide carries its role in its layout name,
`keyline:<role>` with an optional `:<variant>`. Any other name means no role."""

from __future__ import annotations

import re

ROLES = ("cover", "section", "statement", "evidence", "quote", "close")
_NAME = re.compile(r"^keyline:(cover|section|statement|evidence|quote|close)(?::([a-z0-9-]+))?$")


def parse(layout_name: str | None) -> tuple[str | None, str | None]:
    """(role, variant) from a layout name; (None, None) unless the whole name matches."""
    if layout_name is None:
        return None, None
    m = _NAME.fullmatch(layout_name)
    if m is None:
        return None, None
    return m.group(1), m.group(2)
