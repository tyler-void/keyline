"""Spec 002 AC-13(a) with B-8.11: for every portable family's twin (regular and bold)
whose TTF is present, the estimator's width of each committed test string is between
0.995× and 1.25× Pillow's (BASIC layout at 1000 px, scaled). Twins that are absent skip by
name; a string with characters the twin lacks is skipped for that twin (its estimate uses
the maximum advance, and Pillow would measure .notdef), and named."""

import shutil
import subprocess
import tomllib
from fractions import Fraction as F

import pytest

from keyline.config import load as load_config
from keyline.fit import WEIGHTS, Setting, missing, width
from tests.conftest import FIXTURES

STRINGS = tomllib.loads((FIXTURES / "fit/strings.toml").read_text("utf-8"))["string"]
FAMILIES = load_config().portable_fonts
SIZE = F(24)


def twin_file(family, twin, weight):
    if shutil.which("fc-match") is None:
        return None
    style = "Bold" if weight == "bold" else "Regular"
    pattern = f"{family}:style={style}"
    got = subprocess.run(["fc-match", "-f", "%{family}", pattern], capture_output=True, text=True)
    if got.stdout.split(",")[0].strip().casefold() != twin.casefold():
        return None
    out = subprocess.run(["fc-match", "-f", "%{file}", pattern], capture_output=True, text=True)
    return out.stdout.strip()


def ratios(family, twin, weight):
    """(name, ratio, latin) per string, and the names skipped for missing characters."""
    from PIL import ImageFont

    path = twin_file(family, twin, weight)
    if path is None:
        return None, None
    font = ImageFont.truetype(path, 1000, layout_engine=ImageFont.Layout.BASIC)
    out, skipped = [], []
    for s in STRINGS:
        setting = Setting(
            family, weight, SIZE, caps=s.get("caps", False), tracking=F(str(s.get("tracking", 0)))
        )
        if missing(setting, s["text"]):
            skipped.append(s["name"])
            continue
        shown = s["text"].upper() if setting.caps else s["text"]
        pillow = F(font.getlength(shown)) / 1000 * SIZE + setting.tracking * SIZE * len(shown)
        out.append((s["name"], float(width(setting, s["text"]) / pillow), s.get("latin", False)))
    return out, skipped


@pytest.mark.parametrize(("family", "twin"), FAMILIES)
@pytest.mark.parametrize("weight", WEIGHTS)
def test_estimate_against_pillow(family, twin, weight):
    pytest.importorskip("PIL")
    rows, skipped = ratios(family, twin, weight)
    if rows is None:
        pytest.skip(f"{twin} {weight} is not installed")
    for name, ratio, _latin in rows:
        assert 0.995 <= ratio <= 1.25, (twin, weight, name, ratio)
    if family == "Cambria":
        assert skipped == ["vietnamese", "vietnamese-caps"]  # Caladea lacks them (audit 04)
    else:
        assert skipped == []
