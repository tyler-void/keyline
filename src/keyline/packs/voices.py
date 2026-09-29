"""Voices (spec 002 amendment B-8): the values a deck's colours take and its two fonts.

A voice fills a system's `palette_roles` with 6-digit hex values and names a display and
a text family from `portable_fonts`. It comes from a pack file
(`packs/<pack>/voices/<name>.toml`), a file given with `--voice`, or a brief's inline
`[voice]` table. This module loads and validates voices (the B-8.5 schema errors) and
computes the three voice checks as plain data; the registry entries that report them
belong to the brief (T-12). Pure data: no deck, no python-pptx.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from keyline.colorspace import hsl, lab
from keyline.escape import esc, schema_is
from keyline.packs import Pack, PackError, _exists, check_accepted

NAME_RE = re.compile(r"[a-z0-9-]+")  # both matched with fullmatch (B-12 item 1)
HEX_RE = re.compile(r"[0-9A-Fa-f]{6}")
INLINE = "inline"
TOP_KEYS = frozenset({"schema", "accepted", "fonts", "palette", "why"})  # + "name" in a file
FONT_KEYS = frozenset({"display", "text"})


class VoiceError(PackError):
    """A voice is missing or invalid (a schema error, exit 1); the message is one line."""


@dataclass(frozen=True)
class Voice:
    name: str  # the file stem, or "inline" for a brief's [voice] table
    display: str  # canonical portable_fonts spelling
    text: str
    palette: dict[str, str]  # palette role -> "RRGGBB" (upper case)
    why: dict[str, str] = field(default_factory=dict)
    accepted: tuple[tuple[str, str], ...] = ()  # (rule id, reason)
    path: Path | None = None  # the file it came from; None for an inline voice

    def hex(self, role: str) -> str:
        return self.palette[role]

    def font(self, slot: str) -> str:
        """The family for a style's `font` slot, "display" or "text"."""
        return self.display if slot == "display" else self.text

    @property
    def fonts(self) -> tuple[str, ...]:
        """The distinct families, display first."""
        return (self.display,) if self.display == self.text else (self.display, self.text)

    def accent_hexes(self, pack: Pack) -> set[str]:
        return {self.palette[r] for r in pack.accents}

    def same_as(self, other: Voice) -> bool:
        """Whether two voices look the same: fonts and palette (plan Q-35)."""
        return (self.display, self.text, self.palette) == (other.display, other.text, other.palette)


# ---------------------------------------------------------------------------------------
# loading


def portable_fonts() -> tuple[tuple[str, str], ...]:
    from keyline.config import load as load_config

    return load_config().portable_fonts


def is_path(value: str | Path) -> bool:
    """`--voice` takes a name or a file: a separator or a .toml suffix means a file (Q-35)."""
    text = str(value)
    return "/" in text or "\\" in text or text.endswith(".toml")


def load(pack: Pack, name_or_path: str | Path, base: Path | None = None) -> Voice:
    """A voice of `pack` by name, or a voice file (relative to `base` when given)."""
    if isinstance(name_or_path, Path) or is_path(name_or_path):
        path = Path(name_or_path)
        if not path.is_absolute() and base is not None:
            path = base / path
        if not _exists(path, f"voice file {str(name_or_path)!r}", VoiceError):
            raise VoiceError(f"voice file not found: {name_or_path}")
        return _load_file(pack, path, name=None)
    name = str(name_or_path)
    path = pack.directory / "voices" / f"{name}.toml"
    if not NAME_RE.fullmatch(name) or not path.is_file():
        known = ", ".join(pack.voices()) or "none"
        raise VoiceError(f"unknown voice {name!r} for pack {pack.name} (voices: {known})")
    return _load_file(pack, path, name=name)


def _load_file(pack: Pack, path: Path, name: str | None) -> Voice:
    from keyline.brief import read_toml

    data = read_toml(path, "voice file", VoiceError)
    where = f"voice {esc(path.name)}"
    if not schema_is(data.get("schema")):
        raise VoiceError(f"{where}: schema must be the integer 1")
    stated = data.get("name")
    if not isinstance(stated, str) or not NAME_RE.fullmatch(stated):
        raise VoiceError(f"{where}: name must match {NAME_RE.pattern}")
    if stated != path.stem:
        raise VoiceError(f"{where}: name {stated!r} must equal the file name {path.stem!r}")
    return parse(data, pack, where=where, name=stated, path=path)


