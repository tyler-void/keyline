"""Write the generated tables of the skill's docs (spec 002 §8.3; task T-36; Q-54, Q-57):

    python tools/gen_docs.py            # rewrite the tables in place
    python tools/gen_docs.py --check    # exit 1, naming each stale table

A table sits between `<!-- gen:begin NAME -->` and `<!-- gen:end -->` in `SKILL.md` or a
file of `references/`. Its content comes from data only, so the docs cannot drift from
what the tool does:
- `type-scale`: the pack's type scale per mode (pack.toml);
- `budgets`: the per-mode limits the pen and the rules apply (thresholds.toml, pack.toml);
- `roles`: what each role may hold, per mode (pack.toml);
- `layouts`: each role's layouts and their regions (pack.toml);
- `numeral-excluded`: the characters a figure's value may not use (B-26, numerals.json);
- `coverage`: per portable family, its metric twin and the letters of the measured set
  the twin lacks (the fit tables; B-25 item 1).

Dev only. Output is byte-stable.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from keyline.config import load as load_config  # noqa: E402
from keyline.fit import VIETNAMESE, WEIGHTS, load_table  # noqa: E402
from keyline.fit.numerals import excluded  # noqa: E402
from keyline.fit.text import MEASURED, drawn  # noqa: E402
from keyline.packs import resolve  # noqa: E402

SKILL = ROOT / "skill" / "keyline"
PACK = "swiss"
BLOCK = re.compile(r"(<!-- gen:begin ([a-z0-9-]+) -->\n)(.*?)(<!-- gen:end -->)", re.DOTALL)


def _num(value) -> str:
    """A threshold as text: 24, 1.1, 0.08."""
    return f"{float(value):g}"


def _table(head: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines) + "\n"


def type_scale() -> str:
    pack = resolve(PACK)
    rows = []
    for name, shown in pack.styles["presented"].items():
        read = pack.styles["read"][name]
        case = f"caps, +{_num(shown.tracking * 100)} % tracking" if shown.caps else "as typed"
        spacing = _num(shown.line_spacing)
        if read.line_spacing != shown.line_spacing:
            spacing += f" / {_num(read.line_spacing)}"
        rows.append(
            [f"`{name}`", _num(shown.size_pt), _num(read.size_pt), shown.weight, case, spacing]
        )
    head = ["Style", "presented, pt", "read, pt", "Weight", "Case", "Line spacing"]
    return _table(head, rows)


def budgets() -> str:
    pack = resolve(PACK)
    modes = [load_config(mode) for mode in ("presented", "read")]
    keys = [
        ("Words in a title or headline", "title_words_max"),
        ("Reads per brief slide", "reads_max"),
        ("Items in a bullet list", "bullets_max"),
        ("Figures on a slide", "numerals_max"),
        ("Words in a figure's numeral", "kpi_numeral_max_words"),
        ("Words in a label, table header or attribution", "caption_exempt_words"),
        ("Smallest body text, pt", "body_min_pt"),
        ("Smallest source or note line, pt", "source_min_pt"),
        ("Font families in a deck", "font_family_max"),
        ("Text contrast, at least", "contrast_normal"),
    ]
    rows = [[label, *(_num(getattr(c, key)) for c in modes)] for label, key in keys]
    budget = str(pack.accent_budget)
    rows.append(["Accent elements on a slide", budget, budget])
    return _table(["Limit", "presented", "read"], rows)


def roles() -> str:
    pack = resolve(PACK)

    def holds(components: dict) -> str:
        parts = []
        for verb, styles in components.items():
            parts.append(f"`{verb}`" + (f" ({', '.join(styles)})" if styles else ""))
        return ", ".join(parts)

    rows = []
    for role in pack.roles.values():
        shown, read = holds(role.components["presented"]), holds(role.components["read"])
        other = "the same" if read == shown else read
        rows.append([f"`{role.name}`", role.surface, f"`{role.title}`", shown, other])
    return _table(["Role", "Surface", "Title style", "Verbs (styles), presented", "read"], rows)


def layouts() -> str:
    pack = resolve(PACK)
    rows = []
    for role in pack.roles.values():
        for layout in role.layouts:
            variant = layout.split(":")[2] if layout.count(":") == 2 else None
            regions = ", ".join(f"`{r}`" for r in pack.regions[layout])
            how = f'`variant="{variant}"`' if variant else "default"
            rows.append([f"`{role.name}`", how, regions])
    return _table(["Role", "Layout", "Regions"], rows)


def numeral_excluded() -> str:
    out = excluded(resolve(PACK))
    words = {"top": "It would rise above the region", "left": "It would reach left of the region"}
    rows = []
    for edge, why in words.items():
        chars = [c for c, e in out.items() if edge in e.split("+")]
        shown = " ".join(f"{c} (U+{ord(c):04X})" for c in chars)
        rows.append([why, str(len(chars)), shown])
    return _table(["Why", "Count", "Characters"], rows)


def coverage() -> str:
    letters = [c for c in MEASURED if unicodedata.category(c)[0] == "L"]
    signs = [c for c in MEASURED if drawn(c) and unicodedata.category(c)[0] != "L"]
    rows, lacking = [], {}
    for family, twin in load_config().portable_fonts:
        have = set.intersection(*(set(load_table(family, w).advances) for w in WEIGHTS))
        viet = [c for c in VIETNAMESE if ord(c) not in have]
        lacking[family] = viet
        rows.append(
            [
                family,
                twin,
                str(sum(ord(c) not in have for c in letters)),
                str(len(viet)),
                str(sum(ord(c) not in have for c in signs)),
            ]
        )
    head = [
        "Family",
        "Metric twin",
        f"Letters it lacks, of {len(letters)}",
        f"Vietnamese letters it lacks, of {len(VIETNAMESE)}",
        f"Signs it lacks, of {len(signs)}",
    ]
    text = _table(head, rows)
    full = [family for family, viet in lacking.items() if not viet]
    text += f"\nEvery Vietnamese letter: {', '.join(full)}.\n"
    for family, viet in lacking.items():
        if viet:
            text += f"\n{family} lacks these Vietnamese letters: {' '.join(viet)}.\n"
    return text


TABLES = {
    "type-scale": type_scale,
    "budgets": budgets,
    "roles": roles,
    "layouts": layouts,
    "numeral-excluded": numeral_excluded,
    "coverage": coverage,
}


def docs(skill: Path) -> list[Path]:
    return [skill / "SKILL.md", *sorted((skill / "references").glob("*.md"))]


def regenerate(text: str, where: str) -> tuple[str, list[str]]:
    """The text with every table regenerated, and the names of those that were stale."""
    stale = []

    def fill(match: re.Match) -> str:
        name = match[2]
        if name not in TABLES:
            raise SystemExit(f"gen_docs: {where}: unknown table {name!r}")
        fresh = TABLES[name]()
        if match[3] != fresh:
            stale.append(name)
        return match[1] + fresh + match[4]

    return BLOCK.sub(fill, text), stale


def main(argv: list[str], skill: Path = SKILL) -> int:
    check = "--check" in argv
    bad = []
    for path in docs(skill):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        fresh, stale = regenerate(text, path.name)
        bad += [f"{path.relative_to(skill).as_posix()}: {name}" for name in stale]
        if stale and not check:
            path.write_text(fresh, encoding="utf-8")
    if check and bad:
        sys.stderr.write("gen_docs: stale tables:\n" + "".join(f"  {b}\n" for b in bad))
        return 1
    for line in bad:
        print(f"rewrote {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
