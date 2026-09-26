"""Tiny helpers for in-memory OOXML snippets in adapter tests."""

from lxml import etree

A_URI = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_URI = "http://schemas.openxmlformats.org/presentationml/2006/main"
NSDECL = f'xmlns:a="{A_URI}" xmlns:p="{P_URI}"'


def el(xml: str) -> etree._Element:
    """Parse one element written with a:/p: prefixes and no namespace declarations."""
    return etree.fromstring(f"<w {NSDECL}>{xml}</w>")[0]


def lst(level_xml: str, tag: str = "a:lstStyle") -> etree._Element:
    return el(f"<{tag}>{level_xml}</{tag}>")
