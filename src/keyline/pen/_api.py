"""The pen's public API (spec 002 §6): `Deck` and the slide builder.

Every parameter is a token (a role, a style name, a region name, an evidence id) or
content; nothing accepts a colour, a font, a size, a length, a coordinate or an alignment
(§6.2). The builder resolves tokens against the pack's system and the deck's voice into a
writer-neutral plan (`_plan`), checks that every text fits its region (keyline.fit), and
`save()` hands the plans to the python-pptx writer.
"""

from __future__ import annotations

import re
import sys
from fractions import Fraction
from pathlib import Path

from keyline import config as config_mod
from keyline.fit import Setting, coverage_warning, fit, missing
from keyline.pen._errors import PenError
from keyline.pen._plan import ParaSpec, RectSpec, RunSpec, SlidePlan, TextSpec
from keyline.pen._regions import box, layout_for, regions, rule_box

EMU_PER_PT = 12700
# a string that looks like a raw value where a token is expected (§6.2)
RAW = re.compile(r"#[0-9a-f]{3,8}|[0-9a-f]{6}|-?\d+(\.\d+)?\s*(pt|cm|mm|in|px|emu)", re.IGNORECASE)


def _check_token(value: object, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PenError(f"{what} must be a name, not {value!r}")
    if RAW.fullmatch(value.strip()):
        raise PenError(f"{what} {value!r} looks like a raw value; the pen takes tokens only")
    return value


def _check_content(value: object, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PenError(f"{what} must be non-empty text")
    return value


class Deck:
    """A deck in one pack, mode and voice (§6.1, B-8.9). `voice` is a voice name of the
    pack or a voice file; `evidence` is an evidence file or a list of them (the first is
    primary)."""

    def __init__(
        self,
        pack: str,
        mode: str,
        voice: str,
        evidence: str | list[str] | None = None,
    ) -> None:
        from keyline.brief import BriefError, load_evidence, voice_findings
        from keyline.packs import PackError, resolve
        from keyline.packs.templates import build

        _check_token(pack, "pack")
        _check_token(mode, "mode")
        _check_token(voice, "voice")
        try:
            self._pack = resolve(pack, base=Path.cwd())
            if mode not in self._pack.modes:
                raise PenError(f"pack {self._pack.name} has no {mode} mode")
            self._voice = self._pack.voice(voice, base=Path.cwd())
        except PackError as exc:
            raise PenError(str(exc)) from exc
        self._mode = mode
        self._cfg = config_mod.load(mode)
        # Q-29 (audit 02): the pen refuses a voice with an error-level voice-* finding
        for f in voice_findings(self._pack, self._voice, self._cfg):
            if f.severity == "error":
                raise PenError(f"the pen refuses this voice: {f.rule}: {f.message}")
        self._evidence = None
        if evidence is not None:
            paths = [evidence] if isinstance(evidence, str) else list(evidence)
            try:
                self._evidence = load_evidence(paths, mode)
            except BriefError as exc:
                raise PenError(str(exc)) from exc
        self._template = build(self._pack, self._voice, mode)  # in memory (Q-46)
        self._slides: list[SlideBuilder] = []
        self._brief = None
        self._missing: dict[str, str] = {}  # family -> characters its twin lacks

    @classmethod
    def from_brief(cls, path: str) -> Deck:
        """A deck with the brief's mode, pack, voice and evidence; `next()` walks its
        slides in order."""
        from keyline.brief import BriefError, load

        try:
            brief = load(path)
        except BriefError as exc:
            raise PenError(f"{Path(path).name}: {exc}") from exc
        deck = cls.__new__(cls)
        deck._from_brief(brief)
        return deck

    def _from_brief(self, brief) -> None:
        from keyline.brief import voice_findings
        from keyline.packs.templates import build

        self._pack, self._voice, self._mode = brief.pack, brief.voice, brief.mode
        self._cfg = config_mod.load(brief.mode)
        for f in voice_findings(self._pack, self._voice, self._cfg):
            if f.severity == "error":
                raise PenError(f"the pen refuses this voice: {f.rule}: {f.message}")
        self._evidence = brief.evidence
        self._template = build(self._pack, self._voice, brief.mode)
        self._slides = []
        self._brief = brief
        self._missing = {}

    # -- slides ---------------------------------------------------------------------------

    def next(self, variant: str | None = None) -> SlideBuilder:
        """The builder for the brief's next slide, its role, headline and notes applied."""
        if self._brief is None:
            raise PenError("next() needs a brief: use Deck.from_brief(), or add()")
        index = len(self._slides)
        if index >= len(self._brief.slides):
            raise PenError(f"the brief has {len(self._brief.slides)} slides; no slide {index + 1}")
        s = self._brief.slides[index]
        builder = self.add(s.role, s.headline, s.notes or None, variant)
        builder._brief_slide = s
        return builder

    def add(
        self, role: str, headline: str, notes: str | None = None, variant: str | None = None
    ) -> SlideBuilder:
        """A new slide of `role` with its headline in the title placeholder."""
        _check_token(role, "role")
        if role not in self._pack.roles:
            raise PenError(f"unknown role {role!r}")
        if variant is not None:
            _check_token(variant, "variant")
        _check_content(headline, "headline")
        builder = SlideBuilder(self, role, layout_for(self._pack, role, variant))
        builder._headline(headline)
        if notes is not None:
            builder.notes(notes)
        if role == "evidence":  # the keyline device, drawn by the pen (§5.2)
            color = self._voice.hex(self._pack.keyline_rule["color"])
            builder._plan.shapes.append(RectSpec("keyline", rule_box(self._pack), color))
        self._slides.append(builder)
        return builder

    def save(self, path: str, author: str = "") -> None:
        """Write the deck: python-pptx, then the zip normalised (§6.5)."""
        from keyline import zipnorm
        from keyline.pen._writer_pptx import write

        if not isinstance(author, str):
            raise PenError("author must be text")
        data = write(self._template, [s._plan for s in self._slides], author)
        zipnorm.write(path, zipnorm.read_entries(data))
        for family, chars in self._missing.items():  # one warning per deck (audit 04)
            sys.stderr.write(f"keyline pen: warning: {coverage_warning(family, chars)}\n")

    # -- resolving tokens ------------------------------------------------------------------

    def _style(self, role: str, name: str):
        styles = self._pack.styles[self._mode]
        _check_token(name, "style")
        if name not in styles:
            raise PenError(f"unknown style {name!r}")
        return styles[name]

    def _setting(self, style, indent_emu: int = 0) -> Setting:
        return Setting(
            family=self._voice.font(style.font),
            weight=style.weight,
            size=style.size_pt,
            caps=style.caps,
            tracking=style.tracking,
            line_spacing=style.line_spacing,
            space_before=style.space_before_pt,
            space_after=style.space_after_pt,
            indent=Fraction(indent_emu, EMU_PER_PT),
        )

    def _note_missing(self, setting: Setting, text: str) -> None:
        chars = missing(setting, text)
        if chars:
            seen = self._missing.get(setting.family, "")
            self._missing[setting.family] = seen + "".join(c for c in chars if c not in seen)


class SlideBuilder:
    """One slide: its verbs fill named regions (§6.1). Returned by Deck.add() and
    Deck.next()."""

    def __init__(self, deck: Deck, role: str, layout: str) -> None:
        self._deck = deck
        self._role = deck._pack.roles[role]
        self._layout = layout
        self._surface = self._role.surface
        self._plan = SlidePlan(layout)
        self._used: set[str] = set()
        self._brief_slide = None

    # -- helpers the verbs share -------------------------------------------------------

    def _region(self, region: str) -> str:
        _check_token(region, "region")
        names = regions(self._deck._pack, self._layout)
        if region not in names:
            raise PenError(
                f"layout {self._layout} has no region {region!r} (regions: {', '.join(names)})"
            )
        if region in self._used:
            raise PenError(f"region {region!r} already holds a component")
        return region

    def _run(self, style, text: str) -> RunSpec:
        voice = self._deck._voice
        return RunSpec(
            text=text,
            size=style.size_hundredths,
            bold=style.weight == "bold",
            caps=style.caps,
            spacing=round(style.tracking * style.size_pt * 100),
            color=voice.hex(style.color[self._surface]),
            font="+mj-lt" if style.font == "display" else "+mn-lt",
        )

    def _para(self, style, text: str, bullet: bool = False) -> ParaSpec:
        return ParaSpec(
            runs=(self._run(style, text),),
            line_spacing=round(style.line_spacing * 100000),
            space_before=round(style.space_before_pt * 100),
            space_after=round(style.space_after_pt * 100),
            indent=style.bullet_indent_emu if bullet else 0,
            bullet=style.bullet_marker if bullet else "",
        )

    def _text(self, style, paragraphs, region_box, what, bullet=False) -> tuple[ParaSpec, ...]:
        """Fit-checked paragraphs for a box (DoesNotFit otherwise)."""
        setting = self._deck._setting(style, style.bullet_indent_emu if bullet else 0)
        for text in paragraphs:
            self._deck._note_missing(setting, text)
        fit(
            setting,
            list(paragraphs),
            Fraction(region_box.w, EMU_PER_PT),
            Fraction(region_box.h, EMU_PER_PT),
            what,
        )
        return tuple(self._para(style, text, bullet) for text in paragraphs)

    def _headline(self, headline: str) -> None:
        style = self._deck._pack.styles[self._deck._mode][self._role.title]
        title_box = box(self._deck._pack, self._layout, "title")
        paras = self._text(style, [headline], title_box, "headline")
        self._plan.shapes.append(TextSpec("title", title_box, paras, placeholder=0))

    # -- verbs -------------------------------------------------------------------------------

    def notes(self, text: str) -> SlideBuilder:
        """Speaker notes."""
        self._plan.notes = _check_content(text, "notes")
        return self
