"""Rule modules. Importing this package registers every rule."""

from importlib import import_module

RULE_MODULES = ()


def load_all() -> None:
    for name in RULE_MODULES:
        import_module(f"keyline.rules.{name}")
