"""Audit 05 FX-16 (amendment B-22 items 1–3): the estimator and the writer see the same
text. One normalization (NFC, space runs to one U+0020, no leading or trailing space) runs
before both; controls, B-17's line breaks, noncharacters, lone surrogates and invisible
break controls are refused at the verb as PenError naming the code point; `\\n` separates
paragraphs only in text() and notes(). Repros: evidence/audit05-repros/attack_fit1.py,
attack_crlf.py, attack_dblspace.py, attack_nbsp.py."""

import random
import re
import sys
import unicodedata
import zipfile

import pytest
from lxml import etree

from keyline.fit import FitError, Setting, wrap
from keyline.fit.text import JOINERS, SPACES, normalize, paragraphs, refused
from keyline.packs import resolve
from tests.acceptance.m2 import _lo
from tests.conftest import FIXTURES

pytest.importorskip("pptx")

from keyline.pen import Deck, DoesNotFit, PenError

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
NBSP, NNBSP, FIGURE_SPACE = chr(0xA0), chr(0x202F), chr(0x2007)
REFUSED = [0x09, 0x0A, 0x0D, 0x0B, 0x0C, 0x1C, 0x1D, 0x1E, 0x85, 0x2028, 0x2029, 0x00, 0x07,
           0x7F, 0x9F, 0xFFFE, 0xFFFF, 0xD800, 0xAD, 0x200B, 0x2060, 0xFEFF]  # fmt: skip


