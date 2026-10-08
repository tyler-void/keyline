"""AC-13(b), fit stress (spec 002 §6.4, B-21, B-24, B-25; tasks T-30 and the A2 fixes):

    python tools/fit_stress.py [OUT_DIR]

For each of the six portable families (a test-only voice: Swiss neutral's palette with the
family as display and text font; inline voices may use any of them, audit 05) in each
mode, the pen builds a deck in which every text the estimator checks sits at the longest
length the pen accepts:
one more word (or, for a numeral, one more digit) is refused. The texts are:
- the headline on every slide;
- `text` in every style a role allows, in every text region of every layout;
- `bullets` (bullets_max items);
- `table` (a header row and three body rows, two columns);
- `figure` (the numeral and its label; the numerals come from an evidence file written
  here, one entry per length);
- `attribution`;
- the footer's source and note lines.
The words come from an English corpus, and from a Vietnamese one in title case, so stacked
capitals (Ẩ, Ẳ, Ấ) open many lines (B-25, audit 06 FX-25); the Vietnamese texts are set in
the families whose twin has every one of its letters (Caladea lacks most: the pen warns and
the fit promises nothing there, B-25 item 1). Items grow in turn until none takes one more
word. The refusal that stops an item is the
estimator's (DoesNotFit) or a word cap (caption_exempt_words, a PenError); both are
printed. A component the pen refuses even at its shortest is listed, not built. Chart
text is laid out by the chart engine, not the estimator, so charts are not stressed.

Each stress slide is written once per text region, keeping only that region's shapes,
and once with no shapes (the control). The decks are rendered with LibreOffice at
1280 px, its version printed (B-7). A text's ink is every pixel that differs from the
control by more than 10% (26 of 255) in any channel. The verdict is B-24's as amended by
B-25 item 2: no ink past the right or bottom edge of its region box by more than 2 px, nor
past the left edge by more than 2 px plus the text's left allowance, nor past the top edge
by more than 2 px plus its top allowance. The left allowance is the most negative left
side bearing among the text's characters × size; the top allowance is size × (the highest
glyph top among its characters − the first baseline, 1.2 em × line spacing − 0.2 em, B-21)
when positive. Both are read from the twin with fontTools, over the characters as set
(upper-cased for caps styles, bullet markers included), for each style the region uses. The
script prints each text's ink box against its region box, and exits 0 when the verdict
holds, 1 when it does not, and 2 when it cannot run (no LibreOffice, or a family resolves
to something other than its metric twin).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field, replace
from pathlib import Path

from lxml import etree

from keyline import render as render_mod
from keyline.config import load as load_config
from keyline.fit import Setting, load_table
from keyline.packs import resolve
from keyline.pen import Deck, DoesNotFit, PenError

PACK = "swiss"
MODES = ("presented", "read")
FAMILIES = tuple(family for family, _twin in load_config().portable_fonts)  # B-24
TOLERANCE_PX = 2
PX_PER_PT = 1280 / 960  # the render is 1280 px across a 960 pt slide
INK = 26  # 10% of 255
SLIDE_W, SLIDE_H = 12192000, 6858000
NUMERAL_DIGITS = 40  # evidence entries n1 … n40: numerals of 1 … 40 digits
TABLE_ROWS, TABLE_COLS = 4, 2  # a header row and three body rows
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
SHAPES = {f"{{{P}}}{t}" for t in ("sp", "graphicFrame", "pic", "cxnSp", "grpSp")}

CORPUS = (
    "The harbour library opens early on market days so that fishers can return the nets "
    "they borrowed before the tide turns and the stalls fill with crates of lemons, bread "
    "and salted cod. Volunteers keep a ledger of every loan in pencil, and each spring "
    "they copy the worn pages into a fresh book while children sort the returned hooks by "
    "size. Nobody remembers who first suggested lending tools as well as novels, but the "
    "shelf of chisels, planes and clamps now draws more visitors than the reading room, "
    "and the caretaker says the smell of linseed oil has replaced the smell of old paper. "
    "On quiet afternoons the reading room still fills with students who spread their maps "
    "across the long oak tables and argue about the fastest route across the northern "
    "passes, while an elderly clockmaker repairs the brass barometer that hangs above the "
    "counter and quietly predicts rain for the whole week."
)
# B-25 (audit 06 FX-25): Vietnamese, title case, stacked capitals at the start of words
VIETNAMESE = (
    "Ẩm Thực Miền Tây Ẩn Chứa Những Hương Vị Ấm Áp Của Mùa Nước Nổi. Ở Chợ Nổi Cái Răng, "
    "Người Bán Ẵm Con Nhỏ Trên Thuyền, Ổn Định Từ Sáng Sớm Đến Trưa. Ếch Đồng Xào Lăn, Ốc "
    "Bươu Nướng Tiêu Và Ổi Chín Được Bày Bán Ồn Ào Khắp Bến. Ẩn Mình Sau Hàng Dừa Là Những "
    "Ấp Nhỏ, Nơi Ông Bà Kể Chuyện Ầm Ĩ Bên Ấm Trà. Ừ, Ở Đây Ai Cũng Ứng Xử Hiền Hòa, Ửng "
    "Hồng Đôi Má Khi Được Khen. Ẩn Số Của Vùng Đất Này Là Sự Ổn Định Và Ấm Áp Trong Từng "
    "Bữa Cơm. Ắt Hẳn Ai Đến Một Lần Cũng Muốn Trở Lại, Khi Ẳng Ẳng Tiếng Chó Sủa Đầu Làng "
    "Và Ẩn Hiện Ánh Đèn Dầu Trên Những Chiếc Ghe Về Muộn."
)
CORPORA = {"English": CORPUS.split(), "Vietnamese": VIETNAMESE.split()}
WORDS = CORPORA["English"]


def words(n: int, start: int, corpus: str = "English") -> str:
    found = CORPORA[corpus]
    return " ".join(found[(start + i) % len(found)] for i in range(n))


def numeral(digits: int) -> str:
    """A numeral of `digits` digits, grouped by thousands: 1, 12, 123, 1,234, …"""
    return f"{int(('1234567890' * 5)[:digits]):,}"


def write_evidence(path: Path) -> Path:
    """The evidence file the figures draw their numerals from."""
    lines = ["schema = 1", "", "[product]", 'name = "Fit stress"', "fictional = false"]
    for d in range(1, NUMERAL_DIGITS + 1):
        lines += [
            "",
            "[[evidence]]",
            f'id = "n{d}"',
            f'value = "{numeral(d)}"',
            'label = "a numeral"',
            'source = "tools/fit_stress.py"',
        ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _items(counts, start: int, corpus: str) -> list[str]:
    out, at = [], start
    for n in counts:
        out.append(words(n, at, corpus))
        at += n
    return out


@dataclass(frozen=True)
class Fill:
    """What fills a region. Each item is the next counts[i] words of the corpus from word
    `start` on, except a figure's first item, which is its numeral's digit count."""

    kind: str  # headline, text, bullets, table, figure, attribution or footer
    counts: tuple[int, ...]
    start: int
    style: str = ""  # text only
    bounds: tuple[str, ...] = ()  # per item, what refused one more: "fit" or "cap"
    corpus: str = "English"

    @property
    def texts(self) -> list[str]:
        if self.kind == "figure":
            return [numeral(self.counts[0]), words(self.counts[1], self.start, self.corpus)]
        return _items(self.counts, self.start, self.corpus)

    @property
    def amount(self) -> str:
        if self.kind == "figure":
            return f"{self.counts[0]}d {self.counts[1]}w"
        return f"{sum(self.counts)}w"

    def longer(self, i: int, by: int = 1) -> Fill:
        """The same fill with `by` more in item i (the later items move on)."""
        counts = list(self.counts)
        counts[i] += by
        return replace(self, counts=tuple(counts))


@dataclass
class Stress:
    """One stress slide: its headline, what fills each region, and what the pen refused
    even at its shortest."""

    role: str
    layout: str
    variant: str | None
    headline: Fill | None = None
    fills: dict[str, Fill] = field(default_factory=dict)
    refused: list[tuple[str, str, str]] = field(default_factory=list)  # region, kind, why


@dataclass
class Result:
    mode: str
    family: str
    slide: int
    layout: str
    region: str
    what: str
    amount: str
    bound: str
    region_px: tuple[float, float, float, float]
    ink_px: tuple[int, int, int, int] | None
    left_allowance: float = 0.0  # px: the text's most negative left side bearing x size
    top_allowance: float = 0.0  # px: how far its highest glyph rises above the first line
    corpus: str = "English"

    @property
    def edges(self) -> dict[str, float]:
        """How far the ink reaches past each edge of the region box, in px (negative:
        inside)."""
        x0, y0, x1, y1 = self.region_px
        ix0, iy0, ix1, iy1 = self.ink_px
        return {"left": x0 - ix0, "top": y0 - iy0, "right": ix1 - x1, "bottom": iy1 - y1}

    @property
    def overflow(self) -> float | None:
        """How far the ink reaches outside the region box, in px (negative: inside)."""
        return None if self.ink_px is None else max(self.edges.values())

    @property
    def edge(self) -> str:
        return "" if self.ink_px is None else max(self.edges, key=self.edges.get)

    @property
    def beyond(self) -> dict[str, float]:
        """How far the ink reaches past each edge, less that edge's allowance, in px."""
        e = self.edges
        return dict(e, left=e["left"] - self.left_allowance, top=e["top"] - self.top_allowance)

    @property
    def excess(self) -> float | None:
        """B-24 and B-25 item 2: how far the ink reaches past its edges' limits, in px,
        where 0 is exactly 2 px out (the left and top limits are 2 px plus the left and
        top allowances); None without ink."""
        if self.ink_px is None:
            return None
        return max(self.beyond.values()) - TOLERANCE_PX

    @property
    def excess_edge(self) -> str:
        beyond = self.beyond
        return max(beyond, key=beyond.get)


