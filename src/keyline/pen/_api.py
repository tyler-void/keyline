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
from keyline.fit import ROW_ALLOWANCE_PT, Setting, coverage_warning, fit, missing
from keyline.fit.text import code_point, normalize, refused
from keyline.fit.text import paragraphs as paragraphs_of
from keyline.pen._errors import DoesNotFit, PenError
from keyline.pen._plan import (
    ChartSpec,
    ParaSpec,
    PictureSpec,
    RectSpec,
    RunSpec,
    SlidePlan,
    TableSpec,
    TextSpec,
)
from keyline.pen._regions import box, layout_for, regions, rule_box

EMU_PER_PT = 12700
CELL_MARGINS = (0, 91440, 45720, 45720)  # EMU: flush left, a gutter on the right (§6.4)
RULE_WIDTH = 9525  # EMU, 0.75 pt: a hairline
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


def _check_text(value: object, what: str, paragraphs: bool = False) -> str:
    """Text with no character the pen refuses (B-22 item 3), or PenError naming it."""
    if not isinstance(value, str):
        raise PenError(f"{what} must be text, not {type(value).__name__}")
    bad = refused(value, paragraphs)
    if bad is not None:
        hint = "; only text() and notes() take \\n, between paragraphs" if bad == "\n" else ""
        raise PenError(f"{what} contains {code_point(bad)}, which the pen refuses{hint}")
    return value


def _line(value: object, what: str, empty: bool = False) -> str:
    """A one-line text, normalized (B-22): exactly what the estimator measures and the
    writer writes."""
    text = normalize(_check_text(value, what))
    if not text and not empty:
        raise PenError(f"{what} must be non-empty text")
    return text