def parse(
    data: dict[str, Any],
    pack: Pack,
    *,
    where: str = "voice",
    name: str = INLINE,
    path: Path | None = None,
    portable: tuple[tuple[str, str], ...] | None = None,
) -> Voice:
    """Validate a voice table against the pack's system. `name` and `schema` are checked by
    the file loader; an inline `[voice]` may not carry `name` (plan Q-30). The schema is
    closed (amendment B-18): any key not listed below is a schema error that names it."""
    if not isinstance(data, dict):
        raise VoiceError(f"{where}: must be a table")
    allowed = TOP_KEYS | ({"name"} if path is not None else set())
    if "schema" in data and not schema_is(data["schema"]):  # optional inline (Q-30)
        raise VoiceError(f"{where}: schema must be the integer 1")
    for key in data:
        if key not in allowed:
            raise VoiceError(
                f"{where}: unknown key {key!r} (allowed: {', '.join(sorted(allowed))})"
            )
    portable = portable_fonts() if portable is None else portable
    fonts = data.get("fonts")
    if not isinstance(fonts, dict):
        raise VoiceError(f"{where}: missing [fonts] table")
    for key in fonts:
        if key not in FONT_KEYS:
            raise VoiceError(f"{where}: fonts has an unknown key {key!r} (display, text)")
    display = _font(fonts.get("display"), portable, f"{where}: fonts.display")
    text = _font(fonts.get("text"), portable, f"{where}: fonts.text")

    raw = data.get("palette")
    if not isinstance(raw, dict):
        raise VoiceError(f"{where}: missing [palette] table")
    roles = pack.palette_roles
    missing = [r for r in roles if r not in raw]
    if missing:
        raise VoiceError(f"{where}: palette is missing the role {missing[0]!r}")
    extra = sorted(set(raw) - set(roles))
    if extra:
        raise VoiceError(f"{where}: palette has the extra role {extra[0]!r}")
    palette = {}
    for role in roles:
        value = raw[role]
        if not isinstance(value, str) or not HEX_RE.fullmatch(value):
            raise VoiceError(f"{where}: palette.{role} {value!r} is not 6-digit hex (RRGGBB)")
        palette[role] = value.upper()
    for accent in pack.accents:  # plan Q-32: an accent value must mean only "accent"
        for role in roles:
            if role not in pack.accents and palette[role] == palette[accent]:
                raise VoiceError(f"{where}: {accent} has the same value as {role}")

    why = data.get("why", {})
    if not isinstance(why, dict):
        raise VoiceError(f"{where}: [why] must be a table")
    for key in why:
        if key == "accepted":  # the B-8.2 example's trap: a key after [why] belongs to it
            raise VoiceError(f"{where}: why.accepted: accepted belongs before [fonts]")
        if key not in roles:
            raise VoiceError(f"{where}: why has an unknown key {key!r} (not a palette role)")
    try:
        accepted = check_accepted(data.get("accepted", []))  # B-10
    except ValueError as exc:
        raise VoiceError(f"{where}: accepted{exc}") from exc
    return Voice(
        name=name,
        display=display,
        text=text,
        palette=palette,
        why={r: v.strip() for r, v in why.items() if r in roles and isinstance(v, str)},
        accepted=accepted,
        path=path,
    )


