"""Audit 05 FX-22 and FX-23 (amendment B-23): a refused verb leaves the slide exactly as
it was; the footer region takes only source() and note(); `accent` and `header` must be
bool; on a deck made from a brief, next() after add() is a PenError; bullets_max counts
per slide. Repros: evidence/audit05-repros/attack_state.py and attack_next.py."""

import re
import zipfile

import pytest
from PIL import Image

from tests.acceptance.m2 import _lo
from tests.conftest import FIXTURES

pytest.importorskip("pptx")

from keyline.pen import Deck, DoesNotFit, PenError

EVIDENCE = [str(FIXTURES / "briefs/evidence.toml"), str(FIXTURES / "briefs/extra-evidence.toml")]
LONG = "a very long source line " * 12


def texts(path):
    z = zipfile.ZipFile(path)
    names = sorted(n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n))
    return [re.findall(r"<a:t>([^<]*)</a:t>", z.read(n).decode()) for n in names]


def test_a_refused_source_keeps_the_note_and_allows_a_retry(tmp_path):
    """attack_state.py (b): the note vanished, and the retry was refused."""
    d = Deck(pack="swiss", mode="presented", voice="neutral")
    s = d.add("evidence", "Regions snap to one grid")
    s.text("Body text here.")
    s.note("the note that was accepted")
    with pytest.raises(DoesNotFit):
        s.source(LONG)
    s.source("pack.toml")
    d.save(str(tmp_path / "b.pptx"))
    (slide,) = texts(tmp_path / "b.pptx")
    assert slide[-2:] == ["Source: pack.toml", "Note: the note that was accepted"]


def evidence_slide(mode="read"):
    d = Deck(pack="swiss", mode=mode, voice="neutral", evidence=EVIDENCE)
    return d, d.add("evidence", "Most returned tools need a repair", variant="figure")


def refusals(tmp_path):
    bad_image = tmp_path / "band.ppm"
    Image.new("RGB", (40, 10), "#336699").save(bad_image, format="PPM")
    return {
        "text": lambda s: s.text("word " * 400),
        "bullets": lambda s: s.bullets(["word " * 200, "b"]),
        "table": lambda s: s.table([["A", "B"]] + [["row", "cell"]] * 60),
        "figure": lambda s: s.figure("returns_repaired", label="one two three four five six"),
        "chart_bar": lambda s: s.chart_bar("members_by_quarter", highlight="Q9"),
        "image": lambda s: s.image(str(bad_image), alt="A band"),
        "source": lambda s: s.source(LONG),
        "note": lambda s: s.note(LONG),
        "notes": lambda s: s.notes("a\tb"),
        "second accent": lambda s: s.figure("bench_hours", region="side", accent=True),
    }


@pytest.mark.parametrize(
    "verb",
    ["text", "bullets", "table", "figure", "chart_bar", "image", "source", "note", "notes",
     "second accent"],
)  # fmt: skip
def test_a_refused_verb_leaves_the_slide_as_it_was(verb, tmp_path):
    _d, s = evidence_slide()
    s.figure("returns_repaired", accent=True).source().note("A note")
    s.notes("Say it.")
    before = s._state()
    with pytest.raises((DoesNotFit, PenError)):
        refusals(tmp_path)[verb](s)
    assert s._state() == before


def test_the_footer_takes_only_source_and_note():
    """attack_state.py (c): body text in the footer, silently replaced by source()."""
    _d, s = evidence_slide()
    for call in (
        lambda: s.text("Revenue grew 40 percent", region="footer"),
        lambda: s.bullets(["one"], region="footer"),
        lambda: s.table([["A", "B"], ["1", "2"]], region="footer"),
        lambda: s.figure("returns_repaired", region="footer"),
        lambda: s.chart_bar("members_by_quarter", region="footer"),
    ):
        with pytest.raises(PenError, match=r"the footer region takes only source\(\) and note"):
            call()
    s.source("pack.toml")


def test_bullets_max_counts_per_slide():
    """attack_state.py (d): 4 + 4 bullets in main and side on one presented slide."""
    d = Deck(pack="swiss", mode="presented", voice="neutral")
    s = d.add("evidence", "Regions snap to one grid", variant="figure")
    s.bullets(["one", "two"], region="main")
    with pytest.raises(PenError, match="5 bullets on this slide; at most 4 in presented mode"):
        s.bullets(["three", "four", "five"], region="side")
    s.bullets(["three", "four"], region="side")


@pytest.mark.parametrize("value", ["#00FF00", 1, None, "yes"])
def test_flags_must_be_bool(value):
    """attack_state.py (e): figure(accent="#00FF00") spent the accent; table(header="2cm")
    was taken."""
    _d, s = evidence_slide()
    with pytest.raises(PenError, match="accent must be True or False"):
        s.figure("returns_repaired", accent=value)
    assert s._accents == 0
    with pytest.raises(PenError, match="header must be True or False"):
        s.table([["A", "B"], ["1", "2"]], header=value)


def test_next_after_add_is_refused():
    """attack_next.py: after an add(), next() silently skipped a brief slide."""
    brief = str(FIXTURES / "packs/swiss-specimen-read-field.brief.toml")
    d = Deck.from_brief(brief)
    d.add("statement", "An extra slide the brief does not have")
    with pytest.raises(PenError, match=r"next\(\) walks the brief, and this deck has a slide"):
        d.next()
    d = Deck.from_brief(brief)
    assert d.next()._role.name == "cover"
    d.add("statement", "An extra slide")
    with pytest.raises(PenError, match="has a slide from add"):
        d.next()


def test_a_refused_headline_leaves_no_coverage_warning(tmp_path, capsys):
    voice = _lo.voice_file(tmp_path, "Cambria")
    d = Deck(pack="swiss", mode="presented", voice=voice)
    vietnamese = "Người giữ ở lại cả mùa"
    with pytest.raises(DoesNotFit):
        d.add("evidence", " ".join([vietnamese] * 12))
    d.add("evidence", "A plain headline")
    d.save(str(tmp_path / "d.pptx"))
    assert capsys.readouterr().err == ""
