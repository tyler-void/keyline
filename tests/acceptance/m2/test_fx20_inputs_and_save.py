"""Audit 05 FX-20 (amendment B-23): every input is checked at the verb that receives it;
images are PNG, JPEG, GIF, BMP or TIFF, read when image() is called; save() validates
`author`, writes atomically (a temporary file, then a rename) and raises only PenError.
Repros: evidence/audit05-repros/attack_ctrl.py and attack_img.py."""

import io
import os
import zipfile

import pytest
from PIL import Image, features

pytest.importorskip("pptx")

from keyline.pen import Deck, PenError

CONTROLS = {  # attack_ctrl.py's cases, as code points
    "FF": 0x0C,
    "VT": 0x0B,
    "x1c": 0x1C,
    "NUL": 0x00,
    "BEL": 0x07,
    "surrogate": 0xD800,
    "U+FFFE": 0xFFFE,
}
VERBS = {
    "headline": lambda d, t: d.add("evidence", t),
    "notes": lambda d, t: d.add("evidence", "A headline").notes(t),
    "text": lambda d, t: d.add("evidence", "A headline").text(t),
    "table": lambda d, t: d.add("evidence", "A headline").table([["A", "B"], [t, "x"]]),
}


@pytest.mark.parametrize("verb", list(VERBS))
@pytest.mark.parametrize("case", list(CONTROLS))
def test_controls_are_refused_at_the_verb_and_the_deck_still_saves(verb, case, tmp_path):
    d = Deck(pack="swiss", mode="presented", voice="neutral")
    with pytest.raises(PenError, match=f"U\\+{CONTROLS[case]:04X}"):
        VERBS[verb](d, f"Grid{chr(CONTROLS[case])}works")
    d.add("evidence", "The next slide")
    d.save(str(tmp_path / "d.pptx"))  # the refusal cost nothing else


def picture(path, fmt, size=(400, 100), colour="#336699"):
    Image.new("RGB", size, colour).save(path, format=fmt)
    return str(path)


ACCEPTED = [("PNG", "png"), ("JPEG", "jpg"), ("GIF", "gif"), ("BMP", "bmp"), ("TIFF", "tif")]
REFUSED = [("PPM", "ppm"), ("TGA", "tga"), ("ICO", "ico")]
if features.check("webp"):
    REFUSED.append(("WEBP", "webp"))


@pytest.mark.parametrize(("fmt", "ext"), ACCEPTED)
def test_the_five_formats_are_embedded(fmt, ext, tmp_path):
    d = Deck(pack="swiss", mode="presented", voice="neutral")
    path = picture(tmp_path / f"img.{ext}", fmt)
    d.add("evidence", "A picture").image(path, alt="A blue band")
    d.save(str(tmp_path / "d.pptx"))
    media = [n for n in zipfile.ZipFile(tmp_path / "d.pptx").namelist() if "/media/" in n]
    assert len(media) == 1


@pytest.mark.parametrize(("fmt", "ext"), REFUSED)
def test_other_formats_are_refused_at_image(fmt, ext, tmp_path):
    d = Deck(pack="swiss", mode="presented", voice="neutral")
    path = picture(tmp_path / f"img.{ext}", fmt)
    with pytest.raises(PenError, match=f"is {fmt}; the pen takes PNG, JPEG, GIF, BMP, TIFF"):
        d.add("evidence", "A picture").image(path, alt="A blue band")


def test_the_image_is_read_when_image_is_called(tmp_path):
    """attack_img.py: a file replaced between image() and save() was embedded as it was at
    save(), in the box of the one image() measured."""
    path = tmp_path / "swap.png"
    original = picture(path, "PNG", (100, 100))
    before = path.read_bytes()
    d = Deck(pack="swiss", mode="presented", voice="neutral")
    d.add("evidence", "A swapped picture").image(original, alt="A square")
    picture(path, "PNG", (800, 100), "#993333")
    d.save(str(tmp_path / "d.pptx"))
    z = zipfile.ZipFile(tmp_path / "d.pptx")
    (media,) = [n for n in z.namelist() if "/media/" in n]
    assert z.read(media) == before
    assert Image.open(io.BytesIO(z.read(media))).size == (100, 100)


def test_an_unreadable_image_path_is_a_pen_error(tmp_path):
    d = Deck(pack="swiss", mode="presented", voice="neutral")
    s = d.add("evidence", "A picture")
    for bad in (str(tmp_path / "missing.png"), "a\x00b.png", str(tmp_path)):
        with pytest.raises(PenError, match="cannot be read"):
            s.image(bad, alt="Nothing")


@pytest.mark.parametrize(
    ("author", "message"),
    [
        ("x" * 256, "author has 256 characters; at most 255"),
        ("Ty\x07ler", "author contains U\\+0007"),
        ("Ty\nler", "author contains U\\+000A"),
        (42, "author must be text"),
    ],
)
def test_save_checks_the_author(author, message, tmp_path):
    d = Deck(pack="swiss", mode="presented", voice="neutral")
    d.add("evidence", "A slide")
    with pytest.raises(PenError, match=message):
        d.save(str(tmp_path / "d.pptx"), author=author)
    assert not (tmp_path / "d.pptx").exists()
    d.save(str(tmp_path / "d.pptx"), author="x" * 255)


def test_save_raises_only_pen_errors_and_leaves_nothing_behind(tmp_path, monkeypatch):
    d = Deck(pack="swiss", mode="presented", voice="neutral")
    d.add("evidence", "A slide")
    with pytest.raises(PenError, match=r"cannot write d\.pptx"):
        d.save(str(tmp_path / "no-such-dir" / "d.pptx"))
    target = tmp_path / "d.pptx"
    target.write_bytes(b"the earlier deck")

    import keyline.pen._writer_pptx as writer

    def broken(*args, **kwargs):
        raise RuntimeError("the writer failed")

    monkeypatch.setattr(writer, "write", broken)
    with pytest.raises(PenError, match="cannot write the deck: RuntimeError: the writer failed"):
        d.save(str(target))
    assert target.read_bytes() == b"the earlier deck"  # untouched
    assert sorted(p.name for p in tmp_path.iterdir()) == ["d.pptx"]  # no temporary files


def test_save_replaces_the_file_with_the_usual_mode(tmp_path):
    d = Deck(pack="swiss", mode="presented", voice="neutral")
    d.add("evidence", "A slide")
    target = tmp_path / "d.pptx"
    target.write_bytes(b"old")
    d.save(target)  # a path object works too
    assert zipfile.is_zipfile(target)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["d.pptx"]
    if os.name == "posix":
        umask = os.umask(0)
        os.umask(umask)
        assert target.stat().st_mode & 0o777 == 0o666 & ~umask
