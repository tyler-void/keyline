"""Byte-identical saves (spec 002 §6.5, L-013): the outer zip is normalised by zipnorm,
and each embedded chart workbook (XlsxWriter records its build time in docProps/core.xml)
gets the template's `created` date and a normalised inner zip."""

from __future__ import annotations

from lxml import etree

from keyline import zipnorm
from keyline.packs.templates import CREATED

DCTERMS = "http://purl.org/dc/terms/"


def _workbook(data: bytes) -> bytes:
    entries = []
    for name, body in zipnorm.read_entries(data):
        if name == "docProps/core.xml":
            root = etree.fromstring(body)
            for tag in ("created", "modified"):
                for el in root.iter(f"{{{DCTERMS}}}{tag}"):
                    el.text = CREATED
            body = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
        entries.append((name, body))
    return zipnorm.pack_bytes(entries)


def normalise(data: bytes) -> bytes:
    """The saved deck with fixed workbook dates and every zip normalised."""
    entries = [
        (name, _workbook(body) if name.endswith(".xlsx") else body)
        for name, body in zipnorm.read_entries(data)
    ]
    return zipnorm.pack_bytes(entries)
