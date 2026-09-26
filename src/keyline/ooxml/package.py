"""Open a .pptx safely: zip checks, relationship resolution, a hardened XML parser."""

from __future__ import annotations

import posixpath
import zipfile
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from keyline.ooxml.ns import NS, PRESENTATION_CONTENT_TYPES, RT_OFFICE_DOCUMENT, rel_type_matches

MAX_TOTAL_UNCOMPRESSED = 512 * 1024 * 1024  # XML and rels parts only (A-18)
MAX_MEMBERS = 20000
XML_SUFFIXES = (".xml", ".rels")


class ScanError(Exception):
    """The input cannot be scanned. The message is a one-line reason (exit 1)."""


@dataclass(frozen=True, slots=True)
class Rel:
    id: str
    type: str
    target: str  # absolute part name without a leading slash, or the raw external URL
    external: bool


def _parser() -> etree.XMLParser:
    return etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
        dtd_validation=False,
        huge_tree=False,
        remove_comments=True,
        remove_pis=True,
    )


def _rels_name(part: str) -> str:
    d, base = posixpath.split(part)
    return posixpath.join(d, "_rels", base + ".rels")


def _resolve(source_part: str, target: str) -> str:
    if target.startswith("/"):
        return posixpath.normpath(target.lstrip("/"))
    base = posixpath.dirname(source_part)
    return posixpath.normpath(posixpath.join(base, target))


class Package:
    def __init__(
        self,
        path: str | Path,
        *,
        max_total: int | None = None,
        max_members: int | None = None,
    ) -> None:
        self.path = Path(path)
        try:
            is_zip = zipfile.is_zipfile(self.path)
        except OSError as exc:
            raise ScanError(f"cannot read {self.path.name}: {exc.strerror or exc}") from exc
        if not is_zip:
            raise ScanError(f"not a zip file: {self.path.name}")
        try:
            self._zip = zipfile.ZipFile(self.path)
            infos = self._zip.infolist()
        except (zipfile.BadZipFile, OSError) as exc:
            raise ScanError(f"corrupt zip file: {self.path.name}") from exc
        max_total = MAX_TOTAL_UNCOMPRESSED if max_total is None else max_total
        max_members = MAX_MEMBERS if max_members is None else max_members
        if len(infos) > max_members:
            raise ScanError(f"too many zip members ({len(infos)} > {max_members})")
        # A-18: only XML and rels parts are ever decompressed; media is never read.
        total = sum(i.file_size for i in infos if i.filename.lower().endswith(XML_SUFFIXES))
        if total > max_total:
            raise ScanError(f"uncompressed XML size {total} bytes exceeds the {max_total} limit")
        self._names = {i.filename for i in infos}
        self._xml: dict[str, etree._Element] = {}
        self._rels: dict[str, dict[str, Rel]] = {}
        self.main_part = self._find_main_part()

    def close(self) -> None:
        self._zip.close()

    def __enter__(self) -> Package:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def has(self, part: str) -> bool:
        return part in self._names

    def read_bytes(self, part: str) -> bytes:
        try:
            return self._zip.read(part)
        except KeyError as exc:
            raise ScanError(f"missing part {part}") from exc
        except (zipfile.BadZipFile, OSError, RuntimeError) as exc:
            raise ScanError(f"cannot read part {part}: {exc}") from exc

    def xml(self, part: str) -> etree._Element:
        cached = self._xml.get(part)
        if cached is not None:
            return cached
        data = self.read_bytes(part)
        try:
            root = etree.fromstring(data, parser=_parser())
        except etree.XMLSyntaxError as exc:
            raise ScanError(f"XML parse failure in {part}: {exc.msg}") from exc
        if root.getroottree().docinfo.doctype:
            raise ScanError(f"DOCTYPE not allowed in {part}")
        self._xml[part] = root
        return root

    def rels(self, part: str) -> dict[str, Rel]:
        """Relationships of `part` ('' for the package), keyed by rId, in document order."""
        cached = self._rels.get(part)
        if cached is not None:
            return cached
        name = "_rels/.rels" if part == "" else _rels_name(part)
        out: dict[str, Rel] = {}
        if self.has(name):
            for el in self.xml(name).iterfind("pr:Relationship", NS):
                rid = el.get("Id", "")
                target = el.get("Target", "")
                external = el.get("TargetMode") == "External"
                resolved = target if external else _resolve(part, target)
                out[rid] = Rel(rid, el.get("Type", ""), resolved, external)
        self._rels[part] = out
        return out

    def rel_targets(self, part: str, rel_type: str) -> list[str]:
        return [
            r.target
            for r in self.rels(part).values()
            if not r.external and rel_type_matches(r.type, rel_type)
        ]

    def content_type(self, part: str) -> str | None:
        if not self.has("[Content_Types].xml"):
            return None
        root = self.xml("[Content_Types].xml")
        for el in root.iterfind("ct:Override", NS):
            if el.get("PartName", "").lstrip("/") == part:
                return el.get("ContentType")
        ext = posixpath.splitext(part)[1].lstrip(".").lower()
        for el in root.iterfind("ct:Default", NS):
            if el.get("Extension", "").lower() == ext:
                return el.get("ContentType")
        return None

    def _find_main_part(self) -> str:
        if not self.has("[Content_Types].xml"):
            raise ScanError("not an OOXML package: [Content_Types].xml is missing")
        targets = self.rel_targets("", RT_OFFICE_DOCUMENT)
        if not targets:
            raise ScanError("not an OOXML package: no officeDocument relationship")
        main = targets[0]
        ctype = self.content_type(main)
        if ctype not in PRESENTATION_CONTENT_TYPES:
            raise ScanError(f"not a pptx: main part is {main} ({ctype or 'unknown type'})")
        if not self.has(main):
            raise ScanError(f"not a pptx: main part {main} is missing")
        return main