# -- the fonts and the engine -------------------------------------------------------------


def fc_family(family: str) -> str | None:
    if shutil.which("fc-match") is None:
        return None
    out = subprocess.run(["fc-match", "-f", "%{family}", family], capture_output=True, text=True)
    return out.stdout.split(",")[0].strip() or None


def covers(family: str, corpus: str) -> bool:
    """Whether the family's twin has every letter of the corpus, in both cases and both
    weights."""
    letters = {ord(c) for c in VIETNAMESE if not c.isspace()} if corpus == "Vietnamese" else set()
    letters |= {ord(c.upper()) for c in map(chr, letters)}
    return all(letters <= set(load_table(family, w).advances) for w in ("regular", "bold"))


def stressed() -> list[tuple[str, str, str]]:
    """(mode, family, corpus) for every stress deck; a corpus only in the families that
    cover it."""
    return [(m, f, c) for m in MODES for c in CORPORA for f in FAMILIES if covers(f, c)]


def unready() -> str | None:
    """Why the stress cannot run here, or None."""
    if render_mod.find_soffice() is None or render_mod.find_rasterizer() is None:
        return "LibreOffice or a PDF rasterizer is not installed"
    for family in FAMILIES:
        twin = load_table(family, "regular").twin
        got = fc_family(family)
        if got is None or got.casefold() != twin.casefold():
            return f"{family} resolves to {got or 'nothing'}, not its twin {twin}"
    return None


