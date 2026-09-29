"""Audit 02 FX-5 (amendment B-12 item 5 and the one-line rule): every value in pack.toml,
a voice, a brief and an evidence file, replaced by a value of another type or removed,
gives a one-line schema error or loads; never another exception."""

import copy
import math
import tomllib

import pytest

from keyline import brief as brief_mod
from keyline.brief import BriefError
from keyline.packs import BUNDLED, PackError, _build, resolve
from keyline.packs.voices import VoiceError, parse
from tests.conftest import FIXTURES

SWISS = BUNDLED / "swiss"
PACK = resolve("swiss")
ALTERNATIVES = [0, -1, 1.5, math.nan, math.inf, True, "", "x", [], [1], ["x"], {}, {"a": 1}]
REMOVE = object()


def _paths(node, prefix=()):
    if prefix:
        yield prefix
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _paths(value, (*prefix, key))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _paths(value, (*prefix, i))


def _mutants(data):
    for path in _paths(data):
        for value in [REMOVE, *ALTERNATIVES]:
            mutant = copy.deepcopy(data)
            parent = mutant
            for key in path[:-1]:
                parent = parent[key]
            if value is REMOVE:
                del parent[path[-1]]
            else:
                parent[path[-1]] = copy.deepcopy(value)
            yield path, value, mutant


def _read(path):
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _check(load, errors, data):
    failures = []
    count = 0
    for path, value, mutant in _mutants(data):
        count += 1
        try:
            load(mutant)
        except errors as exc:
            if "\n" in str(exc):
                failures.append((path, value, "two lines"))
        except Exception as exc:
            failures.append((path, value, f"{type(exc).__name__}: {exc}"))
    return count, failures


def test_pack_toml_mutations():
    count, failures = _check(lambda d: _build(d, SWISS), PackError, _read(SWISS / "pack.toml"))
    assert count > 3000 and failures[:10] == [], len(failures)


def test_voice_mutations():
    data = _read(SWISS / "voices/neutral.toml")
    count, failures = _check(lambda d: parse(d, PACK, where="voice"), VoiceError, data)
    assert count > 200 and failures[:10] == [], len(failures)


@pytest.mark.parametrize("target", ["valid.brief.toml", "evidence.toml", "extra-evidence.toml"])
def test_brief_and_evidence_mutations(target, monkeypatch):
    brief_path = FIXTURES / "briefs/valid.brief.toml"
    original = brief_mod._read_toml
    state = {}

    def fake_read(path, what):
        if path.name == target:
            return copy.deepcopy(state["data"])
        return original(path, what)

    monkeypatch.setattr(brief_mod, "_read_toml", fake_read)

    def load(mutant):
        state["data"] = mutant
        brief_mod.load(brief_path)

    count, failures = _check(load, BriefError, _read(FIXTURES / "briefs" / target))
    assert count > 50 and failures[:10] == [], len(failures)
