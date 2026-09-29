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
    # spec 002 §3.4
    "claude_look_palette",
    "title_too_long",
    "closing_cliche",
    "off_palette_color",
    "off_scale_size",
    "off_pack_font",
    "accent_overuse",
)


def load_all() -> None:
    # The adapter registers its own advisory findings (P-15); the brief module registers
    # the §4.3 and voice entries, which `keyline brief` reports (spec 002 §3.4).
    import_module("keyline.ooxml.adapter")
    import_module("keyline.brief")
    import_module("keyline.briefcheck")
    import_module("keyline.validate")  # ooxml-invalid: `check` only (plan Q-12)
    for name in RULE_MODULES:
        import_module(f"keyline.rules.{name}")
