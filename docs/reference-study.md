# Reference study for spec 003

How do current slide tools get a designed look, and which of their methods fit keyline?
This study is the input the auditor drafts spec 003 from. It is research only: nothing in
keyline's code changes, and no tool studied here was installed or run.

- **The gaps to close** are the six causes of run 1's dated look ("Tyler's verdict on the
  look", `specs/002-skill-pack/report.md`):
  1. only Office-core fonts;
  2. one composition and one flat background on every slide;
  3. a rule under every title;
  4. content that hugs the top of the slide;
  5. charts that look like spreadsheet defaults;
  6. no pictures.
- **keyline's constraints:**
  - measured gates and byte-identical output (`docs/constitution.md`, VII; spec 002
    §6.5);
  - an editable `.pptx` that opens in PowerPoint 365, PowerPoint for the web, Google
    Slides and Canva. This is the auditor's goal for this study. Note that
    `docs/vision.md:37` makes parity with Google Slides beyond a documented portable
    subset a non-goal. Spec 003 has to reconcile the two.

## Method

- **Clones.** Each repository was cloned with `git clone --depth 1` on 2026-10-30 into a
  scratch folder outside the keyline checkout and the demo folders. Nothing in them was
  installed, built or run.
- **Reading.** One read-only agent per repository answered questions a to h below. I
  checked a sample of their citations against the clones before using them. A claim
  marked *(not stated)* is an inference the repository does not make.
- **Citations.** Each section names the commit once. Paths are relative to the
  repository root, as `path:lines`.
- **Licences**, checked in each clone's LICENSE at the commit read:

  | Repository | Commit | Licence | Use |
  |---|---|---|---|
  | hugohe3/ppt-master | `15baa7c570f12c78cd9ac6ead897724571e32e87` | MIT | ideas; code only with a D-0xx and NOTICE |
  | meiiie/meiiie_skillls (`motion-pptx-studio/`) | `e4d0b29b3a515ff2544ead69313822a6a8847fff` | none: its README grants no licence | ideas only |
  | atharva9167j/dom-to-pptx | `e1805f5d1314388212eea8d92bb077c511385a39` | MIT | ideas; code only with a D-0xx and NOTICE |
  | op7418/guizang-ppt-skill | `c91369c449d34755d320a8b81d0734000d99d1ab` | AGPL-3.0 | ideas only |
  | presenton/presenton | `3d02d00e5a5cd7b75095140ed59ac032b6ffab0e` | Apache-2.0 | ideas; code only with a D-0xx and NOTICE |
  | icip-cas/PPTAgent | `833cda553b343be0e486a93b0b57cac962cdd566` | MIT | ideas; code only with a D-0xx and NOTICE |
  | alchaincyf/huashu-design | `4fc7bfdbd5ec3fa2d43ce7a6433de60976a5e4b1` | MIT | ideas; code only with a D-0xx and NOTICE |

- **Which repositories.** The first four were required. I picked three more from the
  auditor's list:
  - **presenton**, because it is the one generator here with a large layout library
    stored as data and a route from the user's own PPTX template (causes 2 and 1);
  - **PPTAgent**, because it is about how to evaluate decks, which the spike and
    spec 003's gates need;
  - **huashu-design**, because its three-direction step is the most worked-out answer
    to "every deck looks the same" (cause 2), and it measures how different two
    directions are.
- **Copying.** No code, prompt or text from these repositories is copied here. The
  n-gram check is at the end. One licensing flag: huashu-design takes its list of
  "AI look" tells from Anthropic's frontend-design skill
  (`references/content-guidelines.md:7`, `scripts/design_lint.py:33-35`), so keyline
  must not take that list from it either.

The questions:

- **a. Canvas:** how a slide is composed, how many layouts, the type scale, the grid.
- **b. Editability:** what is native text and shape in the `.pptx`, what is a picture;
  does text re-flow when edited.
- **c. Fonts:** embedding, web fonts, fallbacks.
- **d. Images:** sourcing, credits, treatments.
- **e. Motion:** what kind, and what survives outside PowerPoint.
- **f. Quality control:** what is measured, what is judged, and whether a failure
  blocks delivery.
- **g. Where it runs.**
- **h. What keyline should take.**

## ppt-master (MIT, `15baa7c`)

The model writes each slide as an SVG file; a converter turns the SVG into native
DrawingML. Paths below under `skills/ppt-master/` are shortened to start at that folder
where marked `skill:`.

