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
