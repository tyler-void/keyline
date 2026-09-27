"""Style packs (spec 002 §5): load by name or directory, validate, list.

A pack is a directory holding `pack.toml`, `README.md`, one template per mode and `src/`.
Everything in `pack.toml` is data; this module only checks that it is consistent and
derives what other code needs from it (region boxes in EMU, colours as hex). It never
imports python-pptx.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

from keyline.config import MODES
from keyline.geom import Box
from keyline.roles import ROLES
from keyline.roles import parse as parse_layout

BUNDLED = Path(__file__).resolve().parent
COMPONENTS = (
    "text",
    "bullets",
    "figure",
    "table",
    "chart_bar",
    "image",
    "attribution",
    "source",
    "note",
)
WEIGHTS = ("regular", "bold")
SLIDE_W, SLIDE_H = 12192000, 6858000  # 16:9 (§5.3)


class PackError(ValueError):
    """The pack cannot be found or is inconsistent; the message is one line."""


@dataclass(frozen=True)
class Style:
    name: str
    size_pt: Fraction
    weight: str
    color: dict[str, str]  # surface name -> palette name
    caps: bool = False
    tracking: Fraction = Fraction(0)
    line_spacing: Fraction = Fraction(1)
    space_before_pt: Fraction = Fraction(0)
    space_after_pt: Fraction = Fraction(0)
    bullet_indent_emu: int = 0
    bullet_marker: str = ""

    @property
    def size_hundredths(self) -> int:
        """The size as OOXML `sz` (1/100 pt), which is how lint stores run sizes."""
        return int(self.size_pt * 100)


@dataclass(frozen=True)
class Surface:
    name: str
    background: str  # palette name
    text: tuple[str, ...]  # palette names
    accent: str  # palette name


@dataclass(frozen=True)
class Role:
    name: str
    surface: str
    title: str  # style name
    layouts: tuple[str, ...]
    components: dict[str, dict[str, tuple[str, ...]]]  # mode -> component -> styles


@dataclass(frozen=True)
class Region:
    col: int
    span: int
    row: int
    rows: int


@dataclass(frozen=True)
class Grid:
    columns: int
    gutter_emu: int
    margin_x_emu: int
    margin_y_emu: int
    row_emu: int
    rows: int

    @property
    def column_emu(self) -> int:
        content = SLIDE_W - 2 * self.margin_x_emu - (self.columns - 1) * self.gutter_emu
        return content // self.columns

    def box(self, r: Region) -> Box:
        x = self.margin_x_emu + (r.col - 1) * (self.column_emu + self.gutter_emu)
        w = r.span * self.column_emu + (r.span - 1) * self.gutter_emu
        return Box(x, self.margin_y_emu + r.row * self.row_emu, w, r.rows * self.row_emu)


@dataclass(frozen=True)
class Pack:
    name: str
    version: str
    directory: Path
    modes: tuple[str, ...]
    templates: dict[str, str]
    fonts: tuple[str, ...]
    palette: dict[str, str]  # name -> "RRGGBB" (upper case)
    accents: tuple[str, ...]
    accent_budget: int
    containers: str
    alignment: str
    accepted: tuple[tuple[str, str], ...]  # (rule id, reason)
    surfaces: dict[str, Surface]
    grid: Grid
    keyline_rule: dict[str, Any]
    styles: dict[str, dict[str, Style]]  # mode -> style name -> Style
    roles: dict[str, Role]
    regions: dict[str, dict[str, Region]]  # layout name -> region name -> Region
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def hex(self, palette_name: str) -> str:
        return self.palette[palette_name]

    def accent_hexes(self) -> set[str]:
        return {self.palette[n] for n in self.accents}

    def template(self, mode: str) -> Path:
        path = self.directory / self.templates[mode]
        if not path.is_file():
            raise PackError(f"pack {self.name}: template for {mode} is missing: {path.name}")
        return path

    def region_box(self, layout: str, region: str) -> Box:
        return self.grid.box(self.regions[layout][region])

    def scale(self, mode: str) -> set[int]:
        """The mode's type scale as OOXML sizes (1/100 pt)."""
        return {s.size_hundredths for s in self.styles[mode].values()}


# ---------------------------------------------------------------------------------------
# loading


def bundled() -> list[str]:
    """Names of the packs shipped with keyline."""
    return sorted(p.parent.name for p in BUNDLED.glob("*/pack.toml"))


def resolve(name_or_dir: str | Path, base: Path | None = None) -> Pack:
    """A pack directory (relative to `base` when given) or a bundled pack name."""
    candidate = Path(name_or_dir)
    if not candidate.is_absolute() and base is not None:
        candidate = base / candidate
    if (candidate / "pack.toml").is_file():
        return load(candidate)
    name = str(name_or_dir)
    if "/" not in name and "\\" not in name and (BUNDLED / name / "pack.toml").is_file():
        return load(BUNDLED / name)
    raise PackError(f"pack not found: {name_or_dir}")


