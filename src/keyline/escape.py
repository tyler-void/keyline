"""One error, one line (amendment B-20): user text in a message is escaped."""

from __future__ import annotations


def esc(value: object) -> str:
    """Printable characters as they are; anything else (line breaks, controls, format
    characters such as U+200B) as its Python escape, so `\\n` prints as the two characters
    backslash and n. Idempotent: escaping escaped text changes nothing."""
    return "".join(c if c.isprintable() else repr(c)[1:-1] for c in str(value))


def visible(text: str) -> bool:
    """At least one character outside Unicode categories Zs, Cc and Cf (B-20): a reason of
    only spaces, controls or zero-width characters is empty."""
    import unicodedata

    return any(unicodedata.category(c) not in ("Zs", "Cc", "Cf") for c in text)


def schema_is(value: object, expected: int = 1) -> bool:
    """`schema` must be the integer itself: TOML's true and 1.0 compare equal to 1 in
    Python, and neither is accepted (B-20)."""
    return type(value) is int and value == expected
