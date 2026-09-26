"""AC-7: random bytes and a .docx both exit 1 with a one-line reason."""

import random
import zipfile

from tests.acceptance._cli import keyline

CT = (
    '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/'
    'content-types"><Override PartName="/word/document.xml" ContentType="application/'
    'vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'
)
RELS = (
    '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/'
    '2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
    'officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
    "</Relationships>"
)


def _assert_one_line_failure(proc):
    assert proc.returncode == 1
    assert proc.stdout == b""
    lines = proc.stderr.decode().splitlines()
    assert len(lines) == 1, lines
    return lines[0]


def test_random_bytes(tmp_path):
    p = tmp_path / "noise.pptx"
    p.write_bytes(random.Random(0).randbytes(4096))
    line = _assert_one_line_failure(keyline("lint", p, "--json"))
    assert "not a zip file" in line


def test_docx(tmp_path):
    p = tmp_path / "letter.docx"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("[Content_Types].xml", CT)
        z.writestr("_rels/.rels", RELS)
        z.writestr("word/document.xml", "<w:document/>")
    line = _assert_one_line_failure(keyline("lint", p))
    assert "not a pptx" in line


def test_missing_file(tmp_path):
    line = _assert_one_line_failure(keyline("lint", tmp_path / "nope.pptx"))
    assert "no such file" in line
