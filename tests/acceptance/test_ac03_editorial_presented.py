"""AC-3: editorial.pptx in presented mode."""

import pytest

from tests.acceptance._golden import has, run


@pytest.fixture(scope="module")
def result():
    return run("editorial.pptx", "presented")


@pytest.mark.parametrize(
    ("shape", "pt"), [("d1", 12.5), ("d2", 12.5), ("d3", 12.5), ("verdicttx", 11.0)]
)
def test_body_too_small(result, shape, pt):
    (f,) = has(result[1], "body-too-small", shape=shape, severity="warning")
    assert (f["measured"], f["threshold"]) == (pt, 18.0)