- **a. Canvas.**
  - One hand-written SVG per slide, on a 1280 × 720 viewBox, in a closed subset of SVG
    (`docs/technical-design.md:13-25`). One px exports as 0.75 pt
    (skill: `references/shared-standards-core.md:167`).
  - No fixed slots by default. A table maps the content's relationship (comparison,
    sequence and so on) to a starting geometry, including asymmetric 3:7 splits and a
    page left 40 to 60 % empty on purpose (skill: `references/executor-base.md:74-84`).
    Each page also gets a rhythm tag: anchor, dense or breathing
    (skill: `references/plan-core.md:72-75`).
  - Optional layout templates: 86 SVG prototypes in 7 workspaces, among them an
    edge-to-edge picture family, `editorial_bleed` (skill: `templates/`).
  - **The type scale is a ratio to a body size,** and the body size follows the reading
    mode: 20, 24 or 32 px, that is 15, 18 or 24 pt (skill: `references/canvas-formats.md:33-37`).
    A cover hero is 2.5 to 5 times the body, a page title 1.5 to 2 times
    (skill: `references/plan-core.md:170-184`). A size outside the declared scale may
    appear at most twice in a deck (skill: `references/executor-base.md:208`).
  - No column grid.
- **b. Editability.**
  - Rectangles and ellipses become preset shapes, paths become custom geometry, groups
    stay groups, gradients become gradient fills, and a full-canvas first rectangle
    becomes the slide background (`docs/powerpoint-svg-mapping.md`, sections 3 and 6).
  - Pictures stay native, with a native crop; recolouring and blur are baked into a new
    image first (same file, section 5).
  - Charts and tables are drawn as plain shapes unless a flag asks for native objects,
    because native charts render differently across apps (`docs/roadmap.md:150-156`).
  - **Text does not re-flow by default.** Each paragraph is a box with wrapping off
    and hard line breaks; a flag turns square wrapping on
    (skill: `scripts/svg_to_pptx/drawingml/elements.py:3715-3741`). Google Slides'
    differences are declared out of scope (`CONTRIBUTING.md:71`).
  - A structured mode writes real masters and layouts with placeholders
    (skill: `references/pptx-structure-interface.md:9-45`).
- **c. Fonts.** Never embedded (`docs/roadmap.md:88`). The plan names fonts that
  Windows PowerPoint has; web and Mac families are remapped at export
  (skill: `scripts/svg_to_pptx/drawingml/utils.py:133-155`). Text widths come from
  bundled advance tables for ten families, Georgia, Trebuchet MS, Verdana, Tahoma and
  Segoe UI among them (skill: `scripts/svg_to_pptx/drawingml/font_advances.json`).
- **d. Images.**
  - Sourcing: the user's files, image search (Openverse and Wikimedia without a key),
    or image generation (skill: `references/image-searcher.md:39-48`).
  - Licence tiers: free to use, credit required (shown on the slide), or unchecked.
    Non-commercial and no-derivatives licences are refused, and the checker looks for
    the credit on the slide (skill: `references/image-searcher.md:11-27`).
  - Treatments: full-bleed pictures under gradient scrims with fixed alpha stops
    (skill: `references/executor-base.md:123`); cut-outs; duotone and blur made with
    Pillow in a fixed order (skill: `scripts/image_treat.py:1-20`).
- **e. Motion.** A 0.4 s fade by default; object animation is opt-in
  (`docs/animations.md:14-20`). Morph pairs are made deterministic by giving matching
  shapes on adjacent slides the same name, with a fade as the fallback
  (skill: `scripts/docs/pptx-transitions.md:137-139`). Only PowerPoint desktop is
  validated (`docs/animations.md:277`).
- **f. Quality control.**
  - Measured: a 10,000-line checker covers the SVG grammar, fonts, images, credits,
    drift from the locked colours and sizes, and bounds. Overlapping content groups fail,
    and so does text past the slide edge (skill: `scripts/docs/svg-contract.md:439-455`).
  - **Blocking:** export refuses unless a passing report matches a fingerprint of the
    current SVGs (skill: `scripts/svg_to_pptx/pptx_package/cli.py:3128-3153`).
  - Judged: an opt-in visual review by subagents with a rubric
    (skill: `references/visual-review.md:15-50`). There is no measured whitespace or
    vertical-balance check.
  - The output is not byte-identical: it stamps the time
    (skill: `scripts/svg_to_pptx/pptx_package/builder.py:6392-6412`).
- **g. Where it runs.** Python 3.10 to 3.14 with python-pptx, skia-pathops, uharfbuzz
  and PyMuPDF (`requirements.txt`); tested mostly in Claude Code (`README.md:206-218`).
  The default flow opens a local preview server
  (skill: `references/confirm-surface.md:7-15`). claude.ai is not mentioned.
- **h. What keyline should take.**
  1. An edge-to-edge, dark, picture-led layout family with fixed scrim stops, and
     rhythm tags per slide (causes 2 and 6).
  2. The difference between composed negative space and leftover blank, as a measured
     rule rather than a judgment (cause 4).
  3. A ratio type scale anchored on the body size per mode, with a cap on one-off
     display sizes (causes 1 and 4).
  4. Pillow image treatments in a fixed order, and a licence-and-credit check (cause 6).
  5. Chart defaults: one hue, the accent on the key value only, direct labels (cause 5).
  - **Not:** model-written SVG coordinates (not deterministic), and text boxes that do
    not wrap (they break the Google Slides and Canva targets).

## motion-pptx-studio (no licence: ideas only, `e4d0b29`)

