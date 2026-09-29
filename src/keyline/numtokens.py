"""Numeric tokens (spec 002 §4.4, normative; plan Q-19 renamed it from numbers.py).

A token is a numeric core with an optional prefix (sign, currency) and suffix (%, ×, or a
magnitude letter). A token is *significant* when it has a prefix or a suffix, or at least
two digits, except that a bare 4-digit core from 1900 to 2099 is a year. `unsourced-number`
(§4.5) compares a slide's significant tokens with the tokens of its evidence entries.

Known limits (§4.4.5, amendment B-5 and audit 02 FX-8), pinned by tests; the skill's
check.md (phase B) documents them:
- units are not compared; spaces as thousands separators are not read; "24/7" gives "24";
- "27 September 2026" gives a significant "27"; "v2.0.1" gives "2.0.1"; "3 × 4" gives
  "3×"; "$-5" gives "-5";
- "B2B" gives "2B", "4K" gives "4K", "COVID-19" gives "19", "iPhone 15" gives "15";
- "5 %" with a no-break space gives a non-significant "5" (only U+0020 joins the "%");
- a source line inside a table cell is not recognised (B-12): table text is scanned whole.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Iterator

CORE = re.compile(r"\d+(?:[.,]\d+)*")
CURRENCIES = "$€£¥₫"
SIGNS = "-−+"
SPACED_SUFFIXES = "%×"  # immediately after the core, or after one space
LETTER_SUFFIXES = ("bn", "k", "K", "M", "B", "x")  # "bn" before "B"; not before a letter


def tokens(text: str) -> list[tuple[str, bool]]:
    """(token, significant) for every numeric core in `text`, in order (after NFC)."""
    t = unicodedata.normalize("NFC", text)
    out = []
    for m in CORE.finditer(t):
        start, end = m.span()
        core = m.group()
        prefix = _prefix(t, start)
        suffix = _suffix(t, end)
        digits = sum(c.isdigit() for c in core)
        year = (
            not prefix
            and not suffix
            and len(core) == 4
            and core.isdigit()
            and 1900 <= int(core) <= 2099
        )
        significant = (bool(prefix) or bool(suffix) or digits >= 2) and not year
        out.append((prefix + core + suffix, significant))
    return out


def _prefix(t: str, start: int) -> str:
    prefix, i = "", start
    if i > 0 and t[i - 1] in CURRENCIES:
        prefix, i = t[i - 1], i - 1
    # a sign counts at the start of the text or after a character that is not a letter or
    # a digit, so the hyphens in "10-20" and "Q3-2026" are not signs
    if i > 0 and t[i - 1] in SIGNS and (i == 1 or not t[i - 2].isalnum()):
        prefix = ("-" if t[i - 1] == "−" else t[i - 1]) + prefix
    return prefix


def _suffix(t: str, end: int) -> str:
    if end < len(t) and t[end] in SPACED_SUFFIXES:
        return t[end]
    if end + 1 < len(t) and t[end] == " " and t[end + 1] in SPACED_SUFFIXES:
        return t[end + 1]
    for sx in LETTER_SUFFIXES:
        after = end + len(sx)
        if t.startswith(sx, end) and not (after < len(t) and t[after].isalpha()):
            return sx
    return ""


def significant(text: str) -> list[str]:
    return [tok for tok, sig in tokens(text) if sig]


# ---------------------------------------------------------------------------------------
# what a slide shows (§4.4.1) and what an evidence entry allows (§4.4.4)


def slide_texts(slide, cfg) -> Iterator[tuple[object, str]]:
    """(shape, text) for the text in scope: the inked text of each paragraph of each shape
    except source paragraphs and sldNum/dt/ftr placeholders, and each table's text. Charts
    and notes are never in the model's paragraphs. Hidden shapes are not in the model."""
    from keyline.rules._common import inked_text, line_kind

    for shape in slide.shapes:
        if shape.ph_type in ("sldNum", "dt", "ftr"):
            continue
        for p in shape.paragraphs:
            if line_kind(p, cfg) == "source":
                continue
            text = inked_text(p)
            if text.strip():
                yield shape, text
        if shape.table_text:
            yield shape, shape.table_text


def _series_number(n: int | float) -> str:
    return f"{n:,}" if isinstance(n, int) else f"{n:,.1f}"


def entry_tokens(
    value: str | None = None,
    aliases: Iterable[str] = (),
    label: str = "",
    series: Iterable[tuple[str, int | float]] | None = None,
) -> set[str]:
    """Every token an evidence entry allows on its slide (§4.4.4)."""
    texts = [label, *aliases]
    if value is not None:
        texts.append(value)
    for category, number in series or ():
        texts.append(category)
        texts.append(_series_number(number))
    return {tok for text in texts for tok, _sig in tokens(text)}