def _font(value: Any, portable: tuple[tuple[str, str], ...], where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise VoiceError(f"{where} must be a font family")
    key = " ".join(value.split()).casefold()
    for family, _twin in portable:
        if family.casefold() == key:
            return family
    names = ", ".join(f for f, _ in portable)
    raise VoiceError(f"{where} {value!r} is not a portable font ({names})")


# ---------------------------------------------------------------------------------------
# the three voice checks (B-8.5), as data


@dataclass(frozen=True)
class Pair:
    text: str  # palette role of the text colour
    surface: str  # surface name
    background: str  # palette role of the surface
    ratio: float  # WCAG 2.x contrast


def contrast_pairs(pack: Pack, voice: Voice) -> list[Pair]:
    """Every (text colour, surface) pair the system allows (plan Q-28), in pack order."""
    from keyline.rules.text_contrast import contrast

    pairs = []
    for surface in pack.surfaces.values():
        bg = voice.hex(surface.background)
        for role in surface.text:
            pairs.append(
                Pair(role, surface.name, surface.background, contrast(voice.hex(role), bg))
            )
    return pairs


def low_contrast(pack: Pack, voice: Voice, cfg) -> list[Pair]:
    """The pairs below `contrast_normal`: one `voice-contrast` finding each."""
    need = float(cfg.contrast_normal)
    return [p for p in contrast_pairs(pack, voice) if p.ratio < need]


@dataclass(frozen=True)
class ClaudeLook:
    cream: tuple[str, ...]  # background roles whose value is in the cream band
    terracotta: tuple[str, ...]  # palette roles whose value is in the terracotta band

    @property
    def fires(self) -> bool:
        return bool(self.cream)


def background_roles(pack: Pack) -> tuple[str, ...]:
    """The palette roles a system surface uses as its background (Swiss: paper, ink)."""
    return tuple(dict.fromkeys(s.background for s in pack.surfaces.values()))


def claude_look(pack: Pack, voice: Voice, cfg) -> ClaudeLook:
    """`voice-claude-look`: a cream background (warning with a terracotta, else advisory).
    Every background role is tested, not only paper (amendment B-9)."""
    from keyline.rules.claude_look_palette import is_cream, is_terracotta

    cream = tuple(r for r in background_roles(pack) if is_cream(voice.hex(r), cfg))
    terracotta = tuple(r for r, v in voice.palette.items() if is_terracotta(v, cfg))
    return ClaudeLook(cream, terracotta)


def missing_why(pack: Pack, voice: Voice) -> list[str]:
    """`voice-why`: palette roles without a non-empty why line (inline voices only)."""
    return [r for r in pack.palette_roles if not voice.why.get(r)]


def paper_lab(voice: Voice) -> tuple[float, float, float]:
    return lab(voice.hex("paper"))


def accent_hue(voice: Voice) -> float:
    return hsl(voice.hex("accent"))[0]


# ---------------------------------------------------------------------------------------
# messages, shared by `keyline brief` findings (T-12) and the lint-time notices (plan Q-29)


def contrast_message(pair: Pair, voice: Voice, need) -> str:
    return (
        f"{pair.text} #{voice.hex(pair.text)} on the {pair.surface} surface "
        f"#{voice.hex(pair.background)} is {pair.ratio:.2f} : 1 (needs {float(need):g} : 1)"
    )


def claude_look_message(look: ClaudeLook, voice: Voice) -> str:
    cream = " and ".join(f"{r} #{voice.hex(r)}" for r in look.cream)
    cream += " are cream" if len(look.cream) > 1 else " is cream"
    if not look.terracotta:
        return f"{cream}; no terracotta"
    role = look.terracotta[0]
    return f"{cream} and {role} #{voice.hex(role)} is a terracotta"


def notices(pack: Pack, voice: Voice, cfg) -> list[str]:
    """One line per voice finding at warning or error, for commands that load a voice
    outside `keyline brief` (plan Q-29c). `accepted` ids are advisory, so they are left
    out. voice-why applies to inline voices only, which only briefs carry."""
    accepted = {r for r, _ in pack.accepted} | {r for r, _ in voice.accepted}
    out = []
    if "voice-contrast" not in accepted:
        need = cfg.contrast_normal
        for pair in low_contrast(pack, voice, cfg):
            out.append(f"voice {voice.name}: voice-contrast: {contrast_message(pair, voice, need)}")
    look = claude_look(pack, voice, cfg)
    if look.fires and look.terracotta and "voice-claude-look" not in accepted:
        out.append(f"voice {voice.name}: voice-claude-look: {claude_look_message(look, voice)}")
    return out