A photo- and film-led deck skill. The agent writes a JSON deck that a python-pptx script
builds. Its gates refuse delivery. Paths start at `motion-pptx-studio/`.

- **a. Canvas.**
  - Free composition on a 13.333 × 7.5 in slide, from 12 components, placed by
    position or by a span of 12 columns (`references/deck-json.md:47-59`).
  - Each slide declares one of 15 composition kinds. Most are led by a picture or a film
    (bleeds, tight crops, cut-outs, masked shapes); the rest include side-by-side and
    stepped arrangements, a poster, a chart and a diagram
    (`principles/layout-rhythm.md:4-5`). A deck names 5 to 7 compositions of its own
    (`principles/composition-range.md:3`).
  - **The type scale is chosen hero first:** a hero of 200 to 400 pt, steps of about
    1.6 to 2 down to a body of 16 to 20 pt. The largest size is 15 to 25 times the
    smallest, and a deck that tops out near 130 pt reads as a report
    (`principles/one-type-scale.md:2-7`).
- **b. Editability.** Native text boxes with wrapping on (`scripts/build_deck.py:1302-1307`),
  native shapes, native picture crops and native duotone (`scripts/build_deck.py:1216-1252`),
  masks as preset geometry on a picture (`scripts/pptx_fx.py:35-43`). Charts are drawn
  as rectangles and text, not chart objects. Textures and cut-outs are pictures. Films
  are embedded video with a poster frame.
- **c. Fonts.** Each deck picks open-licence families; fonts are embedded at delivery,
  and the script notes that LibreOffice ignores embedded fonts
  (`scripts/embed_fonts.py:1-8`). The fit check uses the real font, warns only, and is
  skipped when the font is missing (`scripts/typeset.py:10-12`).
- **d. Images.**
  - A credited photo library comes before any slide: several candidates per chapter,
    each recorded with its URL, licence, author and job
    (`principles/photo-library-first.md`). Non-commercial and no-derivatives licences
    are skipped.
  - The photo's job decides its arrangement: a place goes full-bleed, an object becomes
    a cut-out at hero scale, a detail gets an extreme crop, a process becomes a strip
    of 3 to 5 frames (`principles/photo-arrangement.md:4-9`).
  - One grade or duotone per chapter, and contrast checked at 4.5:1.
- **e. Motion.** By default Morph is rebuilt from classic effects that other apps keep.
  A second mode keeps Morph for PowerPoint 365 with a classic fallback. The repository
  notes that Google Slides keeps fades and zooms but drops motion paths
  (`scripts/compat.py:1-20`).
- **f. Quality control.**
  - **Measured and blocking.** When a gate fails, the file is renamed `*.UNFINISHED.pptx`
    and the build stops (`scripts/build.py:36-45`). The change came after a failed deck
    was delivered anyway (`CHANGELOG.md:4-7`). Among the gates
    (`scripts/art_check.py`, `scripts/style_check.py`):
    - more than a third of slides with a small headline in the top left corner;
    - near-identical neighbouring slides;
    - too many half-empty slides;
    - a chapter without a hero (very large type, a full bleed or a big cut-out);
    - one layout on more than 3 slides;
    - 4 slides in a row with no strong slide (`scripts/style_check.py:10`);
    - text over a busy part of a photo.
  - Two gates were lowered to warnings because builders learned to game them
    (`CHANGELOG.md`, 6.18).
  - **Judged:** a separate critic session, never the builder, scores the deck against
    yardstick contact sheets that a human scored (`examples/yardsticks/README.md:1-6`).
    The loop is capped at 3 rounds, keeps the better render, and stops when the gain is
    under half a point (`principles/per-slide-critic.md:4-13`).
  - **Three directions** are written and must differ on at least 3 axes. Three sample
    chapters are built, and the pick is recorded as a binding style sheet that the build
    requires (`principles/three-directions.md`, `scripts/build.py:61-68`).
  - **Its own history matches run 1.** Version 6.8.0 diagnosed first-round decks as
    "header templates": a fixed list of sizes topping out near 132 pt and the same title
    band on every slide. The fix was a ratio scale with large heroes and the top-left
    headline gate (`CHANGELOG.md:16-23`).
- **g. Where it runs.** Python with python-pptx, Pillow and numpy, LibreOffice, ffmpeg,
  a Manim fork, and Node with headless Chrome, all required at step 0 (`SKILL.md:8-12`);
  network access for photos; the critic expects the Codex CLI. claude.ai is not
  mentioned.
- **h. What keyline should take** (ideas only):
  1. A measured "header template" rule: the share of slides whose largest text is small
     and in the top left corner, and a hero per section (causes 3 and 4).
  2. Named compositions per slide, with rhythm rules: no composition more than three
     times, a strong slide in every run of four (cause 2).
  3. The photo's job decides its arrangement, with native crops and masks, and a credit
     per image (cause 6).
  4. A failed gate marks the deck unfinished instead of delivering it.
  5. A critic separate from the builder, scored against yardsticks Tyler has scored.
  - **Not:** embedded fonts, which LibreOffice ignores and which does nothing for
    cause 1 in the other apps *(not stated for Google Slides or Canva)*.

