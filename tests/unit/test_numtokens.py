"""Numeric tokens (spec 002 §4.4, T-11): the anchors, the known limits (§4.4.5, B-5), and
equality with the auditor's oracle, imported by path from the spec's evidence folder
(never copied): on the anchors, every string in product.toml, and a seeded corpus."""

import importlib.util
import random
import tomllib

import pytest

from keyline.config import load as load_cfg
from keyline.model import Paragraph, Run, Shape, Slide
from keyline.numtokens import entry_tokens, significant, slide_texts, tokens
from tests.conftest import ROOT

EVIDENCE = ROOT / "specs/002-skill-pack/evidence/numbers_ref.py"
PRODUCT = ROOT / "examples/bonsaihub/product.toml"


def _oracle():
    spec = importlib.util.spec_from_file_location("numbers_ref", EVIDENCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.tokens


ORACLE = _oracle()

# §4.4.3, the auditor's anchors: text -> tokens, "*" marks significant
ANCHORS = {
    "12,400 trees are waiting": ["12,400*"],
    "$1.2M seed round": ["$1.2M*"],
    "$1.2B": ["$1.2B*"],
    "$1.2 million": ["$1.2*"],
    "3.2% of swipes": ["3.2%*"],
    "71 %": ["71%*"],
    "3x faster": ["3x*"],
    "3.2 x": ["3.2*"],
    "-71% churn": ["-71%*"],
    "−0.4%": ["-0.4%*"],
    "12.4k keepers": ["12.4k*"],
    "Q4 2026": ["4", "2026"],
    "Sep 2026": ["2026"],
    "2 pilot cities": ["2"],
    "5kg": ["5"],
    "90-day keeper retention": ["90*"],
    "212-year-old": ["212*"],
    "10-20 trees": ["10*", "20*"],
    "4.99 USD": ["4.99*"],
    "$4.99": ["$4.99*"],
}

# known limits: §4.4.5 and amendment B-5 (pinned so a change is deliberate)
LIMITS = {
    "27 September 2026": ["27*", "2026"],
    "v2.0.1": ["2.0.1*"],
    "3 × 4": ["3×*", "4"],
    "$-5": ["-5*"],  # the $ is dropped: a sign before the currency is the only order
    "12 400 trees": ["12*", "400*"],  # spaces are not thousands separators
    "24/7": ["24*", "7"],
}


def _marked(text):
    return [tok + ("*" if sig else "") for tok, sig in tokens(text)]


@pytest.mark.parametrize("text", list(ANCHORS))
def test_anchor(text):
    assert _marked(text) == ANCHORS[text]


@pytest.mark.parametrize("text", list(LIMITS))
def test_known_limit(text):
    assert _marked(text) == LIMITS[text]


def test_edges_of_the_definition():
    assert _marked("1899 and 2100, but 1900") == ["1899*", "2100*", "1900"]
    assert _marked("Q3-2026") == ["3", "2026"]  # the hyphen after a digit is not a sign
    assert _marked("+5 keepers, +€3") == ["+5*", "+€3*"]
    assert _marked("3bn trees, 3Bonsai, 3B.") == ["3bn*", "3", "3B*"]
    assert _marked("1.5×") == ["1.5×*"]
    assert significant("Save 20 % on 3 trees") == ["20%"]


def _strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from _strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from _strings(v)


def _corpus(n=5000, seed=20260927):
    rng = random.Random(seed)
    parts = (
        list("0123456789") * 4
        + list(".,")
        + list("-−+")
        + list("$€£¥₫")
        + list("%×")
        + ["bn", "k", "K", "M", "B", "x"]
        + [" "] * 4
        + list("aegQvé/")
        + ["٣", "²"]
    )
    corpus: dict[str, None] = {}  # distinct, in generation order
    while len(corpus) < n:
        corpus["".join(rng.choice(parts) for _ in range(rng.randint(1, 24)))] = None
    return list(corpus)


def test_equal_to_the_oracle_on_anchors_limits_and_product_toml():
    product = list(_strings(tomllib.loads(PRODUCT.read_text(encoding="utf-8"))))
    assert len(product) > 50
    for text in [*ANCHORS, *LIMITS, *product]:
        assert tokens(text) == ORACLE(text), text


def test_equal_to_the_oracle_on_a_seeded_corpus():
    corpus = _corpus()
    assert len(set(corpus)) == 5000
    mismatches = [t for t in corpus if tokens(t) != ORACLE(t)]
    assert mismatches == []


def test_entry_tokens():
    got = entry_tokens(
        value="12,400", aliases=["12.4k"], label="Trees on the waitlist", series=None
    )
    assert got == {"12,400", "12.4k"}
    series = entry_tokens(label="Keepers per month", series=[["Apr 2026", 12400], ["May", 3.5]])
    assert series == {"2026", "12,400", "3.5"}
    assert "90" in entry_tokens(value="61%", label="90-day keeper retention")


def _shape(sid, *texts, ph_type=None, table_text=None, hidden=False):
    paras = [Paragraph((Run(t, 2400, hidden=hidden),)) for t in texts]
    return Shape(
        sid, f"s{sid}", "sp", sid, ph_type=ph_type, paragraphs=paras, table_text=table_text
    )


def test_slide_texts_scope():
    cfg = load_cfg()
    slide = Slide(
        1,
        None,
        "solid:#F2F2F0",
        shapes=[
            _shape(2, "12,400 trees", "Source: waitlist, 2026 (18,000 rows)"),
            _shape(3, "7", ph_type="sldNum"),
            _shape(4, "Note: 3 of 4 cities are fictional"),
            _shape(5, "ghost 99", hidden=True),
            Shape(6, "table", "graphicFrame:table", 6, table_text="Q1\t12\nQ2\t14"),
        ],
    )
    got = [(shape.name, text) for shape, text in slide_texts(slide, cfg)]
    assert got == [
        ("s2", "12,400 trees"),
        ("s4", "Note: 3 of 4 cities are fictional"),
        ("table", "Q1\t12\nQ2\t14"),
    ]


def test_adapter_reads_table_text_row_major_outside_paragraphs():
    from keyline.ooxml.adapter import load_deck

    deck, _ = load_deck(ROOT / "fixtures/foreign/stress/d20_pgx_slop.pptx")
    (table,) = [sh for s in deck.slides for sh in s.shapes if sh.kind == "graphicFrame:table"]
    assert table.paragraphs == []
    assert table.table_text.split("\n")[:2] == ["Region\tQ1\tQ2\tQ3\tQ4", "North\t12\t14\t15\t18"]