def voice_file(directory: Path, family: str) -> str:
    """A test-only voice: Swiss neutral's palette, `family` as display and text font."""
    neutral = resolve(PACK).directory / "voices" / "neutral.toml"
    name = family.lower().replace(" ", "-")
    text = neutral.read_text(encoding="utf-8").replace('name = "neutral"', f'name = "{name}"')
    path = Path(directory) / f"{name}.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace('"Arial"', f'"{family}"'), encoding="utf-8")
    return str(path.resolve())


_fonts: dict = {}
_sidebearings: dict = {}
_tops: dict = {}


def _font(family: str, weight: str):
    """The twin that fontconfig picks for the family and weight, opened with fontTools."""
    from fontTools.ttLib import TTFont

    if (family, weight) not in _fonts:
        style = "Bold" if weight == "bold" else "Regular"
        path = subprocess.run(
            ["fc-match", "-f", "%{file}", f"{family}:style={style}"],
            capture_output=True,
            text=True,
        ).stdout
        _fonts[family, weight] = TTFont(path)
    return _fonts[family, weight]


def left_bearings(family: str, weight: str) -> tuple[dict, int]:
    """(codepoint -> left side bearing in font units, units per em) of the twin that
    fontconfig picks for the family and weight."""
    if (family, weight) not in _sidebearings:
        font = _font(family, weight)
        hmtx = font["hmtx"]
        bearings = {cp: hmtx[glyph][1] for cp, glyph in font.getBestCmap().items()}
        _sidebearings[family, weight] = (bearings, font["head"].unitsPerEm)
    return _sidebearings[family, weight]