## dom-to-pptx (MIT, `e1805f5`)

A library that turns HTML laid out in a browser into an editable `.pptx`, on top of
PptxGenJS (`package.json`; `src/index.js:2`).

- **a. Canvas.** A slide is an HTML element in a live browser. The library reads each
  node's box and computed style and places it at that position (`src/index.js:493-621`),
  so flex and grid work because they are measured. Sizes convert at 0.75 pt per px,
  scaled to the slide (`src/utils.js:572-645`). There is no layout system or grid in
  the code; the bundled skill offers style presets and prompt layouts
  (`packages/dom-to-pptx-skills/skills/dom-to-pptx-skill/reference/STYLE_PRESETS.md`).
- **b. Editability.**
  - Native: text boxes with mixed runs, preset shapes with outlines and one shadow,
    native bullets and tables (`src/index.js:1419-1647`, `src/utils.js:885-912`).
  - Pictures: linear gradients (drawn as SVG), uneven corners, blur, inline SVG,
    `<canvas>` charts, and anything else it cannot map (`src/index.js:627-837`,
    `src/utils.js:786-848`).
  - **Image crops are baked into the bitmap,** not written as a native crop
    (`src/image-processor.js:3-110`).
  - Text keeps the browser's box but PowerPoint re-wraps it with its own metrics, and a
    comment in the code says so (`src/index.js:1279-1281`). It re-flows when edited.
- **c. Fonts.** It fetches the web fonts the page uses, converts them and embeds them
  (`src/index.js:236-389`). Only the first family of a CSS stack is written
  (`src/utils.js:627`); a failed fetch is logged and PowerPoint falls back to Arial
  (`Readme.md:500-504`).
- **d. Images.** `<img>` and CSS backgrounds are redrawn at twice their size with the
  crop applied; masks are limited to rounded rectangles and circles.
- **e. Motion.** CSS classes map to 10 entrance and 10 exit presets
  (`src/animations/css-parser.js:7-43`), and about 60 transitions, the newer ones with a
  fade fallback (`src/animations/transitions.js`). Nothing says what survives in Google
  Slides or Canva.
- **f. Quality control.** None in the library: failed images are dropped and nothing
  blocks (`src/index.js:590`). The skill's validator is opt-in and does not catch text
  overflow, by its own account
  (`packages/dom-to-pptx-skills/skills/dom-to-pptx-skill/reference/VALIDATION.md:266-271`).
  **Not deterministic:** the output depends on the browser, installed fonts, the network
  and random clip IDs (`src/utils.js:297`).
- **g. Where it runs.** A browser page, or Node with Puppeteer and headless Chrome; it
  downloads Chrome when none is found (`src/node-exporter.js:128`). Not in the claude.ai
  sandbox.
- **h. What keyline should take.**
  1. A catalogue of compositions and a rule against the same one on consecutive slides
     (cause 2).
  2. Full-bleed picture, dark scrim, title on top. Use its cover-crop arithmetic
     (`src/image-processor.js:57-101`), but write the crop natively (cause 6).
  3. Dark surfaces as palette roles, written as the slide background (cause 2).
  4. Text anchored at 35 to 50 % of the height on statement slides (cause 4).
  5. A small tracked label above the title instead of a rule under it (cause 3).
  - **Not:** baked crops, gradients as pictures, charts as pictures, embedded fonts.

## guizang-ppt-skill (AGPL-3.0: ideas only, `c91369c`)

A "Swiss" deck skill like keyline's own, but its output is a single HTML page, not a
`.pptx`; PPTX export is outside its main path (`README.en.md:386-387`).

- **a. Canvas.**
  - Every slide declares one of 22 locked layouts (`references/swiss-layout-lock.md:9-44`):
    covers and closers, timelines, card grids, data layouts, statements with a full-width
    ink band, comparisons, diagrams and an image hero. The content's shape chooses the
    layout, and data layouts are refused without real numbers
    (`references/layouts-swiss.md:237-246`).
  - **Variety is a rule:** at least 6 different layouts in a deck of 7 or 8 slides, at
    least 8 in 10 or more, and never the same structure three slides in a row
    (`SKILL.md:354-359`).
  - Sizes are fractions of the slide width. A title is at least 8 times the body, and
    weight falls as size grows (`SKILL.md:425-438`, `SKILL.md:506`).
  - 12 columns and an 8 px spacing scale (`assets/template-swiss.html:389-404`, `:43-56`).
- **b. Editability.** HTML only; no `.pptx` or PDF route.
- **c. Fonts.** Web fonts from a CDN, not embedded, with system fallbacks
  (`assets/template-swiss.html:7-9`, `:39-41`). Its light Swiss look depends on a
  weight-200 web font.
