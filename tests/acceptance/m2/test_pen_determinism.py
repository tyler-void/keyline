"""Spec 002 §6.5 (task T-27): the same script and inputs give byte-identical .pptx files,
charts included; core properties come from the template and the author argument."""

import io
import time
import zipfile

import pytest

pytest.importorskip("pptx")

from keyline.packs.templates import CREATED
from keyline.pen import Deck
from tests.conftest import FIXTURES

EVIDENCE = [str(FIXTURES / "briefs/evidence.toml"), str(FIXTURES / "briefs/extra-evidence.toml")]


def build(path, author="Tyler"):
    d = Deck(pack="swiss", mode="presented", voice="neutral", evidence=EVIDENCE)
    d.add("cover", "Toolshed Commons").text("A neighbourhood tool library", style="lede").note()
    s = d.add("evidence", "Membership grew after the first bench opened", notes="n")
    s.chart_bar("members_by_quarter", highlight="Q3").source()
    d.add("evidence", "What members borrow most", notes="n").table(
        [["Tool", "Loans"], ["Saw", "120"]]
    )
    d.save(str(path), author=author)
    return path.read_bytes()


def test_two_builds_are_byte_identical(tmp_path):
    first = build(tmp_path / "a.pptx")
    time.sleep(1.1)  # a build time in any part would now differ
    assert build(tmp_path / "b.pptx") == first


def test_the_zips_are_normalised_and_the_dates_fixed(tmp_path):
    data = build(tmp_path / "a.pptx")
    outer = zipfile.ZipFile(io.BytesIO(data))
    names = outer.namelist()
    assert names[0] == "[Content_Types].xml" and names[1:] == sorted(names[1:])
    assert {i.date_time for i in outer.infolist()} == {(1980, 1, 1, 0, 0, 0)}
    core = outer.read("docProps/core.xml").decode()
    assert f">{CREATED}</dcterms:created>" in core and f">{CREATED}</dcterms:modified>" in core
    assert "<dc:creator>Tyler</dc:creator>" in core and "<cp:lastModifiedBy>Tyler<" in core
    (book,) = [n for n in names if n.endswith(".xlsx")]
    inner = zipfile.ZipFile(io.BytesIO(outer.read(book)))
    assert {i.date_time for i in inner.infolist()} == {(1980, 1, 1, 0, 0, 0)}
    inner_core = inner.read("docProps/core.xml").decode()
    assert inner_core.count(CREATED) == 2


def test_the_author_argument_is_the_only_identity(tmp_path):
    core = zipfile.ZipFile(io.BytesIO(build(tmp_path / "x.pptx", author=""))).read(
        "docProps/core.xml"
    )
    assert b"<dc:creator/>" in core or b"<dc:creator></dc:creator>" in core
