"""Phase B rehearsal (report B): `next()` applies the brief's headline, so when the pen
refuses it, the refusal names the slide. The spine is approved before the build, and a
headline within the word limit can still be too wide for its title: the skill has to
know which one to shorten."""

import pytest

from tests.conftest import FIXTURES

pytest.importorskip("pptx")

from keyline.pen import Deck, DoesNotFit, PenError


def brief(tmp_path, close: str):
    """fixtures/briefs/valid.brief.toml with another headline on its last slide."""
    source = FIXTURES / "briefs"
    for name in ("evidence.toml", "extra-evidence.toml"):
        (tmp_path / name).write_text((source / name).read_text(encoding="utf-8"), encoding="utf-8")
    text = (source / "valid.brief.toml").read_text(encoding="utf-8")
    head, _, last = text.rpartition("[[slides]]")
    lines = [
        f'headline = "{close}"' if line.startswith("headline = ") else line
        for line in last.splitlines()
    ]
    path = tmp_path / "deck.brief.toml"
    path.write_text(head + "[[slides]]" + "\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def test_next_names_the_slide_whose_headline_does_not_fit(tmp_path):
    close = "Book a second meeting soon. We will bring a tree."  # 10 words: inside the limit
    deck = Deck.from_brief(brief(tmp_path, close))
    slides = len(deck._brief.slides)
    for _ in range(slides - 1):
        deck.next()
    with pytest.raises(
        DoesNotFit, match=rf"^slide {slides} \(close\): headline needs 3 lines, region holds 2"
    ):
        deck.next()
    assert len(deck._slides) == slides - 1  # the refused slide was not added (B-23)


def test_add_keeps_its_plain_message():
    deck = Deck(pack="swiss", mode="presented", voice="neutral")
    with pytest.raises(DoesNotFit, match=r"^headline needs \d+ lines, region holds 2"):
        deck.add("close", "Book a second meeting. We bring a tree.")
    with pytest.raises(PenError, match=r"^next\(\) needs a brief"):
        deck.next()