- **d. Images.** 3 of the 22 layouts take pictures. The image hero is a 21:9 photo
  across the top 60 %, cropped with the subject about 35 % from the top
  (`references/swiss-layout-lock.md:57-66`). A group of pictures shares one ratio, and
  text goes on a picture only where it is quiet enough (`SKILL.md:388-398`). No credits
  are kept.
- **e. Motion.** One entrance animation per slide, in the browser only.
- **f. Quality control** (`scripts/validate-swiss-deck.mjs`):
  - Static checks fail the run: a missing layout ID, text inside SVG, an image without
    its slot ID (lines 58-125).
  - Rendered checks need Playwright and are skipped without it (lines 127-296). They
    measure the union of the content boxes: overflow fails; a large bottom gap together
    with low occupied height, and a cramped gap under the title, warn.
  - Whitespace problems only warn, and the rendered checks depend on web fonts and
    timeouts, so they are not reproducible.
- **g. Where it runs.** Claude Code or Codex with a shell; the page needs the network for
  fonts and icons; the validator needs Node, and Chromium for the measurements.
- **Palettes.** Four presets that share warm neutrals and differ only in one accent;
  custom colours are refused, and one accent is allowed per deck
  (`references/themes-swiss.md:117-145`).
- **h. What keyline should take** (ideas only):
  1. Colour-block compositions as layouts (accent cover, half-accent closer, ink band)
     and the variety rule (cause 2).
  2. Measured vertical balance: the content box, the bottom gap and the occupied height,
     with the fix in order: tighten, step the size down, cut, change layout (cause 4).
     keyline should set its own thresholds on its own fixtures.
  3. Rules only at structural boundaries; hierarchy from a small label over a large
     title and a large gap (cause 3).
  4. Picture slots with fixed ratios and a quiet-zone test before text goes on a
     picture (cause 6).
  5. Data layouts only for real numbers; bars in one accent with the value at the end
     (cause 5).
  - Cause 1 does not transfer: its look rests on web fonts.

## presenton (Apache-2.0, `3d02d00`)

An open-source deck generator with a web editor, PPTX export and user templates.

- **a. Canvas.** Two modes (`docs/presentation-generation-modes.md`): templates of
  absolutely placed JSON elements on a 1280 × 720 canvas
  (`servers/fastapi/templates/v2/models/elements.py:203-420`), or free HTML per slide.
  Each editable element carries limits, a minimum and a maximum length, item counts and
  table sizes, and the content schema is compiled from them
  (`servers/fastapi/templates/v2/schema.py:361-449`). 16 templates hold 383 layouts in
  total (`templates/*/template.json`). There is no global type scale or grid.
- **b. Editability.** The PPTX writer is not in the repository: a Node package renders the
  slides in headless Chromium and converts the measured boxes
  (`Dockerfile:76-110`, `servers/nextjs/app/(export)/pdf-maker/PdfMakerPage.tsx:46-50`).
  What ends up native could not be checked here.
- **c. Fonts.** 95 open-licence families bundled as files
  (`servers/fastapi/assets/fonts.json`). An uploaded template's fonts are listed,
  embedded ones extracted, and missing ones requested from the user
  (`servers/fastapi/templates/pptx_font_utils.py:271-310`).
- **d. Images.** Stock search or image generation; the photographer's credit is dropped
  (`servers/fastapi/services/image_generation_service.py:478-511`). Crop to fill with a
  focus point (`servers/fastapi/templates/v2/models/elements.py:240-262`). A large icon
  set, picked by a local embedding search.
- **e. Motion.** None.
- **f. Quality control.**
  - Content is generated against each layout's limits, but after 4 rounds an invalid
    answer is kept with a warning (`servers/fastapi/utils/llm_utils.py:327-376`).
  - A box's text capacity is estimated at 0.58 em per character with a 0.85 safety
    factor, not from font metrics
    (`servers/fastapi/templates/v2/certified_generation.py:62`, `:2470`).
  - Contrast is measured and repaired: a text role below 4.5:1 becomes black or white
    (`servers/fastapi/templates/v2/theme.py:423-430`).
  - In free-HTML mode, a slide with overflow, overlapping boxes or too many words is
    refused and retried up to 8 times (`servers/fastapi/utils/smart_slide_layout.py:230-289`).
- **g. Where it runs.** A Docker image or a desktop app, with an LLM, Chromium and the
  network. Not the claude.ai sandbox.
- **h. What keyline should take.**
  1. Layouts as data in the pack, dark and picture-led variants among them (cause 2).
  2. From the user's own `.pptx`: its layouts and placeholders as slots, palette roles
     from area-weighted colour, unknown fonts mapped to twins with a warning. This is
     the deterministic part of presenton's template route, without its model passes
     (causes 1 and 2).
  3. Each slot with a minimum as well as a maximum length, measured by keyline's own
     estimator, so a slide is not left half empty (cause 4).
  4. Chart colours from palette roles, and switches for labels, legend and gridlines
     (cause 5).
  5. Picture slots with crop to fill around a focus point, keeping the credit that
     presenton drops (cause 6).

