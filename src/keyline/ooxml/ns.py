"""Namespaces and relationship types."""

from __future__ import annotations

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
    "ct": "http://schemas.openxmlformats.org/package/2006/content-types",
}

_RT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
RT_OFFICE_DOCUMENT = _RT + "officeDocument"
RT_SLIDE = _RT + "slide"
RT_SLIDE_LAYOUT = _RT + "slideLayout"
RT_SLIDE_MASTER = _RT + "slideMaster"
RT_THEME = _RT + "theme"
RT_NOTES_SLIDE = _RT + "notesSlide"

# Strict OOXML uses a different namespace for relationship types; accept both spellings.
_RT_STRICT = "http://purl.oclc.org/ooxml/officeDocument/relationships/"

PRESENTATION_CONTENT_TYPES = frozenset(
    {
        "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml",
        "application/vnd.ms-powerpoint.presentation.macroEnabled.main+xml",
        "application/vnd.openxmlformats-officedocument.presentationml.slideshow.main+xml",
        "application/vnd.ms-powerpoint.slideshow.macroEnabled.main+xml",
        "application/vnd.openxmlformats-officedocument.presentationml.template.main+xml",
        "application/vnd.ms-powerpoint.template.macroEnabled.main+xml",
    }
)


def rel_type_matches(actual: str, expected: str) -> bool:
    if actual == expected:
        return True
    return expected.startswith(_RT) and actual == _RT_STRICT + expected[len(_RT) :]


def q(name: str) -> str:
    """'a:off' -> '{http://...drawingml...}off'."""
    prefix, local = name.split(":")
    return f"{{{NS[prefix]}}}{local}"
