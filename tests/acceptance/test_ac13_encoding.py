"""AC-13: under PYTHONIOENCODING=cp1252, d25 exits 2 with valid UTF-8 JSON, byte-equal to
the output under a UTF-8 locale. kpi-recipe slide 4 shows "measured": 0.252 (A-16)."""

import json
import os

from tests.acceptance._cli import keyline
from tests.conftest import FOREIGN, GOLDEN

D25 = FOREIGN / "stress" / "d25_ppx_localized_names.pptx"


def _env(encoding):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = encoding
    env.pop("PYTHONUTF8", None)
    return env


def test_cp1252_json_is_utf8_and_equal_to_utf8_locale():
    cp = keyline("lint", D25, "--json", env=_env("cp1252"))
    utf = keyline("lint", D25, "--json", env=_env("utf-8"))
    assert cp.returncode == 2, cp.stderr.decode("utf-8", "replace")
    assert utf.returncode == 2
    assert b"Traceback" not in cp.stderr
    assert cp.stdout == utf.stdout
    names = {f["shape_name"] for f in json.loads(cp.stdout.decode("utf-8"))}
    assert {"タイトル 2", "Textfeld 3 – Übersicht", "Box 🚀 4"} <= names


def test_ascii_stream_does_not_crash_either():
    proc = keyline("lint", D25, "--json", env=_env("ascii"))
    assert proc.returncode == 2 and b"Traceback" not in proc.stderr
    json.loads(proc.stdout.decode("utf-8"))


def test_ratios_have_three_decimals():
    proc = keyline("lint", GOLDEN / "kpi-recipe.pptx", "--json")
    bands = [f for f in json.loads(proc.stdout) if f["rule"] == "dead-band" and f["slide"] == 4]
    assert sorted(f["measured"] for f in bands) == [0.252, 0.423]
    assert {f["threshold"] for f in bands} == {0.25}
    assert any("(25.2% of slide height)" in f["message"] for f in bands)
