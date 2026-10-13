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

import json
import re
import unicodedata
from pathlib import Path

JOINERS = "\xa0\u202f\u2007"  # no-break space, narrow no-break space, figure space
# Zs without the joiners: U+0020, U+1680, U+2000–U+200A (but U+2007), U+205F, U+3000
SPACES = "\u0020\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2008\u2009\u200a\u205f\u3000"
LINE_BREAKS = "\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029"  # B-17: what str.splitlines() breaks on
INVISIBLE = "\xad\u200b\u2060\ufeff"  # soft hyphen, zero-width space, word joiner, BOM
NONCHARACTERS = "\ufffe\uffff"
# B-27 item 3: the characters LibreOffice will not break before, after a space, and the
# ones it will not break after, before a space, are measured (tools/measure_lo.py, every
# non-letter character of the measured set) and stored as the union over the versions
# measured (tables/breaks.json, written by tools/gen_measured.py). They replace the lists
# of B-22 item 4 and B-25 item 5.
_BREAKS = json.loads(
    (Path(__file__).resolve().parent / "tables" / "breaks.json").read_text(encoding="utf-8")
)
# B-25 item 5's fullwidth closers are outside the measured set, and stay listed
FULLWIDTH_CLOSERS = "\uff01\uff1f\uff0c\u3002\u300d\uff09"  # ！ ？ ， 。 」 ）
NO_BREAK_BEFORE = "".join(map(chr, _BREAKS["no_break_before"])) + FULLWIDTH_CLOSERS
NO_BREAK_AFTER = "".join(map(chr, _BREAKS["no_break_after"]))

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
# guarantees (§6.4, AC-13(b), B-24) cover text inside it. B-27 item 1 adds U+2212 alone:
# §4.4 accepts it as a sign, and negative figures need it (Q-53)
MEASURED_BLOCKS = (
    (0x0000, 0x007F),  # Basic Latin, ASCII digits included
    (0x0080, 0x00FF),  # Latin-1 Supplement
    (0x0100, 0x017F),  # Latin Extended-A
    (0x0180, 0x024F),  # Latin Extended-B
    (0x1E00, 0x1EFF),  # Latin Extended Additional, Vietnamese included
    (0x2000, 0x206F),  # General Punctuation
    (0x20A0, 0x20CF),  # Currency Symbols
    (0x2212, 0x2212),  # MINUS SIGN, alone of Mathematical Operators (B-27 item 1)
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


# Default_Ignorable_Code_Point (Unicode DerivedCoreProperties): nothing is drawn for
# these, and a shaper looks past them (format controls, variation selectors, the grapheme
# joiner, Hangul fillers). Some are category L or M.
DEFAULT_IGNORABLE = (
    (0x00AD, 0x00AD), (0x034F, 0x034F), (0x061C, 0x061C), (0x115F, 0x1160), (0x17B4, 0x17B5),
    (0x180B, 0x180F), (0x200B, 0x200F), (0x202A, 0x202E), (0x2060, 0x206F), (0x3164, 0x3164),
    (0xFE00, 0xFE0F), (0xFEFF, 0xFEFF), (0xFFA0, 0xFFA0), (0xFFF0, 0xFFF8), (0x1BCA0, 0x1BCA3),
    (0x1D173, 0x1D17A), (0xE0000, 0xE0FFF),
)  # fmt: skip


def ignorable(ch: str) -> bool:
    """Whether a character is a default-ignorable code point."""
    c = ord(ch)
    return any(a <= c <= b for a, b in DEFAULT_IGNORABLE)


def visible(ch: str) -> bool:
    """Audit 06 (with FX-30): a letter, mark, number, punctuation mark or symbol that is
    drawn; text made only of spaces, format controls and ignorable marks shows nothing."""
    return unicodedata.category(ch)[0] in "LMNPS" and not ignorable(ch)


def drawn(ch: str) -> bool:
    """A character that puts ink on the line: `inked`, and not default-ignorable."""
    return inked(ch) and not ignorable(ch)


def normalize(text: str) -> str:
    """B-22 item 1: NFC, space runs to one U+0020, no leading or trailing space."""
    return _SPACE_RUN.sub(" ", unicodedata.normalize("NFC", text)).strip(" ")


def opens(ch: str) -> bool:
    """Whether no line breaks after this character, even across a space: a measured
    character of NO_BREAK_AFTER (B-27 item 3), or, outside the measured set, an opening
    punctuation mark (category Ps; B-25 item 5, UAX #14 LB14)."""
    if ch == "":
        return False
    return ch in NO_BREAK_AFTER or (not measured(ch) and unicodedata.category(ch) == "Ps")


def break_units(text: str) -> list[str]:
    """The normalized text as the pieces a line may break between: split at U+0020, with
    a piece that starts with a NO_BREAK_BEFORE character kept with the one before it, and
    a piece that ends in a character that `opens` kept with the one after it (B-22 item 4
    and B-25 item 5, as measured per B-27 item 3)."""
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
