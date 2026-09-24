import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
GOLDEN = FIXTURES / "golden"
RULES = FIXTURES / "rules"
FOREIGN = FIXTURES / "foreign"

HAS_OFFICECLI = shutil.which("officecli") is not None


def pytest_collection_modifyitems(config, items):
    skip = pytest.mark.skip(reason="officecli is not installed")
    for item in items:
        if "officecli" in item.keywords and not HAS_OFFICECLI:
            item.add_marker(skip)