def load(directory: str | Path) -> Pack:
    directory = Path(directory).resolve()
    try:
        data = tomllib.loads((directory / "pack.toml").read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PackError(f"no pack.toml in {directory}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise PackError(f"{directory.name}/pack.toml is not valid TOML: {exc}") from exc
    return _build(data, directory)


def _fail(where: str, why: str) -> PackError:
    return PackError(f"pack.toml: {where}: {why}")


def _get(d: dict, key: str, kind: type | tuple, where: str) -> Any:
    if key not in d:
        raise _fail(where, f"missing key {key!r}")
    value = d[key]
    if kind is int and isinstance(value, bool):
        raise _fail(f"{where}.{key}", "must be an integer")
    if not isinstance(value, kind):
        raise _fail(f"{where}.{key}", f"must be {getattr(kind, '__name__', kind)}")
    return value


def _number(value: Any, where: str) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise _fail(where, "must be a number")
    return Fraction(repr(value)) if isinstance(value, float) else Fraction(value)


def _names(values: Any, known: dict | set, where: str) -> tuple[str, ...]:
    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        raise _fail(where, "must be a list of strings")
    for v in values:
        if v not in known:
            raise _fail(where, f"unknown name {v!r}")
    return tuple(values)


def _hex(value: Any, where: str) -> str:
    if not isinstance(value, str) or len(value) != 6:
        raise _fail(where, "must be RRGGBB")
    try:
        int(value, 16)
    except ValueError as exc:
        raise _fail(where, "must be RRGGBB") from exc
    return value.upper()


def _build(data: dict, directory: Path) -> Pack:
    if data.get("schema") != 1:
        raise _fail("schema", "must be 1")
    name = _get(data, "name", str, "top level")
    modes = _names(_get(data, "modes", list, "top level"), set(MODES), "modes")
    templates = _get(data, "templates", dict, "top level")
    for mode in modes:
        if not isinstance(templates.get(mode), str):
            raise _fail(f"templates.{mode}", "missing")

    palette = {k: _hex(v, f"palette.{k}") for k, v in _get(data, "palette", dict, "top").items()}
    accents = _names(_get(data, "accents", list, "top level"), palette, "accents")
    budget = _get(data, "accent_budget", int, "top level")
    containers = _get(data, "containers", str, "top level")
    if containers not in ("rules", "boxes", "none"):
        raise _fail("containers", "must be rules, boxes or none")
    alignment = _get(data, "alignment", str, "top level")
    if alignment not in ("left", "center"):
        raise _fail("alignment", "must be left or center")
    accepted = []
    for i, item in enumerate(_get(data, "accepted", list, "top level")):
        if not isinstance(item, dict) or not {"rule", "reason"} <= set(item):
            raise _fail(f"accepted[{i}]", "must be { rule, reason }")
        accepted.append((str(item["rule"]), str(item["reason"])))

    surfaces = {}
    for sname, s in _get(data, "surfaces", dict, "top level").items():
        where = f"surfaces.{sname}"
        surfaces[sname] = Surface(
            sname,
            _names([_get(s, "background", str, where)], palette, f"{where}.background")[0],
            _names(_get(s, "text", list, where), palette, f"{where}.text"),
            _names([_get(s, "accent", str, where)], palette, f"{where}.accent")[0],
        )

    g = _get(data, "grid", dict, "top level")
    grid = Grid(
        *(
            _get(g, k, int, "grid")
            for k in ("columns", "gutter_emu", "margin_x_emu", "margin_y_emu", "row_emu", "rows")
        )
    )
    if grid.margin_y_emu * 2 + grid.rows * grid.row_emu != SLIDE_H:
        raise _fail("grid", "margins and rows must fill the slide height exactly")
    if (
        grid.column_emu * grid.columns
        + (grid.columns - 1) * grid.gutter_emu
        + 2 * grid.margin_x_emu
        != SLIDE_W
    ):
        raise _fail("grid", "columns, gutters and margins must fill the slide width exactly")
    rule = _get(data, "keyline_rule", dict, "top level")
    _names([_get(rule, "color", str, "keyline_rule")], palette, "keyline_rule.color")

    styles: dict[str, dict[str, Style]] = {}
    raw_styles = _get(data, "styles", dict, "top level")
    for mode in modes:
        styles[mode] = {}
        for sname, s in _get(raw_styles, mode, dict, "styles").items():
            styles[mode][sname] = _style(sname, s, f"styles.{mode}.{sname}", palette, surfaces)
    if len({frozenset(v) for v in styles.values()}) > 1:
        raise _fail("styles", "every mode must define the same styles")

    roles = {}
    for rname, r in _get(data, "roles", dict, "top level").items():
        roles[rname] = _role(rname, r, modes, styles, surfaces)
    missing = set(ROLES) - set(roles)
    if missing:
        raise _fail("roles", f"missing roles: {', '.join(sorted(missing))}")

    regions: dict[str, dict[str, Region]] = {}
    for lname, rs in _get(data, "regions", dict, "top level").items():
        regions[lname] = {k: _region(v, f"regions.{lname}.{k}", grid) for k, v in rs.items()}
        if "title" not in regions[lname]:
            raise _fail(f"regions.{lname}", "needs a title region")
        _no_overlap(regions[lname], f"regions.{lname}")
    for role in roles.values():
        for layout in role.layouts:
            if layout not in regions:
                raise _fail(f"roles.{role.name}.layouts", f"no regions for {layout}")

    return Pack(
        name=name,
        version=_get(data, "version", str, "top level"),
        directory=directory,
        modes=modes,
        templates={m: templates[m] for m in modes},
        fonts=_names(_get(data, "fonts", list, "top level"), _AnyName(), "fonts"),
        palette=palette,
        accents=accents,
        accent_budget=budget,
        containers=containers,
        alignment=alignment,
        accepted=tuple(accepted),
        surfaces=surfaces,
        grid=grid,
        keyline_rule=rule,
        styles=styles,
        roles=roles,
        regions=regions,
        raw=data,
    )


class _AnyName(set):
    def __contains__(self, item: object) -> bool:
        return isinstance(item, str) and bool(item.strip())


def _style(name: str, s: dict, where: str, palette: dict, surfaces: dict) -> Style:
    weight = _get(s, "weight", str, where)
    if weight not in WEIGHTS:
        raise _fail(f"{where}.weight", "must be regular or bold")
    color = _get(s, "color", dict, where)
    for surface, pname in color.items():
        if surface not in surfaces:
            raise _fail(f"{where}.color", f"unknown surface {surface!r}")
        _names([pname], palette, f"{where}.color.{surface}")
    size = _number(_get(s, "size_pt", (int, float), where), f"{where}.size_pt")
    if size <= 0 or (size * 100).denominator != 1:
        raise _fail(f"{where}.size_pt", "must be positive, in hundredths of a point")
    line_spacing = _number(s.get("line_spacing", 1), f"{where}.line_spacing")
    if line_spacing < 1:
        raise _fail(f"{where}.line_spacing", "must be at least 1.0 (§6.4)")
    return Style(
        name=name,
        size_pt=size,
        weight=weight,
        color=dict(color),
        caps=bool(s.get("caps", False)),
        tracking=_number(s.get("tracking", 0), f"{where}.tracking"),
        line_spacing=line_spacing,
        space_before_pt=_number(s.get("space_before_pt", 0), f"{where}.space_before_pt"),
        space_after_pt=_number(s.get("space_after_pt", 0), f"{where}.space_after_pt"),
        bullet_indent_emu=int(s.get("bullet_indent_emu", 0)),
        bullet_marker=str(s.get("bullet_marker", "")),
    )


def _role(name: str, r: dict, modes: tuple, styles: dict, surfaces: dict) -> Role:
    where = f"roles.{name}"
    if name not in ROLES:
        raise _fail(where, "unknown role")
    surface = _get(r, "surface", str, where)
    if surface not in surfaces:
        raise _fail(f"{where}.surface", f"unknown surface {surface!r}")
    title = _get(r, "title", str, where)
    layouts = tuple(_get(r, "layouts", list, where))
    for layout in layouts:
        if parse_layout(layout)[0] != name:
            raise _fail(f"{where}.layouts", f"{layout!r} is not a {name} layout name")
    comps = _get(r, "components", dict, where)
    components = {}
    for mode in modes:
        if title not in styles[mode]:
            raise _fail(f"{where}.title", f"unknown style {title!r} in {mode}")
        if surface not in styles[mode][title].color:
            raise _fail(f"{where}.title", f"style {title} has no colour on {surface}")
        cm = _get(comps, mode, dict, f"{where}.components")
        components[mode] = {}
        for comp, allowed in cm.items():
            if comp not in COMPONENTS:
                raise _fail(f"{where}.components.{mode}", f"unknown component {comp!r}")
            components[mode][comp] = _names(
                allowed, styles[mode], f"{where}.components.{mode}.{comp}"
            )
            for style_name in allowed:
                if surface not in styles[mode][style_name].color:
                    raise _fail(
                        f"{where}.components.{mode}.{comp}",
                        f"style {style_name} has no colour on {surface}",
                    )
    return Role(name, surface, title, layouts, components)


def _region(v: Any, where: str, grid: Grid) -> Region:
    if not isinstance(v, dict):
        raise _fail(where, "must be { col, span, row, rows }")
    r = Region(*(_get(v, k, int, where) for k in ("col", "span", "row", "rows")))
    if r.col < 1 or r.span < 1 or r.col + r.span - 1 > grid.columns:
        raise _fail(where, "columns outside the grid")
    if r.row < 0 or r.rows < 1 or r.row + r.rows > grid.rows:
        raise _fail(where, "rows outside the grid")
    return r


def _no_overlap(regions: dict[str, Region], where: str) -> None:
    items = list(regions.items())
    for i, (a_name, a) in enumerate(items):
        for b_name, b in items[i + 1 :]:
            cols = a.col <= b.col + b.span - 1 and b.col <= a.col + a.span - 1
            rows = a.row < b.row + b.rows and b.row < a.row + a.rows
            if cols and rows:
                raise _fail(where, f"regions {a_name} and {b_name} overlap (§6.3)")