def glyph_top(family: str, weight: str, ch: str) -> float:
    """How far the twin's glyph for `ch` rises above the baseline, in em (0 for a glyph
    without outline, or one the twin lacks: a fallback font sets it)."""
    from fontTools.pens.boundsPen import BoundsPen

    key = family, weight, ch
    if key not in _tops:
        font = _font(family, weight)
        glyph = font.getBestCmap().get(ord(ch))
        top = 0.0
        if glyph is not None:
            glyphs = font.getGlyphSet()
            pen = BoundsPen(glyphs)
            glyphs[glyph].draw(pen)
            if pen.bounds is not None:
                top = pen.bounds[3] / font["head"].unitsPerEm
        _tops[key] = top
    return _tops[key]


def styles_of(pack, mode: str, stress: Stress, fill: Fill) -> list[str]:
    """The style names a filled region sets its text in."""
    role = pack.roles[stress.role]
    allowed = role.components[mode]
    return {
        "headline": [role.title],
        "text": [fill.style],
        "bullets": list(allowed.get("bullets", ())[:1]),
        "table": ["body", "label"],
        "figure": ["numeral", "label"],
        "attribution": list(allowed.get("attribution", ())[:1]),
        "footer": list(allowed.get("source", ())[:1]),
    }[fill.kind]


def _shown(style, fill: Fill) -> set[str]:
    """The characters a style sets for a fill: upper-cased for caps, bullet markers in."""
    text = "".join(fill.texts) + (style.bullet_marker if fill.kind == "bullets" else "")
    return {ch for ch in (text.upper() if style.caps else text) if not ch.isspace()}


def left_allowance(pack, mode: str, voice, stress: Stress, fill: Fill) -> float:
    """B-24's left allowance in px: the most negative left side bearing among the text's
    characters x size, over each style the region uses (a character the twin lacks is
    set in a fallback font and counts as 0)."""
    worst = 0.0
    for name in styles_of(pack, mode, stress, fill):
        style = pack.styles[mode][name]
        bearings, upm = left_bearings(voice.font(style.font), style.weight)
        lsb = min((bearings.get(ord(ch), 0) for ch in _shown(style, fill)), default=0)
        worst = max(worst, -lsb / upm * float(style.size_pt) * PX_PER_PT)
    return worst


def top_allowance(pack, mode: str, voice, stress: Stress, fill: Fill) -> float:
    """B-25 item 2's top allowance in px: size x (the highest glyph top among the text's
    characters - the first baseline) when positive, over each style the region uses."""
    worst = 0.0
    for name in styles_of(pack, mode, stress, fill):
        style = pack.styles[mode][name]
        family = voice.font(style.font)
        top = max((glyph_top(family, style.weight, ch) for ch in _shown(style, fill)), default=0)
        setting = Setting(family, style.weight, style.size_pt, line_spacing=style.line_spacing)
        over = top * float(style.size_pt) - float(setting.first_baseline)
        worst = max(worst, over * PX_PER_PT)
    return worst


# -- the longest texts the pen accepts ----------------------------------------------------


def apply(builder, region: str, fill: Fill) -> None:
    """Fill a region of a slide with the pen's verbs."""
    texts = fill.texts
    if fill.kind == "text":
        builder.text(texts[0], style=fill.style, region=region)
    elif fill.kind == "bullets":
        builder.bullets(texts, region=region)
    elif fill.kind == "table":
        rows = [texts[r * TABLE_COLS : (r + 1) * TABLE_COLS] for r in range(TABLE_ROWS)]
        builder.table(rows, region=region)
    elif fill.kind == "figure":
        builder.figure(f"n{fill.counts[0]}", region=region, label=texts[1])
    elif fill.kind == "attribution":
        builder.attribution(texts[0])
    else:
        builder.source(texts[0]).note(texts[1])