## PPTAgent (MIT, `833cda5`)

The repository holds the PPTAgent skill. The papers' agent and evaluation code live in
tagged releases, not in this tree (`README.md:20-21`). Paths start at `skills/pptagent/`.

- **a. Canvas.** The host model writes one static HTML file per slide, and a converter
  makes the PPTX (`SKILL.md:29-38`). The starting template has a single title size and a
  flat background (`assets/slide-template.html:6-41`). No layout library.
- **b. Editability.** Text inside paragraph and heading elements becomes native text
  (`references/task-contract.md:28-33`, `tests/test_browser.py:63-91`). Positions are
  fixed from the browser, and the contract asks for slack in text boxes because metrics
  change on export (`references/task-contract.md:35-38`).
- **c. Fonts.** Local font files only; remote font imports are blocked
  (`references/task-contract.md:22-24`).
- **d. Images.** Local files only; optional search and extraction tools.
- **e. Motion.** None.
- **f. Quality control.**
  - **Two renders:** each slide's HTML in Chromium, then the finished PPTX through
    LibreOffice into contact sheets (`scripts/pptagent_runtime/core.py:148-208`, `:345-430`).
    The second render checks the file actually delivered.
  - **Judged:** the host model, or an external vision model at temperature 0, returns a
    verdict per slide and per deck. A "pass" that lists a major problem is refused, and
    a malformed answer counts as a failure (`scripts/pptagent_runtime/visual.py:15-98`).
  - **Bound to the evidence:** each review carries the SHA-256 of the slide, its assets
    and its render; any change makes it stale, and the build refuses while a review is
    missing, stale or failing (`scripts/pptagent_runtime/core.py:93-145`, `:301-304`).
  - The papers' evaluation has three axes: content, design and coherence
    (`README.md:388`).
- **g. Where it runs.** Python, Node, Playwright Chromium and LibreOffice; an API key
  for the external judge.
- **h. What keyline should take.**
  1. A `check` report bound by hash to the deck, the lint output, the renders and the
     rule set, so that a stale pass is impossible.
  2. Measure the delivered file in a second renderer, at a pinned version, with
     tolerances (cause 1: font substitution shows there).
  3. For the slide bench: the three axes, but with design and coherence computed where
     possible (one measure per cause), and any model score kept in a separate,
     advisory column with its model, temperature and prompt hash.
  4. A strict schema for the skill's visual self-review.
  5. Compositions chosen per slide function (cause 2).

## huashu-design (MIT, `4fc7bfd`)

A design skill that writes HTML first and exports to PDF, and to PPTX on request.

- **a. Canvas.**
  - One 1920 × 1080 HTML file per slide (`references/modules/deck.md:15-21`). About seven
    slide types, of which a deck uses four or five (`references/slide-decks.md:527-537`).
  - **Rhythm is planned:** mostly light slides, an occasional colour divider, an
    occasional dark run; the main visual changes kind from slide to slide
    (`references/slide-decks.md:146-162`, `:546-554`). For a longer deck, the two most
    different slides are built first (`references/slide-decks.md:89-109`).
  - **Type is a ratio** (1.5 for slides), at most five steps, with the display size
    outside the scale (`references/typography.md:18-51`).
- **b. Editability.** Two export routes. One keeps text native but refuses gradients
  (`references/editable-pptx.md:51-112`). The other turns SVG and canvas, charts
  included, into screenshots on purpose, and compares the exported text with the page
  to catch lost words (`references/pptx-from-rendered-html.md:178-187`).
- **c. Fonts.** Open-licence web fonts chosen by content type, language and temperature
  before a name is picked (`references/typography.md:7-16`). Not embedded; the docs say
  to check every slide by eye for fallbacks (`references/slide-decks.md:658-680`).
- **d. Images.** Every direction names its hero material. Images the content needs are
  fetched first, from Wikimedia Commons with licence data
  (`references/materials.md`). The test for a decorative image: delete it, and if
  nothing is lost, it was decoration.
- **e. Motion.** Video is a separate module; motion and an editable PPTX are called a
  real trade-off for the user to choose (`references/slide-decks.md:75`).
- **f. Quality control.**
  - **Three directions before building,** required for new visual work
    (`SKILL.md:102-116`). Six candidates come from three sources: an imagined designer,
    a real reference work turned into concrete rules, and a style drawn at random. The
    model picks three that differ in skeleton, temperature and look; each is built as two
    representative slides; the user chooses, and the choice is recorded word for word
    (`references/directions.md:51-126`).
  - **Measured difference:** two directions are flagged as too alike when their palettes
    are close in OKLab, or their layouts correlate on a coarse edge map
    (`scripts/design_lint.py:229`, `:397`). Beauty is left to the user.
  - The lesson it records: a version built on bans made dull output, so it now offers
    options instead (`references/directions.md:7-15`).
- **g. Where it runs.** Python with Playwright and Chromium, Node, and the network
  (`SECURITY.md:7-18`). The lint skips without Playwright.
