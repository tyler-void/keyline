import zipfile

import pytest

from keyline.zipnorm import EPOCH, normalise, pack_bytes, read_entries


def test_order_dates_and_compression(tmp_path):
    data = pack_bytes([("ppt/b.xml", b"<b/>"), ("[Content_Types].xml", b"<t/>"), ("a.xml", b"a")])
    p = tmp_path / "x.zip"
    p.write_bytes(data)
    with zipfile.ZipFile(p) as z:
        infos = z.infolist()
    assert [i.filename for i in infos] == ["[Content_Types].xml", "a.xml", "ppt/b.xml"]
    assert {i.date_time for i in infos} == {EPOCH}
    assert {i.compress_type for i in infos} == {zipfile.ZIP_STORED}


def test_same_entries_same_bytes_whatever_the_order():
    a = [("x.xml", b"1"), ("[Content_Types].xml", b"2")]
    assert pack_bytes(a) == pack_bytes(list(reversed(a)))


def test_normalise_is_idempotent(tmp_path):
    p = tmp_path / "d.pptx"
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("z.xml", "<z/>")
        z.writestr("[Content_Types].xml", "<t/>")
    first = normalise(p).read_bytes()
    assert normalise(p).read_bytes() == first
    assert read_entries(first) == [("[Content_Types].xml", b"<t/>"), ("z.xml", b"<z/>")]


def test_duplicates_rejected():
    with pytest.raises(ValueError):
        pack_bytes([("a", b""), ("a", b"")])
