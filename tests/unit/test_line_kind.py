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
        ("Source\u00a0: une enquête", "source"),  # French: no-break space (B-12)
        ("Source\u202f: une enquête", "source"),  # narrow no-break space
        ("Note\u3000\t: ideographic space and a tab", "note"),
        ("Source\u200b: a zero-width space is not a space separator", None),
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


def test_classification_reads_the_inked_text_only():
    """Audit 02 FX-6 (B-12): an invisible "Source: " run must not hide a visible number
    from the numeric scan, and a visible source line after invisible text still counts."""
    from keyline.model import Shape, Slide
    from keyline.numtokens import slide_texts

    hidden_prefix = Paragraph(runs=(Run("Source: ", 1200, hidden=True), Run("12,400 trees", 1200)))
    assert line_kind(hidden_prefix, CFG) is None
    shape = Shape(2, "body", "sp", 2, paragraphs=[hidden_prefix])
    slide = Slide(1, None, "solid:#FFFFFF", shapes=[shape])
    assert [text for _shape, text in slide_texts(slide, CFG)] == ["12,400 trees"]
    visible = Paragraph(runs=(Run("ghost ", 1200, hidden=True), Run("Source: waitlist", 1200)))
    assert line_kind(visible, CFG) == "source"
