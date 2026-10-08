"""Audit 06 FX-29 (amendment B-25 item 7): the templates set the theme's complex-script
(`cs`) fonts to the voice's display and text families, and every run the pen writes, like
the templates' text styles, names the theme's complex-script slot (+mj-cs, +mn-cs) beside
its Latin one. LibreOffice then sets Hebrew in the voice's twin, which the estimator
measured, rather than in its default CTL font (the audit saw a Times New Roman statement
title +90.6 px past its region). Hebrew stays outside the measured set, so the pen warns.
Repro: evidence/audit06-repros/t_ctl.py."""

import re
import zipfile

import pytest

from keyline.fit import load_table
from keyline.packs import resolve
from keyline.packs.templates import build
from tests.acceptance.m2 import _lo

pytest.importorskip("pptx")

from keyline.pen import Deck, DoesNotFit

HEBREW = [
    "".join(map(chr, (0x05E9, 0x05DC, 0x05D5, 0x05DD))),
    "".join(map(chr, (0x05E2, 0x05D5, 0x05DC, 0x05DD))),
]


@pytest.mark.parametrize("voice", ["neutral", "field"])
@pytest.mark.parametrize("mode", ["presented", "read"])
def test_the_theme_sets_the_voices_families_for_complex_scripts(voice, mode):
    import io

    pack = resolve("swiss")
    v = pack.voice(voice)
    theme = next(
        zipfile.ZipFile(io.BytesIO(build(pack, v, mode))).read(n).decode()
        for n in zipfile.ZipFile(io.BytesIO(build(pack, v, mode))).namelist()
        if n.startswith("ppt/theme/")
    )
    major = re.search(r"<a:majorFont>(.*?)</a:majorFont>", theme).group(1)
    minor = re.search(r"<a:minorFont>(.*?)</a:minorFont>", theme).group(1)
    assert (
        f'<a:cs typeface="{v.display}"/>' in major and f'<a:latin typeface="{v.display}"/>' in major
    )
    assert f'<a:cs typeface="{v.text}"/>' in minor and f'<a:latin typeface="{v.text}"/>' in minor


def test_runs_and_styles_name_the_complex_script_slot(tmp_path):
    d = Deck(pack="swiss", mode="presented", voice="neutral")
    d.add("evidence", "A headline").text("Body text")
    d.save(str(tmp_path / "d.pptx"))
    z = zipfile.ZipFile(tmp_path / "d.pptx")
    slide = z.read("ppt/slides/slide1.xml").decode()
    assert slide.count('<a:latin typeface="+mj-lt"/><a:cs typeface="+mj-cs"/>') == 1
    assert slide.count('<a:latin typeface="+mn-lt"/><a:cs typeface="+mn-cs"/>') == 1
    master = z.read("ppt/slideMasters/slideMaster1.xml").decode()
    assert master.count('typeface="+mn-lt"/>') == master.count('<a:cs typeface="+mn-cs"/>')


def longest(voice, role):
    words, best = HEBREW * 60, None
    for n in range(1, len(words)):
        text = " ".join(words[:n])
        try:
            Deck(pack="swiss", mode="presented", voice=voice).add(role, text)
        except DoesNotFit:
            return best
        best = text
    raise AssertionError("no headline was refused")


@_lo.needs_lo("Times New Roman", "Arial", "Courier New")
def test_hebrew_is_set_in_the_twin_and_stays_in_its_region(tmp_path, capsys):
    pack = resolve("swiss")
    for family in ("Times New Roman", "Arial", "Courier New"):
        voice = _lo.voice_file(tmp_path, family)
        for role in ("statement", "evidence"):
            d = Deck(pack="swiss", mode="presented", voice=voice)
            d.add(role, longest(voice, role))
            path = tmp_path / f"{family}-{role}.pptx"
            d.save(str(path))
            assert "outside the measured set" in capsys.readouterr().err  # B-25: a warning
            (page,) = _lo.chars(path, tmp_path / f"lo-{family}-{role}")
            title = _lo.region_pt(pack, pack.roles[role].layouts[0], "title")
            assert max(c[4] for c in page) <= title[3] + 1.5, (family, role)
            assert min(c[2] for c in page) >= title[1] - 30, (family, role)  # not pushed up
            twin = load_table(family, "bold").twin.replace(" ", "")
            (used,) = _lo.fonts(path, tmp_path / f"fonts-{family}-{role}")
            assert used and all(name.startswith(twin) for name in used), (family, used)
