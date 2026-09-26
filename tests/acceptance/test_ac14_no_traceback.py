"""AC-14: o51–o56 and d27 produce no traceback. The d27 reason names Strict. An injected
exception inside a rule gives the one-line internal-error message and exit 1 (A-17)."""

import dataclasses
import re

import pytest

from keyline import cli, registry
from keyline.rules import load_all
from tests.acceptance._cli import keyline
from tests.conftest import FOREIGN, GOLDEN

STRESS = FOREIGN / "stress"
ODD = sorted(STRESS.glob("o5*.pptx"))


def test_the_six_oddities_are_present():
    assert [p.name[:3] for p in ODD] == ["o51", "o52", "o53", "o54", "o55", "o56"]


@pytest.mark.parametrize("deck", ODD, ids=[p.stem for p in ODD])
def test_oddities_lint_without_traceback(deck):
    proc = keyline("lint", deck, "--json")
    assert b"Traceback" not in proc.stderr
    assert proc.returncode in (0, 2), proc.stderr.decode()


def test_unparseable_values_become_advisories():
    proc = keyline("lint", STRESS / "o55_cxn_id_word.pptx")
    assert b'could not parse stCxn@id="first"; the value was dropped' in proc.stderr
    proc = keyline("lint", STRESS / "o56_ext_40_digits.pptx")
    assert b"could not parse ext@cx=" in proc.stderr


def test_strict_package_is_named():
    proc = keyline("lint", STRESS / "d27_strict_from_ppx.pptx")
    assert proc.returncode == 1
    lines = proc.stderr.decode().splitlines()
    assert len(lines) == 1
    assert "Strict Open XML (ISO/IEC 29500 Strict) is not supported yet" in lines[0]


def _boom(deck, cfg):
    raise ZeroDivisionError("injected")


def test_injected_rule_exception_is_one_line(monkeypatch, capsys):
    load_all()
    spec = registry.get("dead-band")
    monkeypatch.setitem(registry._REGISTRY, "dead-band", dataclasses.replace(spec, check=_boom))
    code = cli.main(["lint", str(GOLDEN / "kpi-recipe.pptx"), "--json"])
    err = capsys.readouterr().err.splitlines()
    assert code == 1
    assert err == [
        "keyline: internal error while reading rule dead-band: ZeroDivisionError; "
        "rerun with --traceback and report it"
    ]


def test_traceback_flag_prints_the_trace(monkeypatch, capsys):
    load_all()
    spec = registry.get("dead-band")
    monkeypatch.setitem(registry._REGISTRY, "dead-band", dataclasses.replace(spec, check=_boom))
    code = cli.main(["lint", str(GOLDEN / "kpi-recipe.pptx"), "--traceback"])
    err = capsys.readouterr().err
    assert code == 1
    assert "Traceback (most recent call last)" in err and "ZeroDivisionError: injected" in err
    assert re.search(r"keyline: internal error while reading rule dead-band", err)
