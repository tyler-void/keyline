"""Briefs and evidence (spec 002 §4.1–§4.3, amendments B-4 and B-8.4/B-8.5).

`load(path)` reads a brief and its evidence files with tomllib, resolves the pack, the mode
and the voice, and returns typed objects. Every schema error is a `BriefError` with a
one-line reason, which the CLI turns into exit 1. Unknown keys are ignored at every level
(§4.1). `findings(brief)` computes the §4.3 and voice findings that `keyline brief`
reports; they are registry entries with `requires = "brief"` and no deck check, so `lint`
never runs them and `check` does not repeat them (§4.3).
"""

from __future__ import annotations

import re
import tomllib
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from keyline import config as config_mod
from keyline.findings import Finding, sort_findings
from keyline.packs import Pack, PackError, resolve
from keyline.packs.voices import (
    Voice,
    claude_look,
    claude_look_message,
    contrast_message,
    is_path,
    low_contrast,
    missing_why,
)
from keyline.packs.voices import parse as parse_voice
from keyline.registry import RuleSpec, register
from keyline.roles import ROLES
from keyline.rules._common import RESEARCH_CANON, RESEARCH_TELLS, words

ID_RE = re.compile(r"[a-z0-9_]+")  # matched with fullmatch (B-12 item 1)
# B-12 item 2: the spine is one line per slide (every break str.splitlines() honours)
LINE_BREAKS = "\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029"
NOTES_ROLES = ("statement", "evidence", "quote", "close")  # brief-notes (§4.3)
NO_EVIDENCE_ROLES = ("section", "quote")  # no room for a source line (§5.2)
MOOD_STRIP = ".,;:!?"
RESEARCH_LOOK = 'research §"Editorial" has become Claude\'s look: the Swiss pack needs hard guards'


class BriefError(ValueError):
    """A schema error in a brief or its evidence: exit 1 with this one-line reason."""


# ---------------------------------------------------------------------------------------
# registry entries (§4.3; B-8.5); fields per plan Q-2


def _entry(id, severity, scope, basis, summary, rationale, notes=""):
    return register(
        RuleSpec(
            id=id,
            category="quality",
            severity=severity,
            scope=scope,
            basis=basis,
            requires="brief",
            since="0.2.0",
            summary=summary,
            rationale=rationale,
            severity_notes=notes,
        )
    )


BRIEF_READS = _entry(
    "brief-reads",
    "warning",
    "slide",
    "structure",
    "A brief slide has more reads than the mode allows",
    RESEARCH_CANON,
)
BRIEF_MOOD = _entry(
    "brief-mood",
    "warning",
    "deck",
    "text",
    "An own_world item is only mood words, not a thing from the subject's world",
    RESEARCH_TELLS,
)
BRIEF_NOTES = _entry(
    "brief-notes",
    "warning",
    "slide",
    "structure",
    "A presented statement, evidence, quote or close slide has no notes in the brief",
    RESEARCH_TELLS,
)
BRIEF_HEADLINE_LONG = _entry(
    "brief-headline-long",
    "warning",
    "slide",
    "text",
    "A brief headline has more words than the mode allows (quote slides exempt)",
    RESEARCH_CANON,
)
BRIEF_NO_STATEMENT = _entry(
    "brief-no-statement",
    "advisory",
    "deck",
    "structure",
    "A long presented brief has no statement slide",
    RESEARCH_TELLS,
)
VOICE_CONTRAST = _entry(
    "voice-contrast",
    "error",
    "deck",
    "color",
    "A text colour and surface the system allows are below contrast_normal in this voice",
    "L-006",
)
VOICE_CLAUDE_LOOK = _entry(
    "voice-claude-look",
    "warning",
    "deck",
    "color",
    "The voice has a cream background and a terracotta colour (the Claude look)",
    "L-007",
    "advisory when only a background is cream, or when the voice or pack accepts it",
)
VOICE_WHY = _entry(
    "voice-why",
    "warning",
    "deck",
    "structure",
    "An inline voice has no why line for a palette role",
    RESEARCH_LOOK,
)


# ---------------------------------------------------------------------------------------
# the typed brief


@dataclass(frozen=True)
class Entry:
    id: str
    label: str
    source: str
    value: str | None = None
    series: tuple[tuple[str, int | float], ...] | None = None
    aliases: tuple[str, ...] = ()

    def tokens(self) -> set[str]:
        from keyline.numtokens import entry_tokens

        return entry_tokens(self.value, self.aliases, self.label, self.series)