def refusal(deck: Deck, stress: Stress, region: str, fill: Fill) -> str | None:
    """None when the pen accepts `fill` in `region` of a slide like `stress` (on a scratch
    deck, which is never saved); else "fit" (DoesNotFit) or "cap: <why>" (PenError)."""
    try:
        if fill.kind == "headline":
            deck.add(stress.role, fill.texts[0], variant=stress.variant)
        else:
            apply(deck.add(stress.role, "Stress", variant=stress.variant), region, fill)
    except DoesNotFit:
        return "fit"
    except PenError as exc:
        return f"cap: {exc}"
    return None


def longest(fill: Fill, refuse) -> Fill | str:
    """The fill grown in turn, item by item, by 16, then 8, … then 1, until no item takes
    one more: the longest the pen accepts, with what refused each item's next step. The
    refusal itself when the pen refuses even the shortest fill. An item that grows moves
    the words of the items after it, so after any growth every item is tried again."""
    why = refuse(fill)
    if why:
        return why
    bounds = [""] * len(fill.counts)
    step = 16
    while step:
        full: set[int] = set()
        i = 0
        while len(full) < len(fill.counts):
            j = i % len(fill.counts)
            i += 1
            if j in full:
                continue
            trial = fill.longer(j, step)
            why = refuse(trial)
            if why is None:
                fill = trial
                full.clear()
            else:
                full.add(j)
                bounds[j] = why.split(":")[0]
        step //= 2
    return replace(fill, bounds=tuple(bounds))


def _kinds(allowed: dict, region: str) -> list[tuple[str, str]]:
    kinds = [("text", s) for s in allowed.get("text", ())]
    kinds += [(k, "") for k in ("bullets", "table", "figure") if k in allowed]
    if "attribution" in allowed and region == "main":
        kinds.append(("attribution", ""))
    return kinds


def _shortest(kind: str, style: str, bullets_max: int) -> Fill:
    n = {"bullets": bullets_max, "table": TABLE_ROWS * TABLE_COLS, "figure": 2}.get(kind, 1)
    return Fill(kind, (1,) * n, 0, style)


def plan(mode: str, voice: str, evidence: Path, corpus: str = "English") -> list[Stress]:
    """The stress slides for a mode and voice, each text at its longest, in words of the
    corpus."""
    pack = resolve(PACK)
    scratch = Deck(PACK, mode, voice, evidence=str(evidence))
    bullets_max = load_config(mode).as_int("bullets_max")
    stresses: list[Stress] = []
    start = 0
    for role in pack.roles.values():
        allowed = role.components[mode]
        for layout in role.layouts:
            variant = layout.rsplit(":", 1)[-1] if layout.count(":") == 2 else None
            per_region: dict[str, list[tuple[str, str]]] = {}
            text_regions = [r for r in pack.regions[layout] if r not in ("title", "footer")]
            for k, region in enumerate(text_regions):
                kinds = _kinds(allowed, region)
                # rotated per region, so no slide carries two figures (numerals_max)
                per_region[region] = (
                    kinds[k % len(kinds) :] + kinds[: k % len(kinds)] if kinds else []
                )
            n_slides = max([len(v) for v in per_region.values()] + [1])
            for j in range(n_slides):
                s = Stress(role.name, layout, variant)
                wanted = [("title", Fill("headline", (1,), 0))]
                for region, kinds in per_region.items():
                    if j < len(kinds):
                        wanted.append((region, _shortest(*kinds[j], bullets_max)))
                if "footer" in pack.regions[layout] and "source" in allowed:
                    wanted.append(("footer", Fill("footer", (1, 1), 0)))
                for region, fill in wanted:
                    start += 7  # each text starts at its own place in the corpus
                    got = longest(
                        replace(fill, start=start, corpus=corpus),
                        lambda f, r=region, s=s: refusal(scratch, s, r, f),
                    )
                    if isinstance(got, str):
                        s.refused.append((region, fill.kind, got))
                    elif region == "title":
                        s.headline = got
                    else:
                        s.fills[region] = got
                stresses.append(s)
    return stresses


