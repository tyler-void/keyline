import random
import zipfile
from pathlib import Path

import pytest

from keyline.ooxml.package import Package, ScanError

GOLDEN = Path(__file__).resolve().parents[2] / "fixtures" / "golden"

CT_PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"
CT_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"


def make_zip(path: Path, parts: dict[str, str | bytes]) -> Path:
    with zipfile.ZipFile(path, "w") as z:
        for name, data in parts.items():
            z.writestr(name, data)
    return path


def content_types(main: str, ctype: str) -> str:
    return (
        '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/'
        f'content-types"><Override PartName="/{main}" ContentType="{ctype}"/></Types>'
    )


def root_rels(target: str) -> str:
    return (
        '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/'
        'package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.'
        'openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        f'Target="{target}"/></Relationships>'
    )


def minimal_pptx(path: Path, presentation: str = "<p/>") -> Path:
    return make_zip(
        path,
        {
            "[Content_Types].xml": content_types("ppt/presentation.xml", CT_PPTX),
            "_rels/.rels": root_rels("ppt/presentation.xml"),
            "ppt/presentation.xml": presentation,
        },
    )


def test_random_bytes(tmp_path):
    p = tmp_path / "noise.pptx"
    p.write_bytes(random.Random(0).randbytes(4096))
    with pytest.raises(ScanError, match="not a zip file"):
        Package(p)


def test_docx_is_rejected(tmp_path):
    p = make_zip(
        tmp_path / "doc.docx",
        {
            "[Content_Types].xml": content_types("word/document.xml", CT_DOCX),
            "_rels/.rels": root_rels("word/document.xml"),
            "word/document.xml": "<w/>",
        },
    )
    with pytest.raises(ScanError, match=r"not a pptx: main part is word/document\.xml"):
        Package(p)


def test_zip_without_content_types(tmp_path):
    p = make_zip(tmp_path / "x.pptx", {"hello.txt": "hi"})
    with pytest.raises(ScanError, match="Content_Types"):
        Package(p)


def test_size_cap(tmp_path):
    p = make_zip(tmp_path / "big.pptx", {"a.bin": b"\0" * 5000})
    with pytest.raises(ScanError, match="exceeds"):
        Package(p, max_total=1000)


def test_member_cap(tmp_path):
    p = make_zip(tmp_path / "many.pptx", {f"f{i}": "" for i in range(12)})
    with pytest.raises(ScanError, match="too many"):
        Package(p, max_members=10)


def test_xxe_is_rejected(tmp_path):
    evil = (
        '<?xml version="1.0"?><!DOCTYPE p [<!ENTITY x SYSTEM "file:///etc/passwd">]>'
        "<p>&x;</p>"
    )
    pkg = Package(minimal_pptx(tmp_path / "xxe.pptx", evil))
    with pytest.raises(ScanError, match="DOCTYPE"):
        pkg.xml("ppt/presentation.xml")


def test_billion_laughs_is_rejected(tmp_path):
    lol = (
        '<?xml version="1.0"?><!DOCTYPE p [<!ENTITY a "aaaaaaaaaa">'
        '<!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">]><p>&b;</p>'
    )
    pkg = Package(minimal_pptx(tmp_path / "lol.pptx", lol))
    with pytest.raises(ScanError):
        pkg.xml("ppt/presentation.xml")


def test_malformed_xml(tmp_path):
    pkg = Package(minimal_pptx(tmp_path / "bad.pptx", "<p><unclosed></p>"))
    with pytest.raises(ScanError, match="XML parse failure"):
        pkg.xml("ppt/presentation.xml")


def test_golden_rels_resolve_absolute_targets():
    # OfficeCLI writes absolute targets ("/ppt/slideLayouts/...").
    with Package(GOLDEN / "kpi-recipe.pptx") as pkg:
        assert pkg.main_part == "ppt/presentation.xml"
        slide_rels = pkg.rels("ppt/slides/slide1.xml")
        targets = sorted(r.target for r in slide_rels.values())
        assert targets == ["ppt/slideLayouts/slideLayout1.xml"]
