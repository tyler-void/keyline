"""Style packs (spec 002 §5, amendment B-8): load by name or directory, validate, list.

A pack is one **system** plus **voices**. The system is a directory holding `pack.toml`,
`README.md`, `voices/` and `src/`; `pack.toml` names colours by role (`palette_roles`)
and fonts as display or text, and a voice (`keyline.packs.voices`) gives the values.
Everything is data; this module only checks that it is consistent and derives what other
code needs from it (region boxes in EMU). It never imports python-pptx.
"""

from __future__ import annotations

import math
import re
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
FONT_SLOTS = ("display", "text")
THEME_SLOTS = (
    "dk1",
    "lt1",
    "dk2",
    "lt2",
    "accent1",
    "accent2",
    "accent3",
    "accent4",
    "accent5",
    "accent6",
    "hlink",
    "folHlink",
)
SLIDE_W, SLIDE_H = 12192000, 6858000  # 16:9 (§5.3)
NAME_RE = re.compile(r"[a-z0-9-]+")  # pack names; matched with fullmatch (B-12 item 1)


class PackError(ValueError):
    """The pack cannot be found or is inconsistent; the message is one line."""


def check_accepted(raw: Any) -> tuple[tuple[str, str], ...]:
    """Amendment B-10: `accepted` (in a pack, a pack voice or an inline voice) may list only
    the `acceptable_rules` of thresholds.toml, each with a non-empty reason. Raises
    ValueError whose text follows the word "accepted"; the caller names the file."""
    from keyline.config import load as load_config
    from keyline.escape import visible

    acceptable = load_config().acceptable_rules
    if not isinstance(raw, list):
        raise ValueError(": must be a list of { rule, reason }")
    out = []
    for i, item in enumerate(raw, 1):
        ok = isinstance(item, dict) and all(
            isinstance(item.get(k), str) for k in ("rule", "reason")
        )
        if not ok:
            raise ValueError(f"[{i}] must be {{ rule, reason }}")
        if item["rule"] not in acceptable:
            names = ", ".join(acceptable)
            raise ValueError(f"[{i}]: {item['rule']!r} cannot be accepted (only {names})")
        if not visible(item["reason"]):  # B-20: not only spaces, controls or zero-width
            raise ValueError(f"[{i}]: the reason must not be empty")
        out.append((item["rule"], item["reason"]))
    return tuple(out)


@dataclass(frozen=True)
class Style:
    name: str
    font: str  # "display" or "text": which of the voice's fonts (plan Q-27)
    size_pt: Fraction
    weight: str
    color: dict[str, str]  # surface name -> palette role
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
    background: str  # palette role
    text: tuple[str, ...]  # palette roles
    accent: str  # palette role


@dataclass(frozen=True)
class Role:
    name: str
    surface: str
    title: str  # style name
    layouts: tuple[str, ...]
    components: dict[str, dict[str, tuple[str, ...]]]  # mode -> component -> styles


ANCHORS = ("t", "b")  # a region's vertical anchor: text from its top, or down on its bottom


@dataclass(frozen=True)
class Region:
    col: int
    span: int
    row: int
    rows: int
    anchor: str = "t"  # audit 05 FX-24


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
    palette_roles: tuple[str, ...]
    accents: tuple[str, ...]  # palette roles
    accent_budget: int
    containers: str
    alignment: str
    accepted: tuple[tuple[str, str], ...]  # (rule id, reason)
    surfaces: dict[str, Surface]
    grid: Grid
    keyline_rule: dict[str, Any]
    theme: dict[str, str]  # theme slot (dk1 … folHlink) -> palette role
    placeholder_idx: dict[str, int]  # non-title region name -> placeholder idx
    placeholder_styles: dict[str, dict[str, str]]  # layout -> region -> style name
    styles: dict[str, dict[str, Style]]  # mode -> style name -> Style
    roles: dict[str, Role]
    regions: dict[str, dict[str, Region]]  # layout name -> region name -> Region
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def voices(self) -> list[str]:
        """Names of the voices shipped with this pack (`voices/*.toml`)."""
        return sorted(p.stem for p in (self.directory / "voices").glob("*.toml"))

    def voice(self, name_or_path: str | Path, base: Path | None = None):
        """A voice of this pack by name, or a voice file (keyline.packs.voices.load)."""
        from keyline.packs.voices import load as load_voice

        return load_voice(self, name_or_path, base)

    def region_box(self, layout: str, region: str) -> Box:
        return self.grid.box(self.regions[layout][region])

    def layout_role(self, layout: str) -> Role:
        return self.roles[parse_layout(layout)[0]]

    def scale(self, mode: str) -> set[int]:
        """The mode's type scale as OOXML sizes (1/100 pt)."""
        return {s.size_hundredths for s in self.styles[mode].values()}


