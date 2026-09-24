"""Rule modules. Importing this package registers every rule."""

from importlib import import_module

RULE_MODULES = (
    "off_slide",
    "edge_margin",
    "dead_band",
    "box_overlap",
    "body_too_small",
    "title_not_dominant",
    "text_contrast",
    "notes_missing",
    "font_count",
    "title_underline",
    "equal_card_row",
)


def load_all() -> None:
    for name in RULE_MODULES:
        import_module(f"keyline.rules.{name}")