- **h. What keyline should take.**
  1. Slide roles that pick layouts, and planned colour rhythm with dividers and dark
     runs, written as native backgrounds (cause 2).
  2. A cheap diversity gate: three voices, two slides each, scored for difference in
     OKLab and edge maps on `keyline render` PNGs; the user picks, recorded verbatim
     (causes 1 and 2).
  3. Decoration must carry information; a repeated title rule is the deck version of the
     tics it removes (cause 3).
  4. Hero material, credited, with a placeholder when there is none (cause 6).
  5. A ratio scale with the display size outside it, and content anchored by role
     (cause 4).

## Comparison (a to g)

| | a. Canvas | b. Editable in the `.pptx` | c. Fonts | d. Images | e. Motion | f. Quality control | g. Runs |
|---|---|---|---|---|---|---|---|
| **keyline today** | pack regions, token type scale, python-pptx | all native; text re-flows | Office-core families with metric twins; not embedded | `image` verb, nothing sourced | none | measured lint and fit; `check` gate | lint in the claude.ai sandbox; pen where python-pptx installs |
| **ppt-master** | model-written SVG; 86 optional prototypes; ratio scale | native shapes, gradients, crops; text does not wrap by default; charts drawn | not embedded; Windows families; measured widths for 10 | search, generation; licence tiers; scrims, duotone | fade; deterministic Morph pairs | 10k-line checker; export blocked by fingerprint | Python; Claude Code |
| **motion-pptx-studio** | free composition, 15 kinds; hero-first ratio | native text and crops; charts drawn; films as video | open fonts, embedded | credited library first; arrangement by job | classic effects by default; Morph opt-in | measured gates block (`UNFINISHED`); separate critic with yardsticks | Python, LibreOffice, ffmpeg, Node, Chrome, network |
| **dom-to-pptx** | browser layout, measured | native text and shapes; gradients, charts and crops as pictures | web fonts fetched and embedded | baked crops | 20 presets, about 60 transitions | none in the library; not deterministic | browser or Node with Chrome |
| **guizang-ppt-skill** | 22 locked layouts; width-relative sizes | no PPTX | web fonts | 3 picture layouts, fixed ratios | browser only | static checks fail; rendered checks warn | Node, Chromium, network |
| **presenton** | 383 JSON layouts in 16 templates | via a closed export package (not checked) | 95 bundled families | stock or generated; no credits | none | limits per element, soft; contrast repaired | Docker, LLM, Chromium |
| **PPTAgent** | HTML per slide | native text; fixed positions | local files only | local files | none | judged reviews bound by hash; build refuses | Python, Node, Chromium, LibreOffice |
| **huashu-design** | HTML, ratio scale, planned rhythm | two routes; charts as screenshots in one | web fonts, not embedded | Wikimedia with licence data | separate video module | three directions with measured difference | Python, Playwright, Node, network |

None of them states what survives in Google Slides or Canva in a way the spike could
rely on. ppt-master declares Google Slides out of scope. motion-pptx-studio names a few
effects Google Slides drops. Canva is not mentioned anywhere.

## The ten best ideas, mapped to the six causes

| # | Idea | Cause | From | Fits keyline because |
|---|---|---|---|---|
| 1 | **Named compositions per slide, with rhythm rules:** a composition at most three times, a strong slide in every run of four, never three of a kind in a row | 2 | motion-pptx-studio, guizang, dom-to-pptx, ppt-master | the pen writes the composition; lint counts it in the XML |
| 2 | **Dark and colour surfaces as native slide backgrounds:** accent cover, ink band, dark section dividers | 2 | guizang, dom-to-pptx, presenton, huashu-design | a background fill is native in all four apps *(to be confirmed in the spike)* |
| 3 | **A hero-first ratio type scale:** the body size by mode, a hero far above it, few one-off sizes | 1, 4 | motion-pptx-studio, ppt-master, huashu-design, guizang | tokens in the pack; the fit estimator measures any size |
| 4 | **A measured "header template" rule:** the share of slides whose largest text is small and top left; a hero per section | 3, 4 | motion-pptx-studio | pure geometry on the XML |
| 5 | **Decoration must do a job:** no default rule under the title; a small label above it, or nothing | 3 | huashu-design, guizang, dom-to-pptx, ppt-master | a pack change, and a lint rule for a repeated title rule |
| 6 | **Measured vertical balance:** the content box, the bottom gap and occupancy; a minimum as well as a maximum length per slot; anchors by role | 4 | guizang, presenton, ppt-master, dom-to-pptx | EMU geometry and the fit estimator; thresholds set on keyline's own fixtures |
| 7 | **Picture slots:** full-bleed with a scrim at fixed stops, native crop to a focus point, cut-outs, one ratio per group, a quiet zone before text goes on a picture | 6 | ppt-master, motion-pptx-studio, guizang, dom-to-pptx | native picture crops; Pillow computes the crop and the quiet zone |
| 8 | **Image provenance as a gate:** licence tiers, refuse non-commercial and no-derivatives, a credit on the slide or in the notes | 6 | ppt-master, motion-pptx-studio, huashu-design | a check on recorded metadata; sourcing stays in the skill, not the core |
| 9 | **Chart discipline on native charts:** palette-role colours, one accent on the key value, direct labels, no gridlines or legend, the relationship chosen first | 5 | ppt-master, guizang, presenton, huashu-design | python-pptx writes native charts; lint reads the chart XML; the data stays editable |
| 10 | **A wider measured font set,** checked across the four apps | 1 | ppt-master (measured widths for ten families) | twins and widths are data; the spike finds which families each app has |

