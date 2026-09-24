"""The provided golden fixtures are never edited (spec §8, constitution VI)."""

import hashlib
from pathlib import Path

from tests.conftest import GOLDEN

HASHES = Path(__file__).with_name("golden_hashes.txt")


def test_golden_fixtures_match_recorded_hashes():
    lines = [ln.split() for ln in HASHES.read_text().splitlines() if ln.strip()]
    assert {name for _, name in lines} >= {"kpi-recipe.pptx", "editorial.pptx"}
    for digest, name in lines:
        assert hashlib.sha256((GOLDEN / name).read_bytes()).hexdigest() == digest, name
