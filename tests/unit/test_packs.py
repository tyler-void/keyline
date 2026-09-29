"""Pack loading and validation (spec 002 §5.1, T-08)."""

import copy
import tomllib

import pytest

from keyline.packs import BUNDLED, PackError, _build, bundled, load, resolve

SWISS = BUNDLED / "swiss"
RAW = tomllib.loads((SWISS / "pack.toml").read_text(encoding="utf-8"))


def build(mutate):
    data = copy.deepcopy(RAW)
    mutate(data)
    return _build(data, SWISS)


def test_bundled_and_resolve():
    assert bundled() == ["swiss"]
    assert resolve("swiss").name == "swiss"
    assert resolve(SWISS).directory == SWISS.resolve()
    assert resolve("swiss", base=SWISS.parent).name == "swiss"  # a directory relative to base
    with pytest.raises(PackError, match="pack not found: nope"):
        resolve("nope")


def test_grid_and_regions():
    p = load(SWISS)
    assert p.grid.column_emu == 761000
    assert p.region_box("keyline:evidence:figure", "main").w == 7348000  # 8 columns, 20.41 cm
    box = p.region_box("keyline:evidence", "footer")
    assert box.bottom == 6858000 - 549000  # the bottom margin is kept


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda d: d.pop("palette_roles"), "missing key 'palette_roles'"),
        (lambda d: d["palette_roles"].append("ink"), "roles must be unique"),
        (lambda d: d.update(palette={"paper": "FFFFFF"}), "palette: belongs to a voice"),
        (lambda d: d.update(fonts=["Arial"]), "fonts: belongs to a voice"),
        (lambda d: d["theme"].update(dk1="gold"), "theme.dk1: unknown name 'gold'"),
        (lambda d: d["styles"]["read"]["body"].update(font="serif"), "display or text"),
        (
            lambda d: d["styles"]["read"]["body"]["color"].update(paper="hairline"),
            "'hairline' is not a text role on paper",
        ),
        (lambda d: d["surfaces"]["paper"].update(text=["ink", "gold"]), "unknown name 'gold'"),
        (lambda d: d["styles"]["read"]["body"].update(line_spacing=0.9), "at least 1.0"),
        (lambda d: d["styles"]["read"]["body"].update(weight="light"), "regular or bold"),
        (lambda d: d["styles"]["read"].pop("lede"), "same styles"),
        (lambda d: d["grid"].update(rows=60), "fill the slide height"),
        (
            lambda d: d["regions"]["keyline:evidence"].update(
                main={"col": 1, "span": 12, "row": 10, "rows": 20}
            ),
            "overlap",
        ),
        (
            lambda d: d["regions"]["keyline:evidence"].update(
                main={"col": 6, "span": 8, "row": 20, "rows": 30}
            ),
            "columns outside the grid",
        ),
        (lambda d: d["roles"]["cover"].update(layouts=["keyline:close"]), "not a cover layout"),
        (
            lambda d: d["roles"]["evidence"]["components"]["read"].update(chart=[]),
            "unknown component 'chart'",
        ),
        (
            lambda d: d["roles"]["section"]["components"]["read"].update(text=["lede"]),
            "no colour on ink",
        ),
        (lambda d: d["roles"].pop("quote"), "missing roles: quote"),
        (lambda d: d.update(accents=["accent", "gold"]), "unknown name 'gold'"),
        (lambda d: d.update(containers="cards"), "rules, boxes or none"),
    ],
)
def test_validation_errors_name_the_key(mutate, message):
    with pytest.raises(PackError, match=message):
        build(mutate)


def test_system_has_roles_and_font_slots_not_values():
    p = load(SWISS)
    assert p.palette_roles == ("paper", "ink", "muted", "hairline", "accent", "accent_on_ink")
    assert p.voices() == ["field", "neutral", "night"]
    display = {n for n, st in p.styles["presented"].items() if st.font == "display"}
    assert display == {"cover_title", "statement", "headline", "quote", "numeral"}  # Q-27
    for mode in p.modes:
        assert {st.font for st in p.styles[mode].values()} == {"display", "text"}
    assert not hasattr(p, "palette") and not hasattr(p, "fonts")


def test_accepted_entries_are_rule_and_reason():
    p = build(lambda d: d.update(accepted=[{"rule": "accent-overuse", "reason": "posters"}]))
    assert p.accepted == (("accent-overuse", "posters"),)
    with pytest.raises(PackError, match=r"accepted\[1\] must be \{ rule, reason \}"):
        build(lambda d: d.update(accepted=["accent-overuse"]))


def test_accepted_is_limited_to_acceptable_rules():
    """Amendment B-10: a pack cannot waive a gate, and every entry needs a reason."""
    for gate in ("dead-band", "fiction-undisclosed", "unsourced-number", "voice-contrast"):
        with pytest.raises(PackError, match=rf"accepted\[1\]: '{gate}' cannot be accepted"):
            build(lambda d, g=gate: d.update(accepted=[{"rule": g, "reason": "because"}]))
    with pytest.raises(PackError, match=r"accepted\[1\]: the reason must not be empty"):
        build(lambda d: d.update(accepted=[{"rule": "accent-overuse", "reason": "  "}]))
