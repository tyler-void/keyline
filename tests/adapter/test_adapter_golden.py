from pathlib import Path

from keyline.geom import Box
from keyline.ooxml.adapter import load_deck

GOLDEN = Path(__file__).resolve().parents[2] / "fixtures" / "golden"
FOREIGN_NESTED = GOLDEN.parent / "foreign" / "nested-groups.pptx"


def by_name(slide, name):
    (s,) = [s for s in slide.shapes if s.name == name]
    return s


def test_kpi_recipe_model():
    deck, diags = load_deck(GOLDEN / "kpi-recipe.pptx")
    assert (deck.width, deck.height) == (12192000, 6858000)
    assert [s.index for s in deck.slides] == [1, 2, 3, 4]
    assert [len(s.shapes) for s in deck.slides] == [4, 10, 5, 8]
    assert [s.has_notes for s in deck.slides] == [False, True, True, True]
    assert [s.background for s in deck.slides] == [
        "solid:#1E2761",
        "solid:#FFFFFF",
        "solid:#FFFFFF",
        "solid:#FFFFFF",
    ]
    t2 = by_name(deck.slides[1], "T2")
    assert t2.box == Box(540000, 432000, 10800000, 720000)
    assert t2.runs[0].size == 3600 and t2.runs[0].bold and t2.runs[0].font == "Georgia"
    assert t2.runs[0].color == "1E2761"
    # slide 3: the chart is its own kind and does not shift the shapes after it (L-001)
    kinds = [s.kind for s in deck.slides[2].shapes]
    assert kinds == ["sp", "graphicFrame:chart", "sp", "sp", "sp"]
    assert deck.slides[2].shapes[1].name == "Rule count by enforcement"
    # slide 4: connectors carry the ids of the boxes they join
    s4 = deck.slides[3]
    ids = {s.name: s.id for s in s4.shapes}
    links = [(c.st_cxn, c.end_cxn) for c in s4.shapes if c.kind == "cxnSp"]
    assert links == [(ids["S1"], ids["S2"]), (ids["S2"], ids["S3"]), (ids["S3"], ids["S4"])]
    card = s4.shapes[1]
    assert card.fill == "solid:#1E2761" and card.geometry == "roundRect"
    assert diags == []


def test_editorial_model():
    deck, diags = load_deck(GOLDEN / "editorial.pptx")
    (slide,) = deck.slides
    assert slide.background == "solid:#F2F2F0"
    l3 = by_name(slide, "l3")
    assert (l3.runs[0].size, l3.runs[0].color, l3.runs[0].caps) == (950, "E8422E", "all")
    verdict = by_name(slide, "verdict")
    assert verdict.fill == "solid:#E8422E" and verdict.text == ""
    assert by_name(slide, "mark").box.y == 450000  # 1.25 cm
    assert diags == []


def test_hidden_group_drops_its_children(tmp_path):
    """A-12: every child of a hidden group leaves the model, and the count covers them."""
    import zipfile

    src = FOREIGN_NESTED
    out = tmp_path / "hidden-group.pptx"
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(out, "w") as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == "ppt/slides/slide1.xml":
                data = data.replace(
                    b'<p:cNvPr id="10" name="G1"/>', b'<p:cNvPr id="10" name="G1" hidden="1"/>'
                )
            zout.writestr(info, data)
    deck, diags = load_deck(out)
    assert deck.slides[0].shapes == []
    (d,) = [f for f in diags if f.rule == "unsupported-content"]
    assert d.message == "4 hidden shapes not linted (A-12)"