# -- the deck, its copies and the render --------------------------------------------------


def build(
    stresses: list[Stress], mode: str, voice: str, evidence: Path, path: Path
) -> list[tuple[int, str]]:
    """The deck: each stress slide once per text region, then once as the control.
    Returns (stress index, kept region or "") per slide."""
    deck = Deck(PACK, mode, voice, evidence=str(evidence))
    order: list[tuple[int, str]] = []
    for i, s in enumerate(stresses):
        for keep in ["title", *s.fills, ""]:
            b = deck.add(s.role, s.headline.texts[0], variant=s.variant)
            for region, fill in s.fills.items():
                apply(b, region, fill)
            order.append((i, keep))
    raw = Path(path).with_suffix(".full.pptx")
    deck.save(str(raw))
    src = zipfile.ZipFile(raw)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as out:
        for info in src.infolist():
            data = src.read(info.filename)
            name = info.filename
            if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                index = int(name[len("ppt/slides/slide") : -len(".xml")]) - 1
                data = _keep_only(data, order[index][1])
            out.writestr(info, data)
    raw.unlink()
    return order


def _keep_only(xml: bytes, keep: str) -> bytes:
    """The slide with only the shapes of region `keep` (its placeholder, or the pen's
    `<region>-table`, `<region>-numeral` and `<region>-label`); none when keep is ""."""
    root = etree.fromstring(xml)
    tree = root.find(f"{{{P}}}cSld/{{{P}}}spTree")
    for child in list(tree):
        if child.tag in SHAPES:
            name = child.find(f".//{{{P}}}cNvPr").get("name")
            if not keep or (name != keep and not name.startswith(f"{keep}-")):
                tree.remove(child)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def ink_box(image, control):
    from PIL import ImageChops

    diff = ImageChops.difference(image.convert("RGB"), control.convert("RGB"))
    r, g, b = diff.split()
    strongest = ImageChops.lighter(ImageChops.lighter(r, g), b)
    return strongest.point(lambda v: 255 if v > INK else 0).getbbox()


def measure(
    mode: str, family: str, work: Path, corpus: str = "English"
) -> tuple[str, list[Result], list[str]]:
    """The render's LibreOffice version, a Result per stressed text, and a line per
    component the pen refused even at its shortest, for one mode, portable family and
    corpus."""
    from PIL import Image

    pack = resolve(PACK)
    slug = f"{family.lower().replace(' ', '-')}-{corpus.lower()}"
    voice = voice_file(work / "voices", family)
    evidence = write_evidence(work / f"evidence-{mode}-{slug}.toml")
    stresses = plan(mode, voice, evidence, corpus)
    deck = work / f"stress-{mode}-{slug}.pptx"
    order = build(stresses, mode, voice, evidence, deck)
    rendered = render_mod.render(deck, work / f"{mode}-{slug}", engine="libreoffice")
    voice_obj = pack.voice(voice)
    images = [Image.open(p) for p in rendered.slides]
    if len(images) != len(order):
        raise SystemExit(f"fit_stress: {len(images)} pages for {len(order)} slides")
    controls = {i: images[k] for k, (i, keep) in enumerate(order) if not keep}
    results = []
    for k, (i, keep) in enumerate(order):
        if not keep:
            continue
        s, img = stresses[i], images[k]
        sx, sy = img.width / SLIDE_W, img.height / SLIDE_H
        b = pack.region_box(s.layout, keep)
        region_px = (b.x * sx, b.y * sy, (b.x + b.w) * sx, (b.y + b.h) * sy)
        fill = s.headline if keep == "title" else s.fills[keep]
        what = {
            "headline": f"headline ({pack.roles[s.role].title})",
            "text": f"text ({fill.style})",
            "footer": "source + note",
        }.get(fill.kind, fill.kind)
        bound = "+".join(sorted(set(fill.bounds)))
        results.append(
            Result(
                mode,
                family,
                k + 1,
                s.layout,
                keep,
                what,
                fill.amount,
                bound,
                region_px,
                ink_box(img, controls[i]),
                left_allowance(pack, mode, voice_obj, s, fill),
                top_allowance(pack, mode, voice_obj, s, fill),
                corpus,
            )
        )
    refused = [
        f"{mode} {family} {corpus}: {s.layout} {region}: {kind} refused at its shortest ({why})"
        for s in stresses
        for region, kind, why in s.refused
    ]
    return rendered.version, results, refused