@dataclass(frozen=True)
class Product:
    name: str
    fictional: bool = False
    disclosure: str = ""


@dataclass(frozen=True)
class EvidenceSet:
    product: Product
    entries: dict[str, Entry]
    files: tuple[Path, ...]


@dataclass(frozen=True)
class Direction:
    audience: str
    decision: str
    thesis: str
    own_world: tuple[str, ...]
    motif: str


@dataclass(frozen=True)
class BriefSlide:
    index: int  # 1-based
    role: str
    headline: str
    reads: tuple[str, ...]
    evidence: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class Brief:
    path: Path
    mode: str
    pack: Pack
    voice: Voice
    evidence: EvidenceSet
    direction: Direction
    slides: tuple[BriefSlide, ...]

    @property
    def spine(self) -> list[dict[str, Any]]:
        return [{"slide": s.index, "role": s.role, "headline": s.headline} for s in self.slides]


# ---------------------------------------------------------------------------------------
# loading


def read_toml(path: Path, what: str, error: type[Exception] = ValueError) -> dict:
    """A TOML file, or `error` with one line (B-12 item 7): missing, a directory,
    unreadable, not UTF-8, not TOML, or nested beyond the parser's limit."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise error(f"{what} not found: {path.name}") from exc
    except IsADirectoryError as exc:
        raise error(f"{what} {path.name} is a directory, not a file") from exc
    except UnicodeDecodeError as exc:
        raise error(f"{what} {path.name} is not UTF-8") from exc
    except OSError as exc:
        raise error(f"{what} {path.name} cannot be read: {exc.strerror or exc}") from exc
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise error(f"{what} {path.name} is not valid TOML: {exc}") from exc
    except RecursionError as exc:
        raise error(f"{what} {path.name} nests too deeply") from exc


def _read_toml(path: Path, what: str) -> dict:
    return read_toml(path, what, BriefError)


def _str(d: dict, key: str, where: str, *, required: bool = True, empty: bool = False) -> str:
    if key not in d:
        if required:
            raise BriefError(f"{where}{key}: missing")
        return ""
    value = d[key]
    if not isinstance(value, str):
        raise BriefError(f"{where}{key}: must be a string")
    if not empty and not value.strip():
        raise BriefError(f"{where}{key}: must not be empty")
    return value


def _strings(d: dict, key: str, where: str, *, required: bool = True) -> tuple[str, ...]:
    if key not in d:
        if required:
            raise BriefError(f"{where}{key}: missing")
        return ()
    value = d[key]
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise BriefError(f"{where}{key}: must be a list of strings")
    for i, v in enumerate(value):
        if not v.strip():
            raise BriefError(f"{where}{key}[{i + 1}]: must not be empty")
    return tuple(value)


def load(path: str | Path) -> Brief:
    """Raises BriefError with a one-line reason on any schema error."""
    path = Path(path)
    data = _read_toml(path, "brief")
    if data.get("schema") != 1:
        raise BriefError("schema: must be 1")
    mode = _str(data, "mode", "")
    if mode not in config_mod.MODES:
        raise BriefError(f"mode: must be presented or read, not {mode!r}")
    cfg = config_mod.load(mode)

    pack_ref = _str(data, "pack", "")
    try:
        pack = resolve(pack_ref, base=path.parent)
    except PackError as exc:
        raise BriefError(str(exc)) from exc
    if mode not in pack.modes:  # B-4
        raise BriefError(f"mode: pack {pack.name} has no {mode} mode ({', '.join(pack.modes)})")
    voice = _voice(data, pack, path)

    raw_ev = data.get("evidence")
    if isinstance(raw_ev, str):
        raw_ev = [raw_ev]
    if not isinstance(raw_ev, list) or not raw_ev or not all(isinstance(e, str) for e in raw_ev):
        raise BriefError("evidence: must be a path or a non-empty list of paths")
    evidence = _evidence([path.parent / e for e in raw_ev], cfg)

    d = data.get("direction")
    if not isinstance(d, dict):
        raise BriefError("direction: missing")
    fields = {k: _str(d, k, "direction.") for k in ("audience", "decision", "thesis", "motif")}
    own_world = _strings(d, "own_world", "direction.")
    if not 3 <= len(own_world) <= 7:
        raise BriefError(f"direction.own_world: needs 3 to 7 items, has {len(own_world)}")
    direction = Direction(own_world=own_world, **fields)

    raw_slides = data.get("slides")
    if not isinstance(raw_slides, list) or not raw_slides:
        raise BriefError("slides: needs at least one [[slides]] table")
    slides = tuple(_slide(i + 1, s, evidence) for i, s in enumerate(raw_slides))
    if slides[0].role != "cover":
        raise BriefError(f"slides[1].role: the first slide must be a cover, not {slides[0].role}")
    covers = [s.index for s in slides if s.role == "cover"]
    if len(covers) > 1:
        raise BriefError(f"slides[{covers[1]}].role: more than one cover")
    return Brief(path, mode, pack, voice, evidence, direction, slides)


def _voice(data: dict, pack: Pack, path: Path) -> Voice:
    """B-8.4: `voice = "<name>"` or an inline [voice] table, exactly one. TOML itself
    refuses both (the same key twice), so "both" arrives as a TOML error."""
    raw = data.get("voice")
    if raw is None:
        raise BriefError("voice: missing; name a voice (voice = NAME) or give a [voice] table")
    try:
        if isinstance(raw, str):
            if is_path(raw):  # B-12 item 3: a brief names a voice; only --voice takes a file
                raise BriefError(f"voice: {raw!r} is a path; a brief names a voice of its pack")
            return pack.voice(raw)
        if isinstance(raw, dict):
            return parse_voice(raw, pack, where="[voice]")
    except PackError as exc:
        raise BriefError(str(exc)) from exc
    raise BriefError("voice: must be a voice name or a [voice] table")


def _slide(index: int, s: Any, evidence: EvidenceSet) -> BriefSlide:
    where = f"slides[{index}]."
    if not isinstance(s, dict):
        raise BriefError(f"slides[{index}]: must be a table")
    role = _str(s, "role", where)
    if role not in ROLES:
        raise BriefError(f"{where}role: unknown role {role!r}")
    headline = _str(s, "headline", where)
    reads = _strings(s, "reads", where)
    if not reads:
        raise BriefError(f"{where}reads: needs at least one item")
    for key, text in [
        ("headline", headline),
        *((f"reads[{i}]", r) for i, r in enumerate(reads, 1)),
    ]:
        if any(ch in LINE_BREAKS for ch in text):
            raise BriefError(f"{where}{key}: must be one line (it contains a line break)")
    ids = _strings(s, "evidence", where, required=False)
    for eid in ids:
        if eid not in evidence.entries:
            raise BriefError(f"{where}evidence: unknown evidence id {eid!r}")
    if ids and role in NO_EVIDENCE_ROLES:
        raise BriefError(f"{where}evidence: a {role} slide has no room for a source line")
    notes = _str(s, "notes", where, required=False, empty=True)
    return BriefSlide(index, role, headline, reads, ids, notes)


def _evidence(paths: list[Path], cfg) -> EvidenceSet:
    entries: dict[str, Entry] = {}
    product = None
    for n, path in enumerate(paths):
        data = _read_toml(path, "evidence file")
        name = path.name
        if data.get("schema") != 1:
            raise BriefError(f"evidence file {name}: schema must be 1")
        if n == 0:  # only the primary file needs [product] (§4.1)
            product = _product(data.get("product"), name)
        raw = data.get("evidence", [])
        if not isinstance(raw, list):
            raise BriefError(f"evidence file {name}: [[evidence]] must be an array of tables")
        for i, e in enumerate(raw):
            entry = _entry_of(e, f"evidence file {name}: evidence[{i + 1}].", cfg)
            if entry.id in entries:
                raise BriefError(f"evidence file {name}: duplicate evidence id {entry.id!r}")
            entries[entry.id] = entry
    return EvidenceSet(product, entries, tuple(paths))


def _product(p: Any, name: str) -> Product:
    where = f"evidence file {name}: product."
    if not isinstance(p, dict):
        raise BriefError(f"evidence file {name}: [product] is missing")
    fictional = p.get("fictional", False)
    if not isinstance(fictional, bool):
        raise BriefError(f"{where}fictional: must be true or false")
    disclosure = _str(p, "disclosure", where, required=fictional)
    return Product(_str(p, "name", where), fictional, disclosure)


def _entry_of(e: Any, where: str, cfg) -> Entry:
    if not isinstance(e, dict):
        raise BriefError(f"{where.rstrip('.')}: must be a table")
    eid = _str(e, "id", where)
    if not ID_RE.fullmatch(eid):
        raise BriefError(f"{where}id: {eid!r} must match {ID_RE.pattern}")
    label = _str(e, "label", where)
    n = words(label)
    limit = cfg.as_int("caption_exempt_words")
    if not 1 <= n <= limit:
        raise BriefError(f"{where}label: has {n} words; 1 to {limit} allowed")
    source = _str(e, "source", where)
    has_value, has_series = "value" in e, "series" in e
    if has_value == has_series:
        raise BriefError(f"{where[:-1]}: needs exactly one of value or series")
    value = _str(e, "value", where) if has_value else None
    series = _series(e["series"], f"{where}series") if has_series else None
    aliases = _strings(e, "aliases", where, required=False)
    return Entry(eid, label, source, value, series, aliases)


def _series(raw: Any, where: str) -> tuple[tuple[str, int | float], ...]:
    ok = isinstance(raw, list) and all(
        isinstance(p, list)
        and len(p) == 2
        and isinstance(p[0], str)
        and isinstance(p[1], int | float)
        and not isinstance(p[1], bool)
        for p in raw
    )
    if not ok:
        raise BriefError(f"{where}: must be a list of [category, number] pairs")
    return tuple((c, v) for c, v in raw)


# ---------------------------------------------------------------------------------------
# findings (§4.3; B-8.5)


def _mood_only(item: str, mood: tuple[str, ...]) -> bool:
    tokens = [t.strip(MOOD_STRIP) for t in unicodedata.normalize("NFC", item).casefold().split()]
    tokens = [t for t in tokens if t]
    return bool(tokens) and all(t in mood for t in tokens)


def findings(brief: Brief) -> list[Finding]:
    cfg = config_mod.load(brief.mode)
    presented = brief.mode == "presented"
    out: list[Finding] = []
    reads_max = cfg.as_int("reads_max")
    words_max = cfg.as_int("title_words_max")
    for s in brief.slides:
        if len(s.reads) > reads_max:
            out.append(
                BRIEF_READS.finding(
                    s.index,
                    None,
                    f"{len(s.reads)} reads (max {reads_max} in {brief.mode} mode)",
                    measured=len(s.reads),
                    threshold=reads_max,
                )
            )
        if presented and s.role in NOTES_ROLES and not s.notes.strip():
            out.append(BRIEF_NOTES.finding(s.index, None, f"{s.role} slide has no notes"))
        n = words(s.headline)
        if s.role != "quote" and n > words_max:
            out.append(
                BRIEF_HEADLINE_LONG.finding(
                    s.index,
                    None,
                    f"headline has {n} words (max {words_max} in {brief.mode} mode)",
                    measured=n,
                    threshold=words_max,
                )
            )
    for item in brief.direction.own_world:
        if _mood_only(item, cfg.mood_words):
            out.append(BRIEF_MOOD.finding(0, None, f"own_world item {item!r} is only mood words"))
    count = len(brief.slides)
    if (
        presented
        and count >= cfg.as_int("statement_min_slides")
        and not any(s.role == "statement" for s in brief.slides)
    ):
        out.append(
            BRIEF_NO_STATEMENT.finding(
                0, None, f"{count} slides and no statement slide", measured=count
            )
        )
    out.extend(voice_findings(brief.pack, brief.voice, cfg))
    return sort_findings(_apply_accepted(out, brief))


def voice_findings(pack: Pack, voice: Voice, cfg) -> list[Finding]:
    """The three B-8.5 voice checks as findings (slide 0: the brief's level)."""
    out = []
    need = cfg.contrast_normal
    for pair in low_contrast(pack, voice, cfg):
        out.append(
            VOICE_CONTRAST.finding(
                0,
                None,
                f"voice {voice.name}: {contrast_message(pair, voice, need)}",
                measured=round(pair.ratio, 2),
                threshold=float(need),
            )
        )
    look = claude_look(pack, voice, cfg)
    if look.fires:
        out.append(
            VOICE_CLAUDE_LOOK.finding(
                0,
                None,
                f"voice {voice.name}: {claude_look_message(look, voice)}",
                severity=None if look.terracotta else "advisory",
            )
        )
    if voice.path is None:  # inline voices only (B-8.5)
        for role in missing_why(pack, voice):
            out.append(VOICE_WHY.finding(0, None, f"inline voice has no why line for {role}"))
    return out


def _apply_accepted(out: list[Finding], brief: Brief) -> list[Finding]:
    from dataclasses import replace

    accepted = dict(brief.pack.accepted)
    accepted.update(dict(brief.voice.accepted))
    return [
        replace(f, severity="advisory", message=f"{f.message} (accepted: {accepted[f.rule]})")
        if f.rule in accepted and f.severity != "advisory"
        else f
        for f in out
    ]
