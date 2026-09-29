"""Spec 002 §6.1 and AC-10 part 1 (task T-23): the pen's public API is token-only and
writer-independent; Deck builds its voice's template in memory, refuses an error-level
voice, walks a brief, draws the keyline on evidence slides, and removes the placeholders
it does not fill."""

import ast
import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("pptx")

from keyline.ooxml.adapter import load_deck
from keyline.packs import resolve
from keyline.packs.templates import committed
from keyline.pen import Deck, DoesNotFit, PenError, SlideBuilder
from tests.conftest import FIXTURES, ROOT

PEN = ROOT / "src/keyline/pen"
FORBIDDEN = {
    "color", "colour", "rgb", "hex", "fill", "font", "typeface", "family", "size",
    "font_size", "pt", "width", "height", "length", "x", "y", "left", "top", "right",
    "bottom", "emu", "cm", "inches", "align", "alignment", "anchor", "position", "offset",
    "bold", "italic",
}  # fmt: skip


def _public_callables():
    for cls in (Deck, SlideBuilder):
        for name, member in inspect.getmembers(cls):
            if (name == "__init__" or not name.startswith("_")) and callable(member):
                yield f"{cls.__name__}.{name}", member


def test_no_public_parameter_accepts_a_raw_value():
    for name, fn in _public_callables():
        for param in inspect.signature(fn).parameters.values():
            assert param.name not in FORBIDDEN, (name, param.name)
            ann = str(param.annotation)
            for bad in ("Length", "Emu", "RGB", "Pt", "Inches", "Cm", "pptx"):
                assert bad not in ann, (name, param.name, ann)


def test_only_the_writer_imports_python_pptx():
    for path in PEN.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {
            (n.module or "") if isinstance(n, ast.ImportFrom) else a.name
            for n in ast.walk(tree)
            if isinstance(n, ast.Import | ast.ImportFrom)
            for a in (n.names if isinstance(n, ast.Import) else [n])
        }
        uses_pptx = any(x == "pptx" or x.startswith("pptx.") for x in names)
        assert uses_pptx == (path.name == "_writer_pptx.py"), path.name


def test_builders_are_pen_types():
    deck = Deck(pack="swiss", mode="presented", voice="neutral")
    builder = deck.add("statement", "Every tree deserves a patient keeper")
    assert type(builder).__module__.startswith("keyline.pen")
    assert builder.notes("Say it.") is builder


@pytest.mark.parametrize("raw", ["#CC3322", "CC3322", "24pt", "2cm", "12 px", "3in", "9144emu"])
def test_raw_values_are_refused_as_tokens(raw):
    deck = Deck(pack="swiss", mode="presented", voice="neutral")
    with pytest.raises(PenError, match="looks like a raw value"):
        deck.add(raw, "Every tree deserves a patient keeper")
    with pytest.raises(PenError, match="looks like a raw value"):
        deck.add("evidence", "Every tree deserves a patient keeper", variant=raw)


def test_unknown_role_mode_and_variant():
    with pytest.raises(PenError, match="has no read mode"):
        Deck(pack=str(FIXTURES / "briefs/packs/presented-only"), mode="read", voice="x")
    deck = Deck(pack="swiss", mode="presented", voice="neutral")
    with pytest.raises(PenError, match="unknown role 'intro'"):
        deck.add("intro", "Hello")
    with pytest.raises(PenError, match="role evidence has no variant 'chart'"):
        deck.add("evidence", "Hello", variant="chart")


def test_the_pen_refuses_an_error_level_voice(tmp_path):
    text = (resolve("swiss").directory / "voices/neutral.toml").read_text(encoding="utf-8")
    faint = text.replace('name = "neutral"', 'name = "faint"').replace(
        'muted = "5C5C5A"', 'muted = "9A9A98"'
    )
    (tmp_path / "faint.toml").write_text(faint, encoding="utf-8")
    with pytest.raises(PenError, match="refuses this voice: voice-contrast"):
        Deck(pack="swiss", mode="presented", voice=str(tmp_path / "faint.toml"))


def test_an_overlong_headline_does_not_fit():
    deck = Deck(pack="swiss", mode="presented", voice="neutral")
    long = "The waitlist grew faster than keepers could sign up " * 3
    with pytest.raises(DoesNotFit, match=r"^headline needs \d+ lines, region holds 2"):
        deck.add("evidence", long)


def test_the_template_is_the_committed_neutral_one():
    """Q-46: the in-memory template for (neutral, mode) is the committed file."""
    for mode in ("presented", "read"):
        deck = Deck(pack="swiss", mode=mode, voice="neutral")
        assert deck._template == committed(resolve("swiss"), mode).read_bytes()


def test_a_saved_deck(tmp_path):
    deck = Deck(pack="swiss", mode="presented", voice="neutral")
    deck.add("cover", "BonsaiHub")
    deck.add("evidence", "The waitlist grew faster than keepers could sign up", notes="n")
    quote = "I came to borrow a saw and stayed to learn how to sharpen one"
    deck.add("quote", quote, notes="Read it slowly.")
    out = tmp_path / "pen.pptx"
    deck.save(str(out), author="Tyler")
    model, diags = load_deck(out)
    assert diags == []
    assert [s.role for s in model.slides] == ["cover", "evidence", "quote"]
    evidence = model.slides[1]
    assert [sh.name for sh in evidence.shapes] == ["title", "keyline"]  # no empty placeholder
    (keyline,) = [sh for sh in evidence.shapes if sh.name == "keyline"]
    assert keyline.fill == "solid:#111111"
    (q,) = model.slides[2].shapes
    assert q.text == quote  # no added quote marks
    assert q.runs[0].size == 4400  # the quote style, presented
    assert model.slides[2].has_notes and not model.slides[0].has_notes


def test_next_walks_the_brief():
    deck = Deck.from_brief(str(FIXTURES / "briefs/drift/base.brief.toml"))
    roles = [deck.next()._role.name for _ in range(5)]
    assert roles == ["cover", "statement", "evidence", "evidence", "close"]
    with pytest.raises(PenError, match="the brief has 5 slides; no slide 6"):
        deck.next()


def test_lint_core_still_never_imports_the_pen():
    code = (
        "import json, sys, keyline.lint, keyline.brief; "
        "print(json.dumps(sorted(m for m in sys.modules if m.startswith('keyline.pen'))))"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert json.loads(out.stdout) == []


def test_pen_output_is_written_where_asked(tmp_path):
    deck = Deck(pack="swiss", mode="read", voice="field")
    deck.add("statement", "Every tree deserves a patient keeper", notes="n")
    deck.save(str(tmp_path / "x.pptx"))
    assert Path(tmp_path / "x.pptx").stat().st_size > 10000
