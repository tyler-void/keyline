import pytest

from keyline.roles import ROLES, parse


@pytest.mark.parametrize("role", ROLES)
def test_every_role_parses(role):
    assert parse(f"keyline:{role}") == (role, None)


def test_variant():
    assert parse("keyline:evidence:two-col") == ("evidence", "two-col")


@pytest.mark.parametrize(
    "name",
    [
        None,
        "",
        "Blank",
        "keyline:",
        "keyline:agenda",
        "Keyline:cover",
        "keyline:cover:",
        "keyline:cover:Two",
        "keyline:cover:a:b",
        " keyline:cover",
        "keyline:cover ",
    ],
)
def test_anything_else_has_no_role(name):
    assert parse(name) == (None, None)
