"""Audit 05 FX-21 (amendment B-23): a deck built only through legal pen calls lints with no
error-level finding. A generated sweep: every role × layout × region × component the role
allows × style it allows, in both modes and the three stock voices, is linted with
`--pack swiss --voice <voice>`. A combination the pen refuses is not legal and is left
out (the figure on a presented statement or close, until Q-48's fix). The sweep also
asserts no `body-too-small`: before the fix, text(style="label") took seven words in both
modes, and lint reported them (attack_label.py; a warning in the registry, not an error)."""

import json

import pytest
from PIL import Image

from keyline.packs import resolve
from tests.acceptance._cli import keyline
from tests.conftest import FIXTURES

pytest.importorskip("pptx")

from keyline.pen import Deck, DoesNotFit, PenError

EVIDENCE = [str(FIXTURES / "briefs/evidence.toml"), str(FIXTURES / "briefs/extra-evidence.toml")]
BODY = "Members bring back most tools within a week and report every repair"
CAPTION = "Tools returned this week"  # four words: a caption in any style


def calls(pack, role, mode, picture):
    """(layout variant, region, component, style, call) for everything the role allows."""
    allowed = pack.roles[role].components[mode]
    for layout in pack.roles[role].layouts:
        variant = layout.rsplit(":", 1)[-1] if layout.count(":") == 2 else None
        for region in (r for r in pack.regions[layout] if r not in ("title", "footer")):
            for style in allowed.get("text", ()):
                for text in (BODY, CAPTION):  # a style below the body minimum refuses BODY
                    yield (
                        variant,
                        region,
                        "text",
                        style,
                        lambda s, r=region, st=style, t=text: s.text(t, style=st, region=r),
                    )
            if "bullets" in allowed:
                yield (
                    variant,
                    region,
                    "bullets",
                    "",
                    lambda s, r=region: s.bullets(
                        ["Saws and planes", "Clamps and chisels"], region=r
                    ),
                )
            if "table" in allowed:
                yield (
                    variant,
                    region,
                    "table",
                    "",
                    lambda s, r=region: s.table(
                        [["Tool", "Loans"], ["Saw", "120"]], region=r
                    ).source("Tool library ledger, 2026"),
                )
            if "figure" in allowed:
                yield (
                    variant,
                    region,
                    "figure",
                    "",
                    lambda s, r=region: s.figure("returns_repaired", region=r).source(),
                )
            if "chart_bar" in allowed:
                yield (
                    variant,
                    region,
                    "chart_bar",
                    "",
                    lambda s, r=region: s.chart_bar("members_by_quarter", region=r).source(),
                )
            if "image" in allowed:
                yield (
                    variant,
                    region,
                    "image",
                    "",
                    lambda s, r=region: s.image(picture, region=r, alt="A blue band"),
                )
        if "attribution" in allowed:
            yield variant, "main", "attribution", "", lambda s: s.attribution("The keepers")


@pytest.mark.parametrize("mode", ["presented", "read"])
@pytest.mark.parametrize("voice", ["neutral", "night", "field"])
def test_every_legal_call_lints_without_an_error(mode, voice, tmp_path):
    pack = resolve("swiss")
    picture = tmp_path / "band.png"
    Image.new("RGB", (800, 200), "#336699").save(picture)
    d = Deck(pack="swiss", mode=mode, voice=voice, evidence=EVIDENCE)
    built, refused, captions = [], [], []
    for role in pack.roles:
        for variant, region, component, style, call in calls(pack, role, mode, str(picture)):
            s = d.add(role, "Tools come back mended", notes="Say it.", variant=variant)
            try:
                call(s)
            except DoesNotFit:
                d._slides.pop()
                refused.append((role, variant, region, component))
                continue
            except PenError as exc:  # BODY in a caption style: not a legal call
                assert "sets captions only" in str(exc), exc
                d._slides.pop()
                captions.append((role, variant, region, style))
                continue
            built.append((role, variant, region, component, style))
    kinds = {"text", "bullets", "table", "figure", "chart_bar", "image", "attribution"}
    assert {c for *_, c, _style in built} == kinds
    assert all(c == "figure" for *_, c in refused), refused
    assert {style for *_, style in captions} == {"label"}  # 14 pt / 10 pt, below the minimum
    d.save(str(tmp_path / "sweep.pptx"))
    proc = keyline(
        "lint", tmp_path / "sweep.pptx", "--mode", mode, "--pack", "swiss", "--voice", voice,
        "--json",
    )  # fmt: skip
    findings = json.loads(proc.stdout)
    assert [f for f in findings if f["severity"] == "error"] == []
    assert [f for f in findings if f["rule"] == "body-too-small"] == []


@pytest.mark.parametrize("mode", ["presented", "read"])
def test_a_style_below_the_body_minimum_sets_captions_only(mode):
    d = Deck(pack="swiss", mode=mode, voice="neutral")
    s = d.add("section", "How the pack sets a slide")
    with pytest.raises(PenError, match="text in the label style has 7 words; at most 5"):
        s.text("one two six ten red map sea", style="label")
    s.text("one two six ten red", style="label")  # five words: a caption
    body = d.add("statement", "Every value comes from the pack")
    body.text("one two six ten red map sea", style="lede")  # at or above the minimum
