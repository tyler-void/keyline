# The OOXML adapter

`keyline lint` reads the `.pptx` package directly with lxml (D-004). This page lists
what the adapter resolves, in which order, and where it knowingly differs from
PowerPoint. The source of truth for each order is `specs/001-lint-core/plan.md` §2 and
the spec's amendment log (A-4, A-5, A-6).

## Colors

Color elements:

| element | result |
|---|---|
| `a:srgbClr@val` | that RGB |
| `a:sysClr@lastClr` | the cached system color |
| `a:schemeClr@val` | `bg1 tx1 bg2 tx2` (and the accents) map through the clrMap, then the theme's `a:clrScheme`. `phClr` takes the color carried by the referencing `fillRef`/`fontRef`/`bgRef` |
| `a:prstClr`, `a:hslClr`, `a:scrgbClr` | unresolved (`None`) and an `adapter-unresolved` advisory |

The clrMap is the master's `p:clrMap`, replaced by `p:clrMapOvr/a:overrideClrMapping`
on the layout and then on the slide. `a:masterClrMapping` keeps the inherited map.

Transforms, applied in document order (`val` is in 1/1000 of a percent):

| transform | formula |
|---|---|
| `lumMod`, `lumOff` | convert to HSL; `L = L · lumMod`, then `L = L + lumOff`; clamp to [0, 1]; back to RGB |
| `tint` | per sRGB channel: `c + (1 − c) · (1 − tint)` |
| `shade` | per sRGB channel: `c · shade` |
| `alpha` | `100%` is ignored. Anything lower is unresolved, because an unblended color would give a false contrast |
| anything else (`satMod`, `hueOff`, `gamma`, …) | unresolved, with `transform:<name>` in the advisory |

**Uncalibrated (plan R-4).** Implementations disagree on `tint` and `shade` (sRGB vs
linear light). keyline applies them per sRGB channel. Nobody has compared the results
with PowerPoint yet.

## Text properties (A-4, A-11)

Size, bold, italic, caps and spacing resolve through the A-4 cascade below. `N` is
`a:pPr@lvl + 1`. **Color and latin font (A-11)** use the same sources, except that the
shape's `p:style/a:fontRef` comes third, right after the shape's own `lstStyle` and before
the layout. Both OfficeCLI and LibreOffice render this way (audit 02, FX-3).

1. the run's `a:rPr` (also `a:fld` runs)
2. the shape's `p:txBody/a:lstStyle/a:lvlNpPr/a:defRPr`
3. the matched layout placeholder's `lstStyle` (placeholders only)
4. the matched master placeholder's `lstStyle` (placeholders only)
5. the master `p:txStyles`: `titleStyle` for `title`/`ctrTitle`, `bodyStyle` for other
   placeholders, `otherStyle` for non-placeholder shapes
6. `p:presentation/p:defaultTextStyle`
7. color only: `tx1` through the clrMap

`+mj-lt` and `+mn-lt` map to the theme's major and minor latin fonts. Other theme font
tokens are unresolved. A size that is still unknown is `None`, and the adapter
reports `adapter-unresolved` (`size`). Rules skip those runs.

**Unverified against PowerPoint.** A-4 leaves `a:pPr/a:defRPr` out of the cascade.
The plan says PowerPoint ignores it for runs, and that text boxes take their defaults
from `defaultTextStyle`. Nobody has checked either claim in PowerPoint.

**Not applied:** `a:bodyPr/a:normAutofit@fontScale`. Sizes are nominal (plan R-2).

## Shape fill

1. the shape's `p:spPr`: `solidFill` → solid; `gradFill` → `gradient`; `noFill` →
   `none`; `blipFill`/`pattFill` → `unknown`; `grpFill` → the enclosing group's fill
2. the matched layout placeholder's `p:spPr`, then the master placeholder's
3. `p:style/a:fillRef`: `idx="0"` → none; otherwise the theme `fillStyleLst` entry
   (1-based; ≥ 1001 uses `bgFillStyleLst`). `phClr` takes the fillRef's color
4. `none`

A picture's fill is `unknown`. A `graphicFrame` has no fill; rules treat it as visible
content by its kind.

## Background (A-5)

The first `p:cSld/p:bg` on the slide, then the layout, then the master:

- `p:bgPr` with `solidFill` → solid.
- `p:bgRef` with a solid theme background style → solid (`phClr` is the bgRef color).
- `gradFill`, `blipFill`, `pattFill` → `unknown`; rules that need the background skip
  it with an advisory.
- `p:bgPr/a:noFill`, or no `p:bg` anywhere → `#FFFFFF`, plus one `adapter-unresolved`
  advisory (`background-default`). PowerPoint paints these white.

## Placeholders (A-6)

- Slide → layout: by `idx` first. If no layout placeholder has that idx, the first with
  the same `type` (keyline-only fallback; python-pptx 1.0.2 matches by idx only).
- Layout → master: by type, after mapping `ctrTitle→title` and `subTitle, obj, body,
  tbl, chart, dgm, media, clipArt, pic→body` (`dt ftr sldNum hdr` unchanged).
- The slide `ph@type` defaults to `obj`, `ph@idx` to `0`.

## Geometry

- The shape's own `a:xfrm` (`p:xfrm` for graphic frames), else the matched layout
  placeholder's, else the master's. Still missing → `adapter-unresolved` (`geometry`).
- Groups compose from the innermost out: `x' = off.x + (x − chOff.x) · ext.cx /
  chExt.cx` (a zero `chExt` means scale 1), with exact fractions. Group flips mirror
  the child's center, and group rotation turns it about the group's center and adds to
  the child's rotation.
- Rules use the axis-aligned bounding box of the rotated rectangle. Multiples of 90°
  are exact; other angles use float trig once, and each edge is rounded to EMU.

## Numbers (A-17)

Every numeric attribute goes through one parser (`ooxml/numbers.py`). It accepts
integers, decimals (`25000.0`, `1.5e6`) and, for percentage attributes such as `lumMod`,
`tint` and `alpha`, the Strict form `N%` (`75%` = 75000). A value that does not parse,
or lies outside the ST_Coordinate range (±27273042316900), is dropped. An unparseable
color transform is skipped, and a transform with a missing geometry value leaves the
shape without a box. Each dropped value gives one `adapter-unresolved` advisory.

Strict packages (`purl.oclc.org` namespaces or `conformance="strict"`) exit 1 with
"Strict Open XML (ISO/IEC 29500 Strict) is not supported yet".