def written(path):
    """Per slide, {shape name: its <a:t> texts}, and the notes text."""
    z = zipfile.ZipFile(path)
    slides = sorted(
        (n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
        key=lambda n: int(re.search(r"\d+", n).group()),
    )
    out = []
    for name in slides:
        root = etree.fromstring(z.read(name))
        shapes = {}
        for sp in root.iter(f"{P}sp", f"{P}graphicFrame"):
            nv = sp.find(f".//{P}cNvPr")
            shapes[nv.get("name")] = [t.text or "" for t in sp.iter(f"{A}t")]
        out.append(shapes)
    return out


# -- the normalization and the refused set ------------------------------------------------


def test_space_separators_are_every_zs_but_the_joiners():
    zs = {chr(c) for c in range(sys.maxunicode + 1) if unicodedata.category(chr(c)) == "Zs"}
    assert set(SPACES) | set(JOINERS) == zs and not set(SPACES) & set(JOINERS)


def test_normalize():
    ideographic, em = chr(0x3000), chr(0x2003)
    assert (
        normalize("  Regions" + " " * 60 + "snap" + em + ideographic + "to  ") == "Regions snap to"
    )
    assert normalize("Cafe" + chr(0x301)) == "Caf" + chr(0xE9)  # NFC
    joined = f"12{NBSP}400 a{NNBSP}b 1{FIGURE_SPACE}2"
    assert normalize(joined) == joined  # the joiners stay
    for text in ("a  b", " a", "x" + em + em + "y"):
        assert normalize(normalize(text)) == normalize(text)
    assert paragraphs("One  two\n\n  \nThree ") == ["One two", "Three"]


@pytest.mark.parametrize("cp", REFUSED, ids=[f"U+{c:04X}" for c in REFUSED])
def test_refused_characters(cp):
    ch = chr(cp)
    assert refused(f"Grid{ch}works") == ch
    if cp == 0x0A:
        assert refused("Grid\nworks", paragraphs=True) is None
    else:
        assert refused(f"Grid{ch}works", paragraphs=True) == ch


def test_the_joiners_are_not_refused():
    assert refused(f"12{NBSP}400{NNBSP}km{FIGURE_SPACE}x") is None


def test_the_estimator_wraps_the_normalized_text_at_u0020_only():
    arial = Setting("Arial", "regular", 24)
    assert wrap(arial, "  a" + " " * 50 + "b  ", 1000) == ["a b"]
    with pytest.raises(DoesNotFit, match="wider than its region"):
        wrap(arial, NBSP.join(["grid"] * 45), 800)  # one joined word
    with pytest.raises(FitError, match="U\\+0009"):
        wrap(arial, "a\tb", 1000)


# -- the pen: refused at the verb, and written as estimated -------------------------------

EVIDENCE = [str(FIXTURES / "briefs/evidence.toml"), str(FIXTURES / "briefs/extra-evidence.toml")]


def evidence_slide(mode="read"):
    d = Deck(pack="swiss", mode=mode, voice="neutral", evidence=EVIDENCE)
    return d, d.add("evidence", "Most returned tools need a repair", variant="figure")


VERBS = {
    "headline": lambda d, s, t: d.add("evidence", t),
    "text": lambda d, s, t: s.text(t),
    "a bullet": lambda d, s, t: s.bullets(["One", t]),
    "table cell": lambda d, s, t: s.table([["Tool", "Loans"], ["Saw", t]]),
    "header cell": lambda d, s, t: s.table([["Tool", t], ["Saw", "1"]]),
    "label": lambda d, s, t: s.figure("returns_repaired", label=t),
    "source": lambda d, s, t: s.source(t),
    "note": lambda d, s, t: s.note(t),
    "notes": lambda d, s, t: s.notes(t),
    "alt": lambda d, s, t: s.image(str(FIXTURES / "packs/src/build_specimens.py"), alt=t),
}


@pytest.mark.parametrize("what", list(VERBS))
@pytest.mark.parametrize("cp", [0x09, 0x0D, 0x2028, 0x00, 0xFEFF, 0xD800])
def test_every_verb_refuses_at_the_verb(what, cp):
    d, s = evidence_slide()
    with pytest.raises(PenError, match=f"{what} contains U\\+{cp:04X}"):
        VERBS[what](d, s, f"Grid{chr(cp)}works")


@pytest.mark.parametrize("what", [w for w in VERBS if w not in ("text", "notes")])
def test_one_line_texts_refuse_a_newline(what):
    d, s = evidence_slide()
    with pytest.raises(PenError, match=r"U\+000A.*only text\(\) and notes\(\) take"):
        VERBS[what](d, s, "Line one\nLine two")


def test_the_audit_headlines(tmp_path):
    """attack_fit1.py: each input was accepted and then set past the title region."""
    d = Deck(pack="swiss", mode="presented", voice="neutral")
    for text in ["x\t" * 40 + "x", "Line one\nLine two", "Line one\rLine two"]:
        with pytest.raises(PenError, match="headline contains U\\+"):
            d.add("evidence", text)
    for sep in (chr(0x2028), chr(0x2029), chr(0x85)):
        with pytest.raises(PenError, match="headline contains U\\+"):
            d.add("evidence", f"Line one{sep}Line two")
    with pytest.raises(DoesNotFit, match="wider than its region"):
        d.add("evidence", NBSP.join(["grid"] * 45))
    d.add("evidence", "Regions" + " " * 60 + "snap" + " " * 60 + "to one grid")
    d.add("evidence", " " * 70 + "Regions snap to one grid on every slide")
    d.save(str(tmp_path / "h.pptx"))
    titles = [s["title"] for s in written(tmp_path / "h.pptx")]
    assert titles == [["Regions snap to one grid"], ["Regions snap to one grid on every slide"]]


def test_text_takes_newlines_but_not_crlf(tmp_path):
    """attack_crlf.py: `\\r\\n` endings are refused, naming U+000D; `\\n` separates
    paragraphs, each normalized, and blank ones are dropped."""
    d = Deck(pack="swiss", mode="presented", voice="neutral")
    s = d.add("evidence", "Windows line endings")
    with pytest.raises(PenError, match="text contains U\\+000D"):
        s.text("Margins keep a clear edge\r\nGutters part the columns")
    s.text("Margins  keep a clear edge.  Twice.\n\n   \nGutters part the columns ")
    s.notes("Say it.\n\nThen  wait.")
    d.save(str(tmp_path / "t.pptx"))
    assert written(tmp_path / "t.pptx")[0]["main"] == [
        "Margins keep a clear edge. Twice.",
        "Gutters part the columns",
    ]
    notes = zipfile.ZipFile(tmp_path / "t.pptx").read("ppt/notesSlides/notesSlide1.xml")
    assert re.findall(rb"<a:t>([^<]*)</a:t>", notes)[-2:] == [b"Say it.", b"Then wait."]


def test_every_written_text_is_the_normalized_input(tmp_path):
    """The estimator measures and the writer writes the same string, for every verb."""
    d, s = evidence_slide("read")
    messy = "  Regions" + chr(0x3000) + "snap   to  one grid  "
    clean = "Regions snap to one grid"
    s.text(messy)
    s.figure("returns_repaired", region="side", label="  repairs  that  held ")
    s.source(" pack.toml ,  [grid] ")
    s.note("  a   note ")
    t = d.add("evidence", "  A   table ")
    t.table([["  Style ", "Used  for"], [messy, ""]])
    b = d.add("statement", messy)
    b.text("One " + chr(0x2003) * 3 + "two")
    d.save(str(tmp_path / "w.pptx"))
    slides = written(tmp_path / "w.pptx")
    assert slides[0]["main"] == [clean]
    assert slides[0]["side-label"] == ["repairs that held"]
    assert slides[0]["footer"] == ["Source: pack.toml , [grid]", "Note: a note"]
    assert slides[1]["title"] == ["A table"]
    assert slides[1]["main-table"] == ["Style", "Used for", clean, ""]
    assert slides[2]["title"] == [clean] and slides[2]["main"] == ["One two"]


# -- LibreOffice: two spaces after each full stop, filled to the pen's limit --------------

SENTENCES = [
    "The grid has twelve columns.",
    "Rows set the rhythm.",
    "Margins keep a clear edge.",
    "Gutters part the columns.",
    "Every region spans whole columns.",
    "Type steps up.",
]


@_lo.needs_lo("Arial")
@pytest.mark.parametrize("mode", ["presented", "read"])
def test_double_spaces_filled_to_the_limit_stay_in_the_region(mode, tmp_path):
    """attack_dblspace.py: 3 of 12 presented cases ran about 23 pt into the footer."""
    pack = resolve("swiss")
    main = _lo.region_pt(pack, "keyline:evidence", "main")
    d = Deck(pack="swiss", mode=mode, voice="neutral")
    for seed in range(4):
        rng = random.Random(seed)
        sentences = [rng.choice(SENTENCES) for _ in range(120)]
        s = d.add("evidence", "Double spaces")
        best = None
        for n in range(1, 120):
            trial = d.add("evidence", "Scratch")
            try:
                trial.text("  ".join(sentences[:n]))
            except DoesNotFit:
                break
            finally:
                d._slides.pop()
            best = "  ".join(sentences[:n])
        s.text(best)
    d.save(str(tmp_path / "dbl.pptx"))
    pages = _lo.chars(tmp_path / "dbl.pptx", tmp_path / "lo")
    for page in pages:
        body = [c for c in page if c[2] >= main[1] - 1.5]
        assert body and max(c[4] for c in body) <= main[3] + 1.5  # 2 px at 1280 px
