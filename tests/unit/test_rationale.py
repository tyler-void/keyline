import re

from keyline.registry import all_rules
from keyline.rules import load_all
from tests.conftest import ROOT


def test_every_rationale_points_at_a_lesson_or_research_heading():
    load_all()
    lessons = set(re.findall(r"\*\*(L-\d{3}) ", (ROOT / "docs/lessons-learned.md").read_text()))
    headings = {
        line.lstrip("#").strip()
        for line in (ROOT / "docs/research.md").read_text().splitlines()
        if line.startswith("#")
    }
    for spec in all_rules():
        r = spec.rationale
        if r.startswith("research §"):
            assert r[len("research §") :] in headings, f"{spec.id}: no heading {r!r}"
        else:
            assert r in lessons, f"{spec.id}: unknown lesson {r!r}"