# ---------------------------------------------------------------------------------------
# loading


def bundled() -> list[str]:
    """Names of the packs shipped with keyline."""
    return sorted(p.parent.name for p in BUNDLED.glob("*/pack.toml"))


def is_pack_path(name_or_dir: str | Path) -> bool:
    """A bare name means a bundled pack; a path needs a separator or a leading "." (audit
    02, X-17), so a local directory can never shadow a bundled pack."""
    text = str(name_or_dir)
    return isinstance(name_or_dir, Path) or "/" in text or "\\" in text or text.startswith(".")


def resolve(name_or_dir: str | Path, base: Path | None = None) -> Pack:
    """A bundled pack by name, or a pack directory (relative to `base` when given)."""
    if is_pack_path(name_or_dir):
        candidate = Path(name_or_dir)
        if not candidate.is_absolute() and base is not None:
            candidate = base / candidate
        if _exists(candidate / "pack.toml", f"pack directory {str(name_or_dir)!r}", PackError):
            return load(candidate)
    elif NAME_RE.fullmatch(str(name_or_dir)) and (BUNDLED / str(name_or_dir)).is_dir():
        return load(BUNDLED / str(name_or_dir))
    from keyline.escape import esc

    raise PackError(f"pack not found: {esc(name_or_dir)}")


def _exists(path: Path, what: str, error: type[Exception]) -> bool:
    """Path.exists(), but a path that cannot be examined (a locked directory) is a one-line
    schema error instead of an internal error (B-12 item 7, audit 03 FX-13)."""
    try:
        return path.exists()
    except OSError as exc:
        raise error(f"{what} cannot be read: {exc.strerror or type(exc).__name__}") from exc


def load(directory: str | Path) -> Pack:
    from keyline.brief import read_toml

    directory = Path(directory).resolve()
    data = read_toml(directory / "pack.toml", "pack file", PackError, f"{directory.name}/pack.toml")
    return _build(data, directory)


def _fail(where: str, why: str) -> PackError:
    from keyline.escape import esc

    return PackError(f"pack.toml: {esc(where)}: {why}")


def _table(value: Any, where: str) -> dict:
    """Every table the loader walks is type-checked (amendment B-12 item 5)."""
    if not isinstance(value, dict):
        raise _fail(where, "must be a table")
    return value


def _get(d: dict, key: str, kind: type | tuple, where: str) -> Any:
    _table(d, where)
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
    if isinstance(value, float) and not math.isfinite(value):
        raise _fail(where, "must be a finite number")
    return Fraction(repr(value)) if isinstance(value, float) else Fraction(value)


def _int(d: dict, key: str, where: str, *, minimum: int, default: int | None = None) -> int:
    if default is not None and key not in d:
        return default
    value = _get(d, key, int, where)
    if value < minimum:
        raise _fail(f"{where}.{key}", f"must be at least {minimum}")
    return value


def _names(values: Any, known: dict | set, where: str) -> tuple[str, ...]:
    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        raise _fail(where, "must be a list of strings")
    for v in values:
        if v not in known:
            raise _fail(where, f"unknown name {v!r}")
    return tuple(values)


