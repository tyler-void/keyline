"""Thresholds per mode, loaded from thresholds.toml (stdlib tomllib, D-012).

Every value becomes an exact Fraction (floats via their shortest repr), so boundary
comparisons such as 36 pt vs 2.0 × 18 pt are exact.
"""

from __future__ import annotations

import tomllib
import unicodedata
from dataclasses import dataclass
from fractions import Fraction
from importlib import resources
from pathlib import Path
from typing import Any

from keyline.units import to_fraction

MODES = ("presented", "read")

KEYS = (
    "body_min_pt",
    "caption_exempt_words",
    "title_ratio_min",
    "edge_margin_cm",
    "edge_margin_tolerance_cm",
    "dead_band_ratio",
    "contrast_normal",
    "contrast_large",
    "large_text_pt",
    "large_text_bold_pt",
    "font_family_max",
    "off_slide_tolerance_cm",
    "background_coverage_min",
    "backing_coverage_min",
    "box_overlap_min_cm",
    "kpi_numeral_min_pt",
    "kpi_numeral_max_words",
    "underline_max_height_cm",
    "underline_max_gap_cm",
    "underline_max_left_offset_cm",
    "underline_max_width_ratio",
    "card_min_count",
    "card_size_tolerance",
    "card_row_tolerance_cm",
    "card_gap_tolerance_cm",
    "card_center_tolerance",
    # spec 002 §3.2, per mode
    "title_words_max",
    "source_min_pt",
    "reads_max",
    "bullets_max",
    "numerals_max",
    # spec 002 §3.2, common
    "source_prefixes",
    "note_prefixes",
    "neutral_chroma_max",
    "cream_lightness_min",
    "cream_chroma_max",
    "cream_hue_min",
    "cream_hue_max",
    "cream_slide_ratio",
    "terracotta_hue_min",
    "terracotta_hue_max",
    "terracotta_sat_min",
    "terracotta_sat_max",
    "terracotta_light_min",
    "terracotta_light_max",
    "closing_cliches",
    "mood_words",
    "statement_min_slides",
    # spec 002 B-8.3, common
    "portable_fonts",
)

# Keys whose value is a list of strings (NFC-normalised and casefolded on load); every
# other key is a number.
LIST_KEYS = frozenset({"source_prefixes", "note_prefixes", "closing_cliches", "mood_words"})
# Keys whose value is a list of { family, metric_twin } tables (B-8.3, plan Q-38), kept as
# written: a tuple of (family, metric_twin) pairs.
FONT_KEYS = frozenset({"portable_fonts"})


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Config:
    mode: str
    calibrated: bool
    values: dict[str, Fraction | tuple[str, ...] | tuple[tuple[str, str], ...]]

    def __getattr__(self, name: str) -> Any:
        try:
            return self.values[name]
        except KeyError:
            raise AttributeError(name) from None

    def as_int(self, name: str) -> int:
        v = self.values[name]
        if v.denominator != 1:
            raise ConfigError(f"{name} must be an integer, got {v}")
        return int(v)


def _number(key: str, raw: Any) -> Fraction:
    if isinstance(raw, bool) or not isinstance(raw, int | float):
        raise ConfigError(f"{key} must be a number, got {raw!r}")
    return to_fraction(raw)


def _strings(key: str, raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, list) or not all(isinstance(s, str) and s.strip() for s in raw):
        raise ConfigError(f"{key} must be a list of non-empty strings, got {raw!r}")
    return tuple(unicodedata.normalize("NFC", s).casefold() for s in raw)


def _fonts(key: str, raw: Any) -> tuple[tuple[str, str], ...]:
    bad = ConfigError(f"{key} must be a list of {{ family, metric_twin }} tables, got {raw!r}")
    if not isinstance(raw, list):
        raise bad
    pairs = []
    for item in raw:
        if not isinstance(item, dict) or set(item) != {"family", "metric_twin"}:
            raise bad
        if not all(isinstance(v, str) and v.strip() for v in item.values()):
            raise bad
        pairs.append((item["family"].strip(), item["metric_twin"].strip()))
    folded = [f.casefold() for f, _ in pairs]
    if len(set(folded)) != len(folded):
        raise ConfigError(f"{key} lists a family twice")
    return tuple(pairs)


def _value(key: str, raw: Any) -> Fraction | tuple:
    if key in FONT_KEYS:
        return _fonts(key, raw)
    return _strings(key, raw) if key in LIST_KEYS else _number(key, raw)


def parse(data: dict[str, Any], mode: str) -> Config:
    if mode not in MODES:
        raise ConfigError(f"unknown mode {mode!r}; expected one of {', '.join(MODES)}")
    calibrated = data.get("calibrated")
    if not isinstance(calibrated, bool):
        raise ConfigError("calibrated must be true or false")
    allowed = {"calibrated", "common", *MODES}
    extra = set(data) - allowed
    if extra:
        raise ConfigError(f"unknown top-level keys: {', '.join(sorted(extra))}")
    merged: dict[str, Fraction | tuple] = {}
    for table in ("common", mode):
        for key, raw in data.get(table, {}).items():
            if key not in KEYS:
                raise ConfigError(f"unknown key [{table}].{key}")
            merged[key] = _value(key, raw)
    missing = [k for k in KEYS if k not in merged]
    if missing:
        raise ConfigError(f"missing keys for mode {mode}: {', '.join(missing)}")
    return Config(mode=mode, calibrated=calibrated, values=merged)


def load(mode: str = "presented", path: Path | None = None) -> Config:
    if path is None:
        text = resources.files("keyline").joinpath("thresholds.toml").read_text("utf-8")
    else:
        text = Path(path).read_text("utf-8")
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"thresholds file is not valid TOML: {exc}") from exc
    return parse(data, mode)
