"""The text the estimator measures and the writer writes (amendment B-22, items 1–3).

One normalization, applied before both, so the pen writes exactly the text it estimated:
- NFC;
- each run of space separators (Unicode category Zs, except the word joiners U+00A0,
  U+202F and U+2007) becomes one U+0020;
- no leading or trailing U+0020.

The pen refuses some characters outright, naming the code point (`refused`):
- controls (category Cc, which includes tab and every line break but U+2028/U+2029),
  except `\\n` in a text that has paragraphs (`text()` and `notes()`);
- B-17's line-break set, U+2028 and U+2029 included;
- the noncharacters U+FFFE and U+FFFF, and lone surrogates;
- the invisible break controls U+00AD, U+200B, U+2060 and U+FEFF.

The word joiners stay: the estimator treats a joined run as one word.
"""

from __future__ import annotations

import re
import unicodedata

JOINERS = "\xa0\u202f\u2007"  # no-break space, narrow no-break space, figure space
# Zs without the joiners: U+0020, U+1680, U+2000–U+200A (but U+2007), U+205F, U+3000
SPACES = "\u0020\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2008\u2009\u200a\u205f\u3000"
LINE_BREAKS = "\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029"  # B-17: what str.splitlines() breaks on
INVISIBLE = "\xad\u200b\u2060\ufeff"  # soft hyphen, zero-width space, word joiner, BOM
NONCHARACTERS = "\ufffe\uffff"
# B-22 item 4 (UAX #14, LB13), with B-25 item 5's fullwidth closers: no line break before
# these, even after a space
NO_BREAK_BEFORE = ")]},.:;!?/%\u2030\u00bb\u201d\u2019"  # ‰ » ” ’
FULLWIDTH_CLOSERS = "\uff01\uff1f\uff0c\u3002\u300d\uff09"  # ！ ？ ， 。 」 ）
NO_BREAK_BEFORE += FULLWIDTH_CLOSERS

INVERTED = "\xa1\xbf"  # inverted exclamation and question marks: class OP, category Po

_SPACE_RUN = re.compile(f"[{SPACES}]+")


def code_point(ch: str) -> str:
    """`U+0009`, with the character's Unicode name when it has one."""
    name = unicodedata.name(ch, "")
    return f"U+{ord(ch):04X}" + (f" ({name})" if name else "")


def refused(text: str, paragraphs: bool = False) -> str | None:
    """The first character of `text` the pen refuses (B-22 item 3; B-17's line breaks in
    a one-line text), or None. With `paragraphs`, `\\n` is allowed: it separates them."""
    for ch in text:
        if ch == "\n" and paragraphs:
            continue
        cp = ord(ch)
        if (
            unicodedata.category(ch) == "Cc"
            or ch in LINE_BREAKS
            or ch in INVISIBLE
            or ch in NONCHARACTERS
            or 0xD800 <= cp <= 0xDFFF
        ):
            return ch
    return None


# B-25 item 1: the measured set is these blocks, minus what B-22 refuses; the fit's
# guarantees (§6.4, AC-13(b), B-24) cover text inside it
MEASURED_BLOCKS = (
    (0x0000, 0x007F),  # Basic Latin, ASCII digits included
    (0x0080, 0x00FF),  # Latin-1 Supplement
    (0x0100, 0x017F),  # Latin Extended-A
    (0x0180, 0x024F),  # Latin Extended-B
    (0x1E00, 0x1EFF),  # Latin Extended Additional, Vietnamese included
    (0x2000, 0x206F),  # General Punctuation
    (0x20A0, 0x20CF),  # Currency Symbols
)


def measured(ch: str) -> bool:
    """Whether a character is in B-25's measured set (an assigned character of its blocks
    that B-22 does not refuse)."""
    cp = ord(ch)
    return (
        any(a <= cp <= b for a, b in MEASURED_BLOCKS)
        and refused(ch) is None
        and unicodedata.category(ch) != "Cn"
    )


MEASURED = "".join(chr(c) for a, b in MEASURED_BLOCKS for c in range(a, b + 1) if measured(chr(c)))


def inked(ch: str) -> bool:
    """A character LibreOffice draws: not a space, separator or format control."""
    return unicodedata.category(ch) not in ("Zs", "Zl", "Zp", "Cf", "Cc")


def normalize(text: str) -> str:
    """B-22 item 1: NFC, space runs to one U+0020, no leading or trailing space."""
    return _SPACE_RUN.sub(" ", unicodedata.normalize("NFC", text)).strip(" ")


def opens(ch: str) -> bool:
    """B-25 item 5 (UAX #14, LB14): an opening punctuation mark (class OP: category Ps,
    and the inverted ! and ?), after which no line breaks, even across a space."""
    return unicodedata.category(ch) == "Ps" or ch in INVERTED


def break_units(text: str) -> list[str]:
    """The normalized text as the pieces a line may break between: split at U+0020, with
    a piece that starts with a NO_BREAK_BEFORE character kept with the one before it
    (B-22 item 4), and a piece that ends in an opening punctuation mark kept with the one
    after it (B-25 item 5)."""
    units: list[str] = []
    for word in normalize(text).split(" "):
        if units and (word[:1] in NO_BREAK_BEFORE or opens(units[-1][-1:])):
            units[-1] = f"{units[-1]} {word}"
        else:
            units.append(word)
    return units


def paragraphs(text: str) -> list[str]:
    """A `text()` or `notes()` string as its normalized paragraphs: split at `\\n`, each
    normalized, the empty ones dropped."""
    return [p for p in (normalize(part) for part in text.split("\n")) if p]
