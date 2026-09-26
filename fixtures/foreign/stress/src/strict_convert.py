# Adapted from audit 02's stress-corpus/src/strict_convert.py: output paths, test photo and the Tyler author only (see _stress.py).
"""D27: mechanically convert D02 (transitional) to ISO/IEC 29500 Strict conformance, as
PowerPoint's "Strict Open XML Presentation" save option writes it: purl.oclc.org
namespaces and relationship types, conformance="strict", and percentages written as
"NN%" strings. Content types and package-level namespaces are unchanged.

Usage: python ppx_layouts.py /tmp/d02.pptx && python strict_convert.py /tmp/d02.pptx [OUT]
"""
import re
import sys
import zipfile

import _stress  # noqa: E402  (fixtures/foreign/stress/src)


SRC = sys.argv[1]
OUT = _stress.out_path("d27_strict_from_ppx.pptx", argv_index=2)
NS = [
    ("http://schemas.openxmlformats.org/presentationml/2006/main", "http://purl.oclc.org/ooxml/presentationml/main"),
    ("http://schemas.openxmlformats.org/drawingml/2006/main", "http://purl.oclc.org/ooxml/drawingml/main"),
    ("http://schemas.openxmlformats.org/drawingml/2006/chart", "http://purl.oclc.org/ooxml/drawingml/chart"),
    ("http://schemas.openxmlformats.org/drawingml/2006/picture", "http://purl.oclc.org/ooxml/drawingml/picture"),
    ("http://schemas.openxmlformats.org/officeDocument/2006/relationships", "http://purl.oclc.org/ooxml/officeDocument/relationships"),
    ("http://schemas.openxmlformats.org/officeDocument/2006/extended-properties", "http://purl.oclc.org/ooxml/officeDocument/extendedProperties"),
    ("http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes", "http://purl.oclc.org/ooxml/officeDocument/docPropsVTypes"),
]
PCT_VAL = ("lumMod", "lumOff", "tint", "shade", "alpha", "satMod", "satOff", "hueMod", "spcPct", "alphaMod", "alphaOff")


def pct(n):
    v = int(n) / 1000
    return (f"{v:g}") + "%"


def to_strict(name, data):
    if not (name.endswith(".xml") or name.endswith(".rels")):
        return data
    s = data.decode("utf-8")
    for a, b in NS:
        s = s.replace(a, b)
    s = re.sub(r"<a:(%s) val=\"(-?\d+)\"" % "|".join(PCT_VAL), lambda m: f'<a:{m.group(1)} val="{pct(m.group(2))}"', s)
    s = re.sub(r'<a:gs pos="(\d+)"', lambda m: f'<a:gs pos="{pct(m.group(1))}"', s)
    s = re.sub(r'<a:fillToRect l="(-?\d+)" t="(-?\d+)" r="(-?\d+)" b="(-?\d+)"',
               lambda m: '<a:fillToRect l="%s" t="%s" r="%s" b="%s"' % tuple(pct(g) for g in m.groups()), s)
    if name == "ppt/presentation.xml":
        s = s.replace("<p:presentation ", '<p:presentation conformance="strict" ', 1)
    return s.encode("utf-8")


zin = zipfile.ZipFile(SRC)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zo:
    for info in zin.infolist():
        zo.writestr(info, to_strict(info.filename, zin.read(info.filename)))
print("wrote", OUT)