def _paragraphs(value: object, what: str) -> list[str]:
    """A `text()` or `notes()` string as its normalized paragraphs (B-22 item 2)."""
    paras = paragraphs_of(_check_text(value, what, paragraphs=True))
    if not paras:
        raise PenError(f"{what} must be non-empty text")
    return paras


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
        headline = _line(headline, "headline")
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
        from keyline.pen._determinism import normalise
        from keyline.pen._writer_pptx import write

        if not isinstance(author, str):
            raise PenError("author must be text")
        data = write(self._template, [s._plan for s in self._slides], author)
        Path(path).write_bytes(normalise(data))  # §6.5: byte-identical for the same input
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
        self._lines: dict[str, str] = {}  # the footer's "source" and "note" lines
        self._evidence_used: dict[str, None] = {}  # evidence ids the verbs used, in order
        self._accents = 0  # accent elements on this slide (the pen enforces accent_budget)
        self._figures = 0

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

    def _allowed(self, component: str, style: str | None = None, styled: bool = True) -> str:
        """The style this component uses on this role in this mode (§5.1 `roles`)."""
        mode = self._deck._mode
        allowed = self._role.components[mode]
        if component not in allowed:
            raise PenError(f"role {self._role.name} does not allow {component} in {mode} mode")
        if not styled:  # an image carries no text style
            return ""
        if style is None:
            if not allowed[component]:
                raise PenError(f"role {self._role.name} gives {component} no style")
            return allowed[component][0]
        self._deck._style(self._role.name, style)  # a token, and a known style
        if style not in allowed[component]:
            raise PenError(
                f"style {style!r} is not allowed for {component} on {self._role.name} "
                f"in {mode} mode (allowed: {', '.join(allowed[component])})"
            )
        return style

    def _caption(self, text: str, what: str) -> str:
        """Labels, attributions and header cells are captions: at most caption_exempt_words
        words (§6.2), so they never become body text."""
        from keyline.rules._common import words

        limit = self._deck._cfg.as_int("caption_exempt_words")
        text = _line(text, what)
        n = words(text)
        if n > limit:
            raise PenError(f"{what} has {n} words; at most {limit} (caption_exempt_words)")
        return text

    def _place(self, region: str, style_name: str, paragraphs, what: str, bullet=False):
        style = self._deck._pack.styles[self._deck._mode][style_name]
        region_box = box(self._deck._pack, self._layout, region)
        paras = self._text(style, paragraphs, region_box, what, bullet)
        if style.color[self._surface] in self._deck._pack.accents:
            self._spend_accent(what)  # e.g. a label in accent_on_ink on a section slide
        idx = self._deck._pack.placeholder_idx.get(region)
        self._plan.shapes.append(TextSpec(region, region_box, paras, placeholder=idx))
        self._used.add(region)

    def _check_accent(self, what: str) -> None:
        """One more accent element would exceed the pack's accent_budget (§6.1)."""
        budget = self._deck._pack.accent_budget
        if self._accents + 1 > budget:
            raise PenError(f"{what} would be accent {self._accents + 1}; the budget is {budget}")

    def _spend_accent(self, what: str) -> None:
        self._check_accent(what)
        self._accents += 1

    def _entry(self, evidence_id: str):
        from keyline.pen._errors import EvidenceError

        _check_token(evidence_id, "evidence id")
        evidence = self._deck._evidence
        if evidence is None or evidence_id not in evidence.entries:
            raise EvidenceError(f"unknown evidence id {evidence_id!r}")
        self._evidence_used[evidence_id] = None
        return evidence.entries[evidence_id]

    def _footer(self) -> None:
        """The fixed bottom region: the source line, then the note line (§6.1)."""
        if "footer" not in regions(self._deck._pack, self._layout):
            raise PenError(f"layout {self._layout} has no footer region for source or note lines")
        lines = [self._lines[k] for k in ("source", "note") if k in self._lines]
        self._plan.shapes = [
            s for s in self._plan.shapes if not (isinstance(s, TextSpec) and s.name == "footer")
        ]
        self._used.discard("footer")
        self._place("footer", self._allowed("source"), lines, "source and note lines")

    # -- verbs -------------------------------------------------------------------------------

    def text(self, content: str, style: str = "body", region: str = "main") -> SlideBuilder:
        """A block of text in one region, in a style the role allows for text."""
        style = self._allowed("text", style)
        region = self._region(region)
        self._place(region, style, _paragraphs(content, "text"), "text")
        return self

    def bullets(self, items: list[str], region: str = "main") -> SlideBuilder:
        """A bulleted list, at most bullets_max items (§3.2)."""
        style = self._allowed("bullets")
        region = self._region(region)
        if not isinstance(items, list) or not items:
            raise PenError("bullets need a non-empty list of items")
        limit = self._deck._cfg.as_int("bullets_max")
        if len(items) > limit:
            raise PenError(f"{len(items)} bullets; at most {limit} in {self._deck._mode} mode")
        texts = [_line(item, "a bullet") for item in items]
        self._place(region, style, texts, "bullets", bullet=True)
        return self

    def figure(
        self,
        evidence_id: str,
        region: str = "main",
        label: str | None = None,
        accent: bool = False,
    ) -> SlideBuilder:
        """An evidence value as a numeral, with its label, as two shapes in one region
        (§6.1, Q-43): the numeral's box is the region's top rows, one numeral line tall
        (rounded up to whole grid rows); the label's box is the rest, top-anchored; both
        span the region's width and touch without overlapping. `accent=True` sets the
        numeral in the surface's accent and counts against accent_budget."""
        import math

        from keyline.geom import Box

        numeral_style = self._allowed("figure", "numeral")
        label_style = self._allowed("figure", "label")
        region = self._region(region)
        entry = self._entry(evidence_id)
        if entry.value is None:
            raise PenError(f"{evidence_id!r} is a series; use chart_bar for it")
        limit = self._deck._cfg.as_int("numerals_max")
        if self._figures + 1 > limit:
            raise PenError(f"figure {self._figures + 1}; at most {limit} per slide")
        from keyline.rules._common import words

        value = _line(entry.value, "numeral")
        if words(value) > self._deck._cfg.as_int("kpi_numeral_max_words"):
            raise PenError(f"numeral {value!r} has too many words for a figure")
        label = self._caption(entry.label if label is None else label, "label")
        if accent:
            self._check_accent("figure(accent=True)")  # before any fitting, and spent last

        pack, styles = self._deck._pack, self._deck._pack.styles[self._deck._mode]
        num, lab = styles[numeral_style], styles[label_style]
        region_box = box(pack, self._layout, region)
        row = pack.grid.row_emu
        numeral_pitch = self._deck._setting(num).pitch  # points
        rows = math.ceil(numeral_pitch * EMU_PER_PT / row)
        numeral_h = rows * row
        label_line = self._deck._setting(lab).pitch
        if numeral_h + label_line * EMU_PER_PT > region_box.h:
            have = region_box.h // row
            raise DoesNotFit(
                f"figure needs {rows} rows for the numeral and one label line "
                f"({float(label_line):.1f} pt), region {region!r} has {have} rows"
            )
        top = Box(region_box.x, region_box.y, region_box.w, numeral_h)
        rest = Box(region_box.x, region_box.y + numeral_h, region_box.w, region_box.h - numeral_h)
        numeral_paras = self._text(num, [value], top, "numeral")
        if accent:
            accent_hex = self._deck._voice.hex(pack.surfaces[self._surface].accent)
            numeral_paras = tuple(
                ParaSpec(
                    runs=tuple(RunSpec(**{**r.__dict__, "color": accent_hex}) for r in p.runs),
                    line_spacing=p.line_spacing,
                    space_before=p.space_before,
                    space_after=p.space_after,
                )
                for p in numeral_paras
            )
        label_paras = self._text(lab, [label], rest, "label")
        if accent:
            self._spend_accent("figure(accent=True)")
        if lab.color[self._surface] in pack.accents:
            self._spend_accent("label")
        self._plan.shapes.append(TextSpec(f"{region}-numeral", top, numeral_paras))
        self._plan.shapes.append(TextSpec(f"{region}-label", rest, label_paras))
        self._used.add(region)
        self._figures += 1
        return self

    def _role_hex(self, role: str, fallback: str) -> str:
        voice = self._deck._voice
        return voice.hex(role) if role in voice.palette else voice.hex(fallback)

    def table(
        self, rows: list[list[str]], header: bool = True, region: str = "main"
    ) -> SlideBuilder:
        """A table of strings: hairline rules under each row, no fills; the header row in
        the label style, each header cell at most caption_exempt_words words (§6.1). Each
        column is as wide as its widest cell allows; rows grow to their tallest cell; the
        table must fit the region (§6.4)."""
        import math

        from keyline.fit import width, wrap

        body_name = self._allowed("table", "body")
        label_name = self._allowed("table", "label") if header else body_name
        region = self._region(region)
        ok = isinstance(rows, list) and rows and all(isinstance(r, list) and r for r in rows)
        if not ok or len({len(r) for r in rows}) != 1:
            raise PenError("a table needs rows: a non-empty list of equally long lists")
        for r in rows:
            for cell in r:
                if not isinstance(cell, str):
                    raise PenError("table cells must be text")
        rows = [
            [self._caption(cell, "header cell") for cell in r]
            if header and i == 0
            else [_line(cell, "table cell", empty=True) for cell in r]
            for i, r in enumerate(rows)
        ]
        styles = self._deck._pack.styles[self._deck._mode]
        row_styles = [
            styles[label_name] if header and i == 0 else styles[body_name] for i in range(len(rows))
        ]
        settings = [self._deck._setting(st) for st in row_styles]
        region_box = box(self._deck._pack, self._layout, region)
        left, right, top, bottom = (Fraction(m, EMU_PER_PT) for m in CELL_MARGINS)
        cols = len(rows[0])
        natural = [
            max(width(settings[i], rows[i][c]) for i in range(len(rows))) + left + right
            for c in range(cols)
        ]
        region_w = Fraction(region_box.w, EMU_PER_PT)
        widths = [n * region_w / sum(natural) for n in natural]
        heights = []
        for i, row in enumerate(rows):
            lines = 0
            for c, cell in enumerate(row):
                self._deck._note_missing(settings[i], cell)
                if cell.strip():
                    lines = max(
                        lines, len(wrap(settings[i], cell, widths[c] - left - right, "table cell"))
                    )
            # B-22 item 5: cell lines at max(1.2, hhea); one more 0.01 mm per row
            heights.append(max(lines, 1) * settings[i].cell_pitch + ROW_ALLOWANCE_PT + top + bottom)
        region_h = Fraction(region_box.h, EMU_PER_PT)
        if sum(heights) > region_h:
            raise DoesNotFit(
                f"table needs {float(sum(heights)):.1f} pt of height, region holds "
                f"{float(region_h):.1f} pt: shorten it or split the slide"
            )
        col_emu = [math.floor(w * EMU_PER_PT) for w in widths[:-1]]
        col_emu.append(region_box.w - sum(col_emu))
        row_emu = [math.ceil(h * EMU_PER_PT) for h in heights]
        cells = tuple(
            tuple((self._para(row_styles[i], text),) for text in row) for i, row in enumerate(rows)
        )
        rule = self._role_hex("hairline", self._surface)
        spec = TableSpec(
            f"{region}-table",
            region_box,
            tuple(col_emu),
            tuple(row_emu),
            cells,
            CELL_MARGINS,
            rule,
            RULE_WIDTH,
        )
        self._plan.shapes.append(spec)
        self._used.add(region)
        return self

    def chart_bar(
        self, evidence_id: str, region: str = "main", highlight: str | None = None
    ) -> SlideBuilder:
        """A column chart of a series entry: muted bars, at most one highlighted category
        in the accent (counted against accent_budget), no legend, light horizontal rules,
        direct data labels, in the voice's text font (§6.1)."""
        label_name = self._allowed("chart_bar", "label")
        region = self._region(region)
        entry = self._entry(evidence_id)
        if entry.series is None:
            raise PenError(f"{evidence_id!r} has a value, not a series; use figure for it")
        categories = [_line(str(c), "category") for c, _v in entry.series]
        index = None
        if highlight is not None:
            highlight = _line(highlight, "highlight")
            if highlight not in categories:
                raise PenError(f"highlight {highlight!r} is not a category of {evidence_id!r}")
            index = categories.index(highlight)
            self._check_accent("chart_bar(highlight=…)")
        values = [v for _c, v in entry.series]
        label = self._deck._pack.styles[self._deck._mode][label_name]
        voice = self._deck._voice
        spec = ChartSpec(
            name=f"{region}-chart",
            box=box(self._deck._pack, self._layout, region),
            categories=tuple(categories),
            values=tuple(float(v) for v in values),
            number_format="#,##0" if all(isinstance(v, int) for v in values) else "#,##0.0",
            bar=self._role_hex("muted", self._surface),
            highlight=index,
            accent=voice.hex(self._deck._pack.surfaces[self._surface].accent),
            text=voice.hex(label.color[self._surface]),
            rule=self._role_hex("hairline", self._surface),
            font=voice.font(label.font),
            size=label.size_hundredths,
        )
        self._plan.shapes.append(spec)
        self._used.add(region)
        if index is not None:
            self._spend_accent("chart_bar(highlight=…)")
        return self

    def image(self, path: str, region: str = "main", *, alt: str) -> SlideBuilder:
        """A picture fitted inside the region, without cropping or distortion, flush to its
        top left; `alt` is required and written as its description."""
        from PIL import Image

        from keyline.geom import Box

        self._allowed("image", styled=False)
        region = self._region(region)
        _check_content(path, "image path")
        alt = _line(alt, "alt")
        try:
            with Image.open(path) as im:
                px_w, px_h = im.size
        except OSError as exc:
            raise PenError(f"image {Path(path).name!r} cannot be read: {exc}") from exc
        region_box = box(self._deck._pack, self._layout, region)
        scale = min(Fraction(region_box.w, px_w), Fraction(region_box.h, px_h))
        fitted = Box(region_box.x, region_box.y, int(px_w * scale), int(px_h * scale))
        self._plan.shapes.append(PictureSpec(f"{region}-image", fitted, str(path), alt))
        self._used.add(region)
        return self

    def attribution(self, text: str) -> SlideBuilder:
        """Who said the quote: on quote slides, in the label style, in its own region."""
        style = self._allowed("attribution")
        region = self._region("main")
        self._place(region, style, [self._caption(text, "attribution")], "attribution")
        return self

    def source(self, text: str | None = None) -> SlideBuilder:
        """The source line. Without text: the sources of the brief slide's evidence
        (without a brief, of the evidence the slide's verbs used), first-seen order,
        joined with "; " and prefixed "Source: "."""
        from keyline.rules._common import line_kind

        self._allowed("source")
        if "source" in self._lines:
            raise PenError("this slide already has a source line")
        if text is None:
            ids = self._brief_slide.evidence if self._brief_slide else tuple(self._evidence_used)
            if not ids or self._deck._evidence is None:
                raise PenError("no evidence to source on this slide; give the source text")
            entries = self._deck._evidence.entries
            text = "; ".join(dict.fromkeys(entries[i].source for i in ids))
        text = _line(text, "source")
        if line_kind(self._as_paragraph(text), self._deck._cfg) != "source":
            text = f"Source: {text}"
        self._lines["source"] = text
        self._footer()
        return self

    def note(self, text: str | None = None) -> SlideBuilder:
        """The note line. Without text on a cover or close slide: the primary evidence
        file's disclosure. A text without a note prefix gets "Note: "."""
        from keyline.rules._common import line_kind

        self._allowed("note")
        if "note" in self._lines:
            raise PenError("this slide already has a note line")
        if text is None:
            evidence = self._deck._evidence
            disclosure = evidence.product.disclosure if evidence else ""
            if self._role.name not in ("cover", "close") or not disclosure:
                raise PenError("no disclosure to write here; give the note text")
            text = disclosure
        text = _line(text, "note")
        if line_kind(self._as_paragraph(text), self._deck._cfg) != "note":
            text = f"Note: {text}"
        self._lines["note"] = text
        self._footer()
        return self

    def notes(self, text: str) -> SlideBuilder:
        """Speaker notes."""
        self._plan.notes = "\n".join(_paragraphs(text, "notes"))
        return self

    @staticmethod
    def _as_paragraph(text: str):
        from keyline.model import Paragraph, Run

        return Paragraph(runs=(Run(text, 1200),))
