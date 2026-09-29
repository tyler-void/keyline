"""T-22 as audit 04 ruled: when a deck's text uses characters its voice's twin lacks, the
pen prints one warning per deck on save, naming the family, its twin and every such
character, and the build goes ahead. It is not a registry entry."""

import pytest

from keyline.pen import Deck
from tests.conftest import ROOT

pytest.importorskip("pptx")

NEUTRAL = ROOT / "src/keyline/packs/swiss/voices/neutral.toml"


def voice(tmp_path, font):
    path = tmp_path / f"{font.lower()}.toml"
    text = NEUTRAL.read_text(encoding="utf-8").replace(
        'name = "neutral"', f'name = "{font.lower()}"'
    )
    path.write_text(text.replace('"Arial"', f'"{font}"'), encoding="utf-8")
    return str(path)


def build(tmp_path, font):
    d = Deck(pack="swiss", mode="read", voice=voice(tmp_path, font))
    d.add("statement", "Cây cảnh chờ người giữ").text("Người giữ ở lại cả mùa")
    d.add("statement", "Mười hai nghìn cây đang đợi").text("Hồ sơ của từng cây")
    out = tmp_path / f"{font}.pptx"
    d.save(str(out))
    return out


def test_one_warning_per_deck_naming_every_missing_character(tmp_path, capsys):
    assert build(tmp_path, "Cambria").stat().st_size > 0  # the build goes ahead
    err = capsys.readouterr().err.splitlines()
    assert len(err) == 1, err
    line = err[0]
    assert line.startswith("keyline pen: warning: Caladea (for Cambria) lacks: ")
    assert line.endswith(
        "LibreOffice renders them in a fallback font, so the check render is not faithful"
    )
    lacking = line.split("lacks: ", 1)[1].split(";", 1)[0]
    for ch in "ảờữồơừợ":  # from both slides, headlines and body text alike
        assert ch in lacking
    assert len(set(lacking)) == len(lacking)  # each named once


def test_no_warning_when_the_twin_has_every_character(tmp_path, capsys):
    build(tmp_path, "Arial")
    assert capsys.readouterr().err == ""


def test_the_warning_is_not_a_registry_entry():
    from keyline.registry import all_rules
    from keyline.rules import load_all

    load_all()
    ids = [r.id for r in all_rules()]
    assert len(ids) == 35  # B-8.6; the warning added none
    assert not [i for i in ids if any(w in i for w in ("coverage", "glyph"))]
