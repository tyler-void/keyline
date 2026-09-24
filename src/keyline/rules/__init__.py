"""Rule modules. Importing this package registers every rule."""

from importlib import import_module

RULE_MODULES = (
    "off_slide",
    "edge_margin",
    "dead_band",
    "box_overlap",
    "body_too_small",
    "title_not_dominant",
)


def load_all() -> None:
    for name in RULE_MODULES:
        import_module(f"keyline.rules.{name}")
