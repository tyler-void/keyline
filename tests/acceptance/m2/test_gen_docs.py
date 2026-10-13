"""Task T-36 (spec 002 §8.3; Q-54 and Q-57 as ruled): `tools/gen_docs.py` writes the
tables between `<!-- gen:begin NAME -->` and `<!-- gen:end -->` from thresholds.toml,
pack.toml and the fit tables; `--check` exits 1 naming each stale table; the output is
byte-stable."""

import importlib.util
import sys

import pytest

from keyline.config import load as load_config
from keyline.fit.numerals import excluded
from keyline.packs import resolve
from tests.conftest import ROOT


@pytest.fixture(scope="module")
def gen_docs():
    spec = importlib.util.spec_from_file_location("gen_docs", ROOT / "tools" / "gen_docs.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_docs"] = module
    spec.loader.exec_module(module)
    return module


def test_the_tables(gen_docs):
    assert sorted(gen_docs.TABLES) == [
        "budgets", "coverage", "layouts", "numeral-excluded", "roles", "titles", "type-scale",
    ]  # fmt: skip
    for name, table in gen_docs.TABLES.items():
        text = table()
        assert text.startswith("| ") and text.endswith("\n") and "\n\n\n" not in text, name
        assert table() == text, name  # byte-stable


def test_the_type_scale_and_budgets_come_from_the_data(gen_docs):
    pack = resolve("swiss")
    scale = gen_docs.type_scale()
    for name, style in pack.styles["presented"].items():
        read = pack.styles["read"][name]
        assert f"| `{name}` | {float(style.size_pt):g} | {float(read.size_pt):g} |" in scale
    assert "caps, +8 % tracking" in scale
    budgets = gen_docs.budgets()
    shown, read = load_config("presented"), load_config("read")
    assert (
        f"| Words in a title or headline | {shown.title_words_max} | {read.title_words_max} |"
        in budgets
    )
    assert f"| Items in a bullet list | {shown.bullets_max} | {read.bullets_max} |" in budgets
    assert (
        f"| Accent elements on a slide | {pack.accent_budget} | {pack.accent_budget} |" in budgets
    )


def test_the_roles_and_layouts_come_from_the_pack(gen_docs):
    pack = resolve("swiss")
    roles, layouts = gen_docs.roles(), gen_docs.layouts()
    for role in pack.roles.values():
        assert f"| `{role.name}` | {role.surface} | `{role.title}` |" in roles
        for verb in role.components["presented"]:
            assert f"`{verb}`" in roles
    assert '| `evidence` | `variant="figure"` | `title`, `main`, `side`, `footer` |' in layouts
    assert layouts.count("\n") == 2 + sum(len(r.layouts) for r in pack.roles.values())


def test_the_title_table_comes_from_the_pack_and_the_fit(gen_docs):
    """Per role and mode: the lines the title region holds and about how many characters
    fit on a line, as the range over the six portable families."""
    from fractions import Fraction as F

    from keyline.fit import WRAP_MARGIN, Setting, lines_held, width

    pack = resolve("swiss")
    titles = gen_docs.titles()
    assert titles.count("\n") == 2 + len(pack.roles)
    assert "| `cover` | `cover_title` | 2 lines of 18 to 25 characters |" in titles
    assert "| `statement` | `statement` | 2 to 3 lines of" in titles  # Georgia holds one less
    style = pack.styles["presented"]["cover_title"]
    box = pack.region_box("keyline:cover", "title")
    arial = Setting("Arial", style.weight, style.size_pt, line_spacing=style.line_spacing)
    assert lines_held(arial, F(box.h, 12700)) == 2
    per_line = int(
        F(box.w, 12700) * WRAP_MARGIN * len(gen_docs.SAMPLE) / width(arial, gen_docs.SAMPLE)
    )
    assert 18 <= per_line <= 25


def test_the_numeral_and_coverage_tables_come_from_the_fit_data(gen_docs):
    out = excluded(resolve("swiss"))
    numerals = gen_docs.numeral_excluded()
    for ch in out:
        assert f"{ch} (U+{ord(ch):04X})" in numerals
    assert "| 33 |" in numerals and "| 4 |" in numerals
    coverage = gen_docs.coverage()
    assert "| Cambria | Caladea | 442 | 88 | 77 |" in coverage
    assert "| Arial | Liberation Sans | 9 | 0 | 52 |" in coverage
    assert (
        "Every Vietnamese letter: Arial, Times New Roman, Courier New, Georgia, Calibri."
        in coverage
    )
    assert "Cambria lacks these Vietnamese letters:" in coverage


def skill(tmp_path, body: str):
    """A skill folder with one reference that holds `body`."""
    root = tmp_path / "skill" / "keyline"
    (root / "references").mkdir(parents=True)
    (root / "SKILL.md").write_text("no tables here\n", encoding="utf-8")
    doc = root / "references" / "doc.md"
    doc.write_text(body, encoding="utf-8")
    return root, doc


def test_check_names_a_stale_table_and_a_rewrite_fixes_it(gen_docs, tmp_path, capsys):
    stale = "before\n<!-- gen:begin budgets -->\n| old |\n<!-- gen:end -->\nafter\n"
    root, doc = skill(tmp_path, stale)
    assert gen_docs.main(["--check"], skill=root) == 1
    assert "references/doc.md: budgets" in capsys.readouterr().err
    assert doc.read_text(encoding="utf-8") == stale  # --check writes nothing
    assert gen_docs.main([], skill=root) == 0
    fresh = doc.read_text(encoding="utf-8")
    assert (
        fresh
        == f"before\n<!-- gen:begin budgets -->\n{gen_docs.budgets()}<!-- gen:end -->\nafter\n"
    )
    assert gen_docs.main(["--check"], skill=root) == 0
    assert gen_docs.main([], skill=root) == 0 and doc.read_text(encoding="utf-8") == fresh


def test_an_unknown_table_is_an_error(gen_docs, tmp_path):
    root, _doc = skill(tmp_path, "<!-- gen:begin nonsense -->\n<!-- gen:end -->\n")
    with pytest.raises(SystemExit, match="unknown table 'nonsense'"):
        gen_docs.main(["--check"], skill=root)


def test_the_committed_docs_are_current(gen_docs, capsys):
    assert gen_docs.main(["--check"]) == 0, capsys.readouterr().err