def _build(data: dict, directory: Path) -> Pack:
    from keyline.escape import schema_is

    if not schema_is(data.get("schema")):
        raise _fail("schema", "must be the integer 1")
    name = _get(data, "name", str, "top level")
    if not NAME_RE.fullmatch(name):
        raise _fail("name", f"must match {NAME_RE.pattern}")
    _get(data, "version", str, "top level")
    modes = _names(_get(data, "modes", list, "top level"), set(MODES), "modes")
    if not modes:
        raise _fail("modes", "must name at least one mode")
    for moved in ("palette", "fonts", "templates"):  # B-8: they belong to voices now
        if moved in data:
            raise _fail(moved, "belongs to a voice, not the system (B-8)")
    palette = _names(_get(data, "palette_roles", list, "top level"), _AnyName(), "palette_roles")
    if len(set(palette)) != len(palette):
        raise _fail("palette_roles", "roles must be unique")
    palette_set = set(palette)
    accents = _names(_get(data, "accents", list, "top level"), palette_set, "accents")
    budget = _int(data, "accent_budget", "top level", minimum=0)
    containers = _get(data, "containers", str, "top level")
    if containers not in ("rules", "boxes", "none"):
        raise _fail("containers", "must be rules, boxes or none")
    alignment = _get(data, "alignment", str, "top level")
    if alignment not in ("left", "center"):
        raise _fail("alignment", "must be left or center")
    raw_accepted = _get(data, "accepted", list, "top level")  # its own error, not wrapped
    try:
        accepted = check_accepted(raw_accepted)
    except ValueError as exc:
        raise PackError(f"pack.toml: accepted{exc}") from exc

    surfaces = {}
    for sname, s in _get(data, "surfaces", dict, "top level").items():
        where = f"surfaces.{sname}"
        surfaces[sname] = Surface(
            sname,
            _names([_get(s, "background", str, where)], palette_set, f"{where}.background")[0],
            _names(_get(s, "text", list, where), palette_set, f"{where}.text"),
            _names([_get(s, "accent", str, where)], palette_set, f"{where}.accent")[0],
        )

    g = _get(data, "grid", dict, "top level")
    grid = Grid(
        _int(g, "columns", "grid", minimum=1),
        *(_int(g, k, "grid", minimum=0) for k in ("gutter_emu", "margin_x_emu", "margin_y_emu")),
        _int(g, "row_emu", "grid", minimum=1),
        _int(g, "rows", "grid", minimum=1),
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
    _names([_get(rule, "color", str, "keyline_rule")], palette_set, "keyline_rule.color")
    if _int(rule, "row", "keyline_rule", minimum=0) >= grid.rows:
        raise _fail("keyline_rule.row", "is outside the grid")
    _int(rule, "thickness_emu", "keyline_rule", minimum=1)

    styles: dict[str, dict[str, Style]] = {}
    raw_styles = _get(data, "styles", dict, "top level")
    for mode in modes:
        styles[mode] = {}
        for sname, s in _get(raw_styles, mode, dict, "styles").items():
            _table(s, f"styles.{mode}.{sname}")
            styles[mode][sname] = _style(sname, s, f"styles.{mode}.{sname}", surfaces)
    if len({frozenset(v) for v in styles.values()}) > 1:
        raise _fail("styles", "every mode must define the same styles")

    roles = {}
    for rname, r in _get(data, "roles", dict, "top level").items():
        roles[rname] = _role(rname, _table(r, f"roles.{rname}"), modes, styles, surfaces)
    missing = set(ROLES) - set(roles)
    if missing:
        raise _fail("roles", f"missing roles: {', '.join(sorted(missing))}")

    regions: dict[str, dict[str, Region]] = {}
    for lname, rs in _get(data, "regions", dict, "top level").items():
        rs = _table(rs, f"regions.{lname}")
        regions[lname] = {k: _region(v, f"regions.{lname}.{k}", grid) for k, v in rs.items()}
        if "title" not in regions[lname]:
            raise _fail(f"regions.{lname}", "needs a title region")
        _no_overlap(regions[lname], f"regions.{lname}")
    for role in roles.values():
        for layout in role.layouts:
            if layout not in regions:
                raise _fail(f"roles.{role.name}.layouts", f"no regions for {layout}")

    theme = _get(data, "theme", dict, "top level")
    if set(theme) != set(THEME_SLOTS):
        raise _fail("theme", f"needs exactly the slots {', '.join(THEME_SLOTS)}")
    for slot, pname in theme.items():
        if not isinstance(pname, str):
            raise _fail(f"theme.{slot}", "must be a palette role name")
        _names([pname], palette_set, f"theme.{slot}")
    ph = _get(data, "placeholders", dict, "top level")
    ph_idx = _get(ph, "idx", dict, "placeholders")
    for region, idx in ph_idx.items():
        if isinstance(idx, bool) or not isinstance(idx, int) or idx < 1:
            raise _fail(f"placeholders.idx.{region}", "must be a positive integer")
    if len(set(ph_idx.values())) != len(ph_idx):
        raise _fail("placeholders.idx", "idx values must be unique")
    ph_styles = _get(ph, "styles", dict, "placeholders")
    for layout, rs in ph_styles.items():
        for region, sname in _table(rs, f"placeholders.styles.{layout}").items():
            if not isinstance(sname, str):
                raise _fail(f"placeholders.styles.{layout}.{region}", "must be a style name")
    for layout, rs in regions.items():
        role = roles[parse_layout(layout)[0]]
        styles_here = ph_styles.get(layout, {})
        for region in rs:
            if region == "title":
                continue
            where = f"placeholders.styles.{layout}.{region}"
            if region not in ph_idx:
                raise _fail("placeholders.idx", f"no idx for region {region!r}")
            if region not in styles_here:
                raise _fail(where, "missing")
            sname = styles_here[region]
            for mode in modes:
                allowed = {s for ss in role.components[mode].values() for s in ss}
                if sname not in allowed:
                    raise _fail(where, f"style {sname!r} is not allowed on {role.name} in {mode}")

    return Pack(
        name=name,
        version=_get(data, "version", str, "top level"),
        directory=directory,
        modes=modes,
        palette_roles=palette,
        accents=accents,
        accent_budget=budget,
        containers=containers,
        alignment=alignment,
        accepted=accepted,
        surfaces=surfaces,
        grid=grid,
        keyline_rule=rule,
        theme=dict(theme),
        placeholder_idx=dict(ph_idx),
        placeholder_styles={k: dict(v) for k, v in ph_styles.items()},
        styles=styles,
        roles=roles,
        regions=regions,
        raw=data,
    )


class _AnyName(set):
    def __contains__(self, item: object) -> bool:
        return isinstance(item, str) and bool(item.strip())


def _style(name: str, s: dict, where: str, surfaces: dict) -> Style:
    weight = _get(s, "weight", str, where)
    if weight not in WEIGHTS:
        raise _fail(f"{where}.weight", "must be regular or bold")
    font = _get(s, "font", str, where)
    if font not in FONT_SLOTS:
        raise _fail(f"{where}.font", "must be display or text")
    color = _get(s, "color", dict, where)
    for surface, pname in color.items():
        if surface not in surfaces:
            raise _fail(f"{where}.color", f"unknown surface {surface!r}")
        # a style may use a role on a surface only if the surface allows it as text (Q-28)
        if pname not in surfaces[surface].text:
            raise _fail(f"{where}.color.{surface}", f"{pname!r} is not a text role on {surface}")
    size = _number(_get(s, "size_pt", (int, float), where), f"{where}.size_pt")
    if size <= 0 or (size * 100).denominator != 1:
        raise _fail(f"{where}.size_pt", "must be positive, in hundredths of a point")
    line_spacing = _number(s.get("line_spacing", 1), f"{where}.line_spacing")
    if line_spacing < 1:
        raise _fail(f"{where}.line_spacing", "must be at least 1.0 (§6.4)")
    return Style(
        name=name,
        font=font,
        size_pt=size,
        weight=weight,
        color=dict(color),
        caps=_flag(s, "caps", where),
        tracking=_number(s.get("tracking", 0), f"{where}.tracking"),
        line_spacing=line_spacing,
        space_before_pt=_spacing(s, "space_before_pt", where),
        space_after_pt=_spacing(s, "space_after_pt", where),
        bullet_indent_emu=_int(s, "bullet_indent_emu", where, minimum=0, default=0),
        bullet_marker=_get(s, "bullet_marker", str, where) if "bullet_marker" in s else "",
    )


def _flag(s: dict, key: str, where: str) -> bool:
    return _get(s, key, bool, where) if key in s else False


def _spacing(s: dict, key: str, where: str) -> Fraction:
    value = _number(s.get(key, 0), f"{where}.{key}")
    if value < 0:
        raise _fail(f"{where}.{key}", "must not be negative")
    return value


def _role(name: str, r: dict, modes: tuple, styles: dict, surfaces: dict) -> Role:
    where = f"roles.{name}"
    if name not in ROLES:
        raise _fail(where, "unknown role")
    surface = _get(r, "surface", str, where)
    if surface not in surfaces:
        raise _fail(f"{where}.surface", f"unknown surface {surface!r}")
    title = _get(r, "title", str, where)
    layouts = _names(_get(r, "layouts", list, where), _AnyName(), f"{where}.layouts")
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
        for comp, allowed in cm.items():
            if not isinstance(allowed, list):
                raise _fail(f"{where}.components.{mode}.{comp}", "must be a list of styles")
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
    anchor = v.get("anchor", "t")
    if anchor not in ANCHORS:
        raise _fail(f"{where}.anchor", 'must be "t" or "b"')
    r = Region(*(_get(v, k, int, where) for k in ("col", "span", "row", "rows")), anchor)
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
