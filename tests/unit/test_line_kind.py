"""Spec 002 §3.1: source and note paragraphs."""

import pytest

from keyline.config import load
from keyline.model import Paragraph, Run
from keyline.rules._common import line_kind

CFG = load()


def para(text, ink=True):
    return Paragraph(runs=(Run(text, 1200, hidden=not ink),))


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("Source: BonsaiHub waitlist", "source"),
        ("SOURCES: two surveys", "source"),
        ("  source  : indented, spaces before the colon", "source"),
        ("Nguồn： khảo sát", "source"),  # full-width colon
        ("Note: fictional", "note"),
        ("Notes: two of them", "note"),
        ("Ghi chú: hư cấu", "note"),
        ("Source code matters", None),  # no colon after the prefix
        ("Sourced: elsewhere", None),  # the prefix must be followed by the colon
        ("Footnote: not a prefix", None),
        ("Note - dash, not colon", None),
        ("", None),
    ],
)
def test_line_kind(text, kind):
    assert line_kind(para(text), CFG) == kind


def test_nfd_input_is_normalised():
    import unicodedata

    assert line_kind(para(unicodedata.normalize("NFD", "Nguồn: x")), CFG) == "source"


def test_uninked_paragraph_is_never_a_line():
    assert line_kind(para("Source: hidden", ink=False), CFG) is None