Also worth taking, as process rather than a cause:

- **Three directions with a measured difference,** the user's pick recorded verbatim
  (huashu-design, motion-pptx-studio).
- **A yardstick deck scored by Tyler,** and a critic separate from the builder
  (motion-pptx-studio).
- **A `check` report bound by hash to what it checked** (PPTAgent, ppt-master).
- **A failed gate marks the deck unfinished** (motion-pptx-studio).

**Cause 1 is the one no repository solves** across PowerPoint for the web, Google Slides
and Canva. Each one either embeds fonts (ignored by LibreOffice, by motion-pptx-studio's
own note), relies on web fonts (no `.pptx`), or accepts substitution (ppt-master). Spec
003 has to decide it, and the spike should measure which families each app actually
has.

## Spike plan: three routes on the BonsaiHub pitch

**Goal:** choose spec 003's route with evidence. Running any of these tools is the
spike's work, and Tyler decides whether it goes ahead.

- **The same input for every route:**
  - `examples/bonsaihub/pitch.brief.toml`, the brief Tyler approved in run 2: the same
    eleven headlines, the same numbers, the same notes;
  - one small set of credited pictures (Openverse or Wikimedia, licences recorded),
    chosen once and used by every route.
- **The three routes:**
  - **A. Swiss:** run 2's `examples/bonsaihub/pitch.pptx`, unchanged. This is the
    baseline.
  - **B. SVG to DrawingML:** a fresh session writes one SVG per slide from the brief;
    ppt-master's converter builds the PPTX with text wrapping on and native charts.
    MIT; no code enters keyline.
  - **C. HTML to DOM to PPTX:** a fresh session writes one HTML slide per headline;
    dom-to-pptx's command-line tool builds the PPTX. MIT; no code enters keyline.
  - Routes B and C run in their own scratch folder, with their own Node or Python
    environment, outside the keyline checkout.
- **Measured on each `.pptx`** by one script, written for the spike, that reads the XML:
  1. the share of visible words in native text, against words in pictures;
  2. whether a chart is a native chart with editable data;
  3. the fonts named, and which of them each app substitutes;
  4. the picture area share, and the number of full-bleed slides;
  5. the composition signatures: how many distinct ones, and the longest run of one;
  6. the number of rules under titles, and the share of small top-left headlines;
  7. where the content's centre sits vertically, and the share of empty lower halves;
  8. two builds of the same input compared byte for byte;
  9. `keyline check` on the deck: its exit code and rule IDs.
- **Opened in each app:** PowerPoint for the web, Google Slides (import) and Canva
  (import).
  - One screenshot per slide in each app.
  - Per slide, one of: as built; degraded (font substituted, gradient lost, crop lost,
    text moved); or broken.
  - Then the edit test: change one headline and see whether it re-wraps inside its box.
- **The yardstick.**
  - Tyler picks one reference deck he rates 10 out of 10, as motion-pptx-studio's
    yardstick does.
  - He scores each route's contact sheet against it, 1 to 10, with the route's name
    hidden.
  - Separately, he judges correctness and tailoring, as G-2 does.
- **Decision rule.** A route qualifies only if:
  - its text is native and re-wraps in all three apps;
  - keyline's gates can measure it;
  - it runs where the skill runs, or the subset it needs is stated;
  - Tyler scores it above route A.

  Among the routes that qualify, the cheapest to make deterministic wins. If none
  qualifies, spec 003 keeps the pen and takes the ten ideas into it.
- **The record:** `specs/003-*/spike.md` gets each deck's SHA-256, the measurement
  table, the screenshots' hashes, Tyler's scores, and the tools' versions and commits.

## The n-gram check

`tools/ngram_overlap.py`, with this study in a folder of its own, against each clone
(8-word sequences):

| Repository | Shared sequences | What they are |
|---|---|---|
| ppt-master | 1 | the path `scripts/svg_to_pptx/pptx_package/cli.py`, cited above |
| motion-pptx-studio (whole clone) | 0 | |
| dom-to-pptx | 3 | the path `packages/dom-to-pptx-skills/skills/dom-to-pptx-skill/`, cited above |
| guizang-ppt-skill | 0 | |
| presenton | 0 | |
| PPTAgent | 0 | |
| huashu-design | 0 | |

The first run also found one sequence shared with motion-pptx-studio: a list of its
composition names in its own order. That sentence was reworded, and the run above is
the one after it.