def report(version: str, results: list[Result], refused: list[str]) -> tuple[list[str], bool]:
    lines = [f"LibreOffice: {version}", f"ink threshold: > {INK} of 255 in any channel", ""]
    lines.append(
        "mode       family           corpus     slide layout                    region  "
        "text                  amount  bound    region box (px)              ink box (px)"
        "          left allow  top allow  outside  edge"
    )
    for r in results:
        box_s = "[{:.1f}, {:.1f}, {:.1f}, {:.1f}]".format(*r.region_px)
        ink_s = "[{}, {}, {}, {}]".format(*r.ink_px) if r.ink_px else "no ink"
        out = f"{r.overflow:+.1f}" if r.overflow is not None else "n/a"
        lines.append(
            f"{r.mode:<10} {r.family:<16} {r.corpus:<10} {r.slide:>5} {r.layout:<25} "
            f"{r.region:<7} {r.what:<20} {r.amount:>7}  {r.bound:<7}  {box_s:<28} "
            f"{ink_s:<21} {r.left_allowance:>10.1f} {r.top_allowance:>10.1f}  {out:>7}  {r.edge}"
        )
    lines.append("")
    lines.append("not stressed (the twin lacks letters of the corpus; B-25 item 1):")
    lines += [f"  {c}: {f}" for c in CORPORA for f in FAMILIES if not covers(f, c)] or ["  none"]
    lines.append("")
    lines.append("refused at the shortest (not built):")
    lines += [f"  {line}" for line in refused] or ["  none"]
    blank = [r for r in results if r.ink_px is None]
    inked = [r for r in results if r.ink_px is not None]
    over = [r for r in inked if r.excess > 0]
    ok = not blank and not over
    lines.append("")
    lines.append(f"{len(results)} texts, {len(blank)} without ink; per edge, the most outside:")
    for edge in ("left", "top", "right", "bottom"):
        most = max(inked, key=lambda r: r.edges[edge])
        extra = {
            "left": f", left allowance {most.left_allowance:.1f} px",
            "top": f", top allowance {most.top_allowance:.1f} px",
        }.get(edge, "")
        lines.append(
            f"  {edge:<6} {most.edges[edge]:+.1f} px ({most.mode} {most.family} {most.corpus}, "
            f"slide {most.slide}, {most.layout} {most.region}{extra})"
        )
    closest = max(inked, key=lambda r: r.excess)
    lines.append(
        f"closest to a limit: {closest.excess:+.1f} px from it ({closest.mode} "
        f"{closest.family} {closest.corpus}, slide {closest.slide}, {closest.layout} "
        f"{closest.region}, {closest.excess_edge})"
    )
    lines.append(f"past a limit: {len(over)} text(s)")
    lines += [
        f"  {r.mode} {r.family} {r.corpus}, slide {r.slide}, {r.layout} {r.region} ({r.what}): "
        f"{r.excess:+.1f} px past the {r.excess_edge} limit"
        for r in over
    ]
    lines.append(
        f"verdict, AC-13(b) as amended by B-24 and B-25 (right, bottom at {TOLERANCE_PX} px; "
        f"left and top at {TOLERANCE_PX} px + their allowances): {'PASS' if ok else 'FAIL'}"
    )
    return lines, ok


def main(argv: list[str]) -> int:
    reason = unready()
    if reason:
        sys.stderr.write(f"fit_stress: cannot run: {reason}\n")
        return 2
    with tempfile.TemporaryDirectory(prefix="keyline-fit-stress-") as tmp:
        work = Path(argv[0]) if argv else Path(tmp)
        work.mkdir(parents=True, exist_ok=True)
        version, results, refused = "", [], []
        for mode, family, corpus in stressed():
            version, got, no = measure(mode, family, work, corpus)
            results.extend(got)
            refused.extend(no)
        lines, ok = report(version, results, refused)
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
