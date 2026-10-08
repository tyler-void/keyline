"""Audit 06 FX-30: a chart series is non-empty, and every value is finite and representable
as a float; this is checked when the evidence loads and again at chart_bar() (B-23).
Before, `nan`, `inf` and `series = []` passed both, and save() then failed and lost the
deck; an integer above 1e308 made chart_bar() raise a raw OverflowError. Also from the
audit: text with no visible character (only spaces and format controls) is refused.
Repros: evidence/audit06-repros/t_chart.py and t_misc.py."""

import dataclasses

import pytest

from keyline.brief import BriefError, load_evidence
from keyline.fit.text import visible
from tests.acceptance._cli import keyline
from tests.conftest import FIXTURES

pytest.importorskip("pptx")

from keyline.pen import Deck, PenError

HEAD = 'schema = 1\n\n[product]\nname = "Chart attack"\nfictional = false\n'
SERIES = {
    "nan": ('series = [["a", 1], ["b", nan], ["c", 3]]', "nan is not a finite number"),
    "inf": ('series = [["a", 1], ["b", inf]]', "inf is not a finite number"),
    "minus_inf": ('series = [["a", 1], ["b", -inf]]', "-inf is not a finite number"),
    "empty": ("series = []", "must have at least one"),
    "huge": (f'series = [["a", 1], ["b", 1{"0" * 400}]]', "too large for a chart"),
}


def evidence(tmp_path, name, line):
    path = tmp_path / f"{name}.toml"
    path.write_text(
        HEAD + f'\n[[evidence]]\nid = "{name}"\nlabel = "a series"\nsource = "test"\n{line}\n',
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize("name", list(SERIES))
def test_the_loader_refuses_a_series_it_cannot_chart(name, tmp_path):
    line, message = SERIES[name]
    path = evidence(tmp_path, name, line)
    with pytest.raises(BriefError, match=message):
        load_evidence([str(path)])
    with pytest.raises(PenError, match=message):
        Deck(pack="swiss", mode="presented", voice="neutral", evidence=str(path))


@pytest.mark.parametrize("name", ["nan", "inf", "empty", "huge"])
def test_chart_bar_checks_again(name):
    """An entry that bypassed the loader is refused at the verb as PenError, not later."""
    d = Deck(
        pack="swiss",
        mode="presented",
        voice="neutral",
        evidence=[
            str(FIXTURES / "briefs/evidence.toml"),
            str(FIXTURES / "briefs/extra-evidence.toml"),
        ],
    )
    entries = d._evidence.entries
    good = entries["members_by_quarter"]
    bad = {
        "nan": (("a", 1), ("b", float("nan"))),
        "inf": (("a", 1), ("b", float("inf"))),
        "empty": (),
        "huge": (("a", 1), ("b", 10**400)),
    }[name]
    entries["members_by_quarter"] = dataclasses.replace(good, series=bad)
    s = d.add("evidence", "A chart")
    with pytest.raises(PenError, match="members_by_quarter"):
        s.chart_bar("members_by_quarter")
    entries["members_by_quarter"] = good
    s.chart_bar("members_by_quarter")


INVISIBLE = {
    "ZWJ": chr(0x200D),
    "U+2061": chr(0x2061),
    "VS16": chr(0xFE0F),  # category Mn, but ignorable
    "LRM": chr(0x200E),
    "ZWJ+LRM": chr(0x200D) + " " + chr(0x200E),
    "CGJ+VS17": chr(0x034F) + chr(0xE0100),
    "Hangul filler": chr(0x3164),  # category Lo, but ignorable
}


def test_visible():
    for ch in "a0.%" + chr(0x301) + chr(0x20AB) + chr(0x6F22) + chr(0x1F600):
        assert visible(ch), hex(ord(ch))
    for ch in " " + chr(0xA0) + "".join(INVISIBLE.values()):
        assert not visible(ch), hex(ord(ch))


@pytest.mark.parametrize("name", list(INVISIBLE))
def test_text_with_no_visible_character_is_refused(name):
    text = INVISIBLE[name]
    d = Deck(pack="swiss", mode="presented", voice="neutral")
    with pytest.raises(PenError, match="headline has no visible character"):
        d.add("evidence", text)
    s = d.add("evidence", "A headline")
    with pytest.raises(PenError, match="text has no visible character"):
        s.text(text)
    with pytest.raises(PenError, match="text has no visible character"):
        s.text(f"A paragraph\n{text}")
    with pytest.raises(PenError, match="source has no visible character"):
        s.source(text)
    s.text(f"Visible {text} text")  # a visible character is enough
    t = d.add("evidence", "A table")
    with pytest.raises(PenError, match="has no visible character"):
        t.table([["Item", "Value"], ["Q3", text]])
    t.table([["Item", "Value"], ["Q3", ""]])  # an empty cell stays allowed


def test_keyline_brief_names_the_bad_series(tmp_path):
    path = evidence(tmp_path, "nan", SERIES["nan"][0])
    brief = tmp_path / "b.brief.toml"
    valid = (FIXTURES / "briefs/valid.brief.toml").read_text(encoding="utf-8")
    start = valid.index("evidence = [")
    end = valid.index("\n", start)
    brief.write_text(valid[:start] + f'evidence = ["{path.name}"]' + valid[end:], encoding="utf-8")
    proc = keyline("brief", brief)
    assert proc.returncode != 0
    assert "nan is not a finite number" in proc.stderr.decode()
