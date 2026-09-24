from keyline.config import load
from keyline.model import Paragraph, Run, Shape, Slide
from keyline.rules._common import body_paragraphs, is_kpi_numeral, pick_title, words

CFG = load("presented")


def shape(sid, text, size, ph=None, kind="sp"):
    paras = [Paragraph(runs=(Run(t, size),)) for t in text.split("\n")]
    return Shape(id=sid, name=f"s{sid}", kind=kind, z=sid, ph_type=ph, paragraphs=paras)


def test_words_ignore_separators():
    assert words("officecli validate: pass    ·    view issues: 0 found") == 7
    assert words("a | b — c · d") == 4
    assert words("   ") == 0


def test_kpi_numeral():
    assert is_kpi_numeral(shape(1, "61", 6000), CFG)
    assert not is_kpi_numeral(shape(1, "61", 4700), CFG)
    assert not is_kpi_numeral(shape(1, "one two three four five six", 6000), CFG)


def test_pick_title_prefers_placeholder_then_largest_non_kpi():
    slide = Slide(1, None, "solid:#FFFFFF")
    slide.shapes = [shape(1, "61", 7600), shape(2, "Big heading", 3200), shape(3, "x", 3200)]
    assert pick_title(slide, CFG).id == 2  # KPI skipped; tie goes to the earlier shape
    slide.shapes.append(shape(4, "Placeholder title", 2000, ph="title"))
    assert pick_title(slide, CFG).id == 4


def test_body_paragraphs_exclude_title_and_captions():
    slide = Slide(2, None, "solid:#FFFFFF")
    title = shape(1, "What a text-only gate cannot see", 3600)
    cap = shape(2, "fix cycles, then give up", 1400)  # 5 words: a caption
    body = shape(3, "one two three four five six seven", 1800)
    slide.shapes = [title, cap, body]
    got = [(s.id, p.text) for s, p in body_paragraphs(slide, title, CFG)]
    assert got == [(3, "one two three four five six seven")]
