# Codifying slide aesthetics: impeccable for .pptx

*Research notes, September 2026. Compiled with Claude (Anthropic) from six parallel research threads; sandbox results were produced in the same session on OfficeCLI v1.0.152 and have not been reproduced elsewhere.*

The "impeccable for slides" niche is still open, but only at one narrow point. Nobody has yet combined four things: a set of anti-slop rules that are **deterministic, carry rule IDs, and run on any .pptx file**; an impeccable-style command vocabulary; Claude Code hooks; and OfficeCLI as the engine. As for the anti-slop layer written in prose, every major slide skill already has one. So the core value of the project lies in **deck-lint**, not in SKILL.md. The sandbox demonstrated this: `officecli view issues` reported 0 issues on a deck with an empty band covering 37–42% of the slide height, while a 9-rule prototype reading from `officecli dump` caught 6 real errors. A deterministic linter is also the best foundation for a future benchmark, because existing benchmarks score design with a VLM judge, and this kind of judge is systematically biased. For example, PPTEval reached only Spearman ρ = 0.303 when re-checked independently. However, the name "Slide Bench" already has three owners, and "deck-lint" also collides with another repo's name. Technically, .pptx displays embedded fonts reliably only on PowerPoint desktop. OfficeCLI cannot embed fonts, and its renderer falls back to `sans-serif`, so the toolchain has to patch three things itself: font embedding, render QA with `@font-face`, and handling the quirks of `dump`. On taste, the most important warning concerns the "editorial" look: off-white/cream background, rust-red accent, letter-spaced uppercase labels, italic serif. This very look rescued the rebuild in the sandbox, but the press and Anthropic's own documentation now call it the "Claude look". Worse, Anthropic's pptx skill and OfficeCLI's KPI recipe prescribe many tells. The proposed architecture follows this order: deck-lint (borrowing impeccable's registry and JSON contract) → render/font pipeline → hooks → skill router with DESIGN.md, ANTI-TELLS.md and style packs. The benchmark comes last, once the rules have been calibrated on a human-labeled corpus.

*Label conventions: **[VERIFIED]** = read at the original source (URL attached) or run in the sandbox; **[VERIFIED-S]** = read through a WebFetch summary, wording may not be verbatim; **[INFERRED]** = inferred from the cited source; **[GUESS]** = unverified judgment, used only as a hypothesis to test. All sandbox results were run by Claude in this research session, on OfficeCLI v1.0.152 installed via npm; nobody has rerun them on another machine.*

## The niche is open at only one point: an anti-slop linter that runs on any .pptx file

The slide skill market is much more crowded than it first appears. The awesome-html-slide-skills list counted "20+ serious skill packages in two months" in early 2026 alone **[VERIFIED]** ([awesome-html-slide-skills](https://raw.githubusercontent.com/ToseaAI/awesome-html-slide-skills/main/README.md)). The ecosystem splits into three camps:

- **HTML-first**, with the most stars: frontend-slides at about **28.6k stars**, exporting only PDF, and huashu-design at about **24.2k**.
- **Native PPTX**: Anthropic's `pptx` skill, OpenAI's `slides` skill, **OfficeCLI 24k stars** and **ppt-master 52.3k stars**.
- **Slide generation with an image model**: text is baked into pixels, so it is almost impossible to edit.

Figures from [frontend-slides](https://github.com/zarazhangrui/frontend-slides), [OfficeCLI](https://github.com/iOfficeAI/OfficeCLI), [ppt-master](https://github.com/hugohe3/ppt-master) and [awesome-ai-ppt](https://raw.githubusercontent.com/ningzimu/awesome-ai-ppt/main/README.md) **[VERIFIED]**.

Almost every major skill already has a list of "AI tells" written in prose **[VERIFIED]**:

- Anthropic's pptx skill says: "**NEVER use accent lines under titles — these are a hallmark of AI-generated slides**" ([Anthropic pptx SKILL.md](https://raw.githubusercontent.com/anthropics/skills/main/skills/pptx/SKILL.md)).
- The `officecli-pptx` skill lists three "Visual AI-tells to avoid": underlined titles, rounded cards with a colored left border, emoji as icons ([officecli-pptx SKILL.md](https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/skills/officecli-pptx/SKILL.md)).
- slide-craft has a "Never do these" section.

A comparison of 8 PPT skills (August 2026) concluded that current best practice consists only of "render/overflow/overlap/font checks", and found no design linting or anti-slop terminology **[VERIFIED]** ([2Slides](https://2slides.com/blog/best-ppt-skills-claude-code-codex-2026)). In other words, **everyone now has a prose anti-slop layer**, and writing a better SKILL.md does not create a durable advantage **[INFERRED]**.

The projects closest to this idea each lack exactly one piece. The table below summarizes:

| Project | Has | Missing relative to "impeccable for slides" |
|---|---|---|
| impeccable (Apache-2.0, 70.7k stars) | 24 commands, 61 deterministic detector rules, hooks, PRODUCT.md/DESIGN.md | The README never mentions slides, decks or presentations **[VERIFIED]** ([impeccable](https://github.com/pbakaus/impeccable)) |
| SlideSpeak/slide-design-skill (MIT, 6 stars) | "Design rules here are enforced by code, not by prompt wording alone": gates for card-edge accent line, em-dash, occupancy "large empty bands" | Output is 1920×1080 HTML, not .pptx **[VERIFIED]** ([README](https://raw.githubusercontent.com/SlideSpeak/slide-design-skill/main/README.md)) |
| power-design (MIT, 581 stars, 3 commits) | 20 slide rules with numeric thresholds: whitespace ≥ 40%, body ≥ 24px, contrast ≥ 4.5:1, 60-30-10… | No checking script; output is HTML **[VERIFIED]** ([README](https://raw.githubusercontent.com/ItsssssJack/power-design/main/README.md)) |
| EveryInc/hands-on-deck (MIT, ~210 stars) | Deterministic PPTX linter after every patch: overflow, off-slide, text-on-text, near-miss alignment against an implicit grid | Describes itself with "It catches the near-miss, not the design"; no aesthetic rules **[VERIFIED]** ([README](https://raw.githubusercontent.com/EveryInc/hands-on-deck/main/README.md)) |
| pptx-qc (19 rules) · pptlint (14 rules) · SlideGauge (Marp, 11 rules) | Stable rule IDs, config, JSON/SARIF, severity gate | Checks correctness only: placeholders, fonts, dpi, overflow; no AI tells **[VERIFIED]** ([pptx-qc](https://raw.githubusercontent.com/BDBDDSCAT/pptx-qc/master/README.md), [pptlint](https://raw.githubusercontent.com/heroak2008/ppt-linter/main/README.md), [SlideGauge](https://raw.githubusercontent.com/nibzard/slidegauge/main/README.md)) |
| OfficeCLI `view issues` | `shape_off_slide`, text-fit, `low_contrast` | `low_contrast` only catches dark text on a dark background *of the same shape*; the skill admits it "can't see" text that sits on a separate background shape **[VERIFIED]** ([officecli-pptx SKILL.md](https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/skills/officecli-pptx/SKILL.md)) |

This gap is real, not just theoretical. In the sandbox, `view issues` reported **0 issues** on a deck whose bottom band was empty for 37–42% of the height. A 9-rule deck-lint prototype (Python, reading JSON from `officecli dump`) caught **6 real errors** after an indexing bug was fixed **[VERIFIED – sandbox]**. The 9 rules are `body-too-small`, `title-not-dominant`, `edge-margin`, `dead-band`, `overlap`, `title-underline`, `dark-on-dark`, `notes-missing` and `font-count`. The prototype also used exit codes 0/2/1 like `impeccable detect` **[VERIFIED – sandbox `deck_lint.py`]**.

Searches for "impeccable skill slides", "anti-slop slides", "deck-lint" and "pptx linter" returned no project that describes itself as a port of impeccable to slides **[INFERRED from empty search results, so no URL]**. From this, the four pieces that are truly missing are **[INFERRED]**:

1. A **catalog of deterministic anti-slop rules at the format level**, versioned and with IDs, that runs on *any* deck, not just the output of one skill.
2. An **impeccable-style command vocabulary** for decks: critique, polish, distill, bolder, quieter, typeset, layout.
3. **Automatic linting via Claude Code hooks** for PPTX. The closest is hands-on-deck's "lint after every apply", but that mechanism lives inside its own CLI.
4. A **design-language layer on top of OfficeCLI**: no third party has been seen doing this.

The content of individual rules can mostly be harvested from the projects above. What is new is the packaging. Strategic consequence: deck-lint should be positioned as a **checker for every PPTX generation source** (OfficeCLI, pptxgenjs, html2pptx, ppt-master), not only for this project's skill. Doing so widens the user base beyond the skill **[INFERRED]**.

There are three threats to plan for:

- **A first-party competitor.** Claude Slides entered beta on **2026-09-16** and can export PowerPoint and PDF. Reviews note "no confirmed template library or brand styling persistence" **[VERIFIED]** ([Serverman](https://www.serverman.co.uk/ai/claude/claude-docs-and-slides-what-they-can-and-cant-do/); [Remio](https://www.remio.ai/post/claude-slides-launch-brings-editable-decks-into-every-conversation)).
- **Commercial tools win by narrowing the layout space**, not by prompting. Beautiful.ai treats design rules as "non-negotiable". Gamma is "optimized around structured blocks … rather than unrestricted placement" **[VERIFIED]** ([Beautiful.ai](https://www.beautiful.ai/blog/ai-can-build-slides-fast--but-great-presentations-still-need-design-rules); [Moda review](https://moda.app/blog/gamma-ai-presentation)). A project that places shapes freely with OfficeCLI without a constraint layer (grid, type scale, layout archetypes, lint gate) will lose on consistency **[INFERRED]**.
- **HN users state clearly the differentiator they need**: working with corporate PowerPoint templates, because "none of the AI slide makers I've seen have any competency in doing that" **[VERIFIED]** ([HN](https://news.ycombinator.com/item?id=46998194)). So the project must treat an existing .potx file as the "incumbent visual authority" and must not impose its own taste over it.

Two further practical notes. First, Anthropic's document skills, including pptx, are **"source-available, not open source"**. Learn from the ideas only; do not copy the wording. By contrast, impeccable and OfficeCLI use Apache-2.0; hands-on-deck, SlideSpeak and power-design use MIT **[VERIFIED]** ([anthropics/skills](https://github.com/anthropics/skills)). Second, others fork very quickly, so once the idea is public, the speed and quality of the rule catalog matter more than the concept itself **[GUESS]**.

## Existing benchmarks score design with a VLM judge, and the name "Slide Bench" is taken

Slide benchmarks have gone through three phases:

1. **Task completion**: PPTC, 2023–24.
2. **Full deck generation**: SlidesGen-Bench, PresentBench, DECKBench, in 2026.
3. **Editing**: PPTArena, TSBench, PPT-Eval.

Scoring of *design* almost always uses a VLM judge that looks at rendered images. The two partial exceptions are SlidesGen-Bench (computational aesthetics on pixels) and PPTBench (tests whether the *model* can detect errors) **[VERIFIED]**. The table below collects the most relevant benchmarks:

| Benchmark | Scope | How design is scored | Agreement with humans |
|---|---|---|---|
| AutoPresent / **SlidesBench** (CVPR 2025, MIT) | 7k train / 585 test, **individual slides**, from 310 decks | Reference-based: element match, CIEDE2000, position. Reference-free: VLM scores 0–5 for Text/Image/Layout/Color | ICC 73.8–85.3% **[VERIFIED]** ([arXiv](https://arxiv.org/html/2501.00912v1)) |
| PPTEval (PPTAgent, EMNLP 2025) | Content/Design/Coherence, 1–5 scale | GPT-4o looks at rendered slides | Self-reported: design ρ = 0.88. Independent re-check: **ρ = 0.303** **[VERIFIED]** ([PPTAgent](https://arxiv.org/html/2501.03936v3); [PresentBench](https://arxiv.org/html/2603.07244v1)) |
| PresentBench (3/2026, Apache-2.0) | 238 instances, on average ~54.1 binary checklist items, of which 17.0 concern Visual Design | `gemini-3-flash-preview` | ρ = 0.532 against a human–human ceiling of 0.664. "Visual Design and Layout is a primary bottleneck"; the best system (NotebookLM) reaches only 62.8 on this dimension **[VERIFIED]** ([arXiv](https://arxiv.org/html/2603.07244v1)) |
| SlidesGen-Bench (1/2026, MIT) | Content (QuizBank), Aesthetics, Editability | 5 deterministic metrics: WCAG contrast, color harmony, colorfulness, subband entropy, "Visual HRV" | 0.71, versus 0.57 for the LLM judge. Two versions describe the metrics inconsistently **[VERIFIED]** ([GitHub](https://github.com/YunqiaoYang/SlidesGen-Bench); [Lacuna](https://lacuna.tiptreesystems.com/work/slidesgen-bench-evaluating-slides-generation-via-computational-and-quantitative/wrk_90ee3a8643a27771eb4d8c52917916ce)) |
| PPTArena (ECCV 2026, CC BY 4.0) | 100 decks, 1,300+ edits | Two VLM judges score 0–5; the Instruction-Following judge reads the XML diff | **[VERIFIED]** ([arXiv](https://arxiv.org/html/2512.03042v3)) |
| PPTBench (12/2025) | 4,439 samples from 958 PPT files | Tests whether the model *detects* overlap, out-of-bounds, misalignment | Detection 76–95%; modification/generation 30–87% **[VERIFIED]** ([arXiv](https://arxiv.org/html/2512.02624v1)) |
| SlideAudit (UIST 2025, CC BY 4.0) | 2,400 slides, 27 error types in 5 groups | LLM detects errors | Human–human agreement is only **κ = 0.26**; best LLM F1 = 0.655 **[VERIFIED]** ([arXiv](https://arxiv.org/html/2508.03630v1)) |
| DECKBench (KDD 2026) | 294 paper–slide pairs, 5 rounds of iterative editing | Reference-based metrics and LLM judge | **No** human agreement study **[VERIFIED]** ([arXiv](https://arxiv.org/html/2602.13318)) |
| Design Arena – Slides | Human pairwise votes | Bradley-Terry, at least 15 comparisons before appearing on the board | **[VERIFIED]** ([methodology](https://notes.designarena.ai/methodology/)) |

The evidence on VLM judge reliability is fairly clear. The study "VLM Judges Can Rank but Cannot Score" found that every judge **over-scores poor outputs by +1.73 to +1.98 points**, under-scores excellent outputs by −0.74 to −1.04, and that the prediction interval for aesthetics covers about 40% of the 1–5 scale **[VERIFIED]** ([Kumar et al.](https://arxiv.org/html/2604.25235v1)). AesEval-Bench (ICLR 2026) found that the best model was right 72.52% of the time on aesthetic judgments, but **IoU for localizing errors was below 0.20** **[VERIFIED]** ([arXiv](https://arxiv.org/html/2603.01083v1)).

In other words, VLMs are weakest exactly where deck-lint is strongest: geometric localization such as overlap and margins. SlideAudit adds two points. Humans also disagree about "design quality" in general (κ = 0.26). And giving the LLM extra saliency, Gestalt or color metrics does **not** improve F1 **[VERIFIED]**. Consequence: narrow, objectively checkable rules (overflow, out-of-bounds, contrast ratio) should reach much higher agreement than an overall aesthetic score. This is the direct argument for the linter approach **[INFERRED]**.

The gap that a deck-lint-based benchmark could occupy has three points **[INFERRED from the descriptions of the benchmarks above]**:

- No benchmark **fixes a design system and then compares models within it**. All of them compare products or agents on free-form design.
- No benchmark **scores design from the raw OOXML structure**. The closest is PPTArena's IF judge, which reads the XML diff, but to score instruction following.
- A metric set built on `dump` has exact geometry, z-order and style, so it is more precise than the pixel- or saliency-based approximate metrics in the layout literature (Alignment, Overlap, Underlay, Validity, Occlusion from PosterLlama/LayoutRectifier) **[INFERRED]** ([PosterLlama](https://arxiv.org/html/2404.00995v3); [LayoutRectifier](https://arxiv.org/html/2508.11177v2)).

There is precedent for "linter as scoring function": LintBench uses Markdown and Python linters to score LLM output, though it has nothing to do with slides **[VERIFIED]** ([lintbench.ai](https://lintbench.ai/)).

The biggest risk is **Goodhart**. An empty slide scores perfectly on overlap, and a model can learn to shrink text to dodge overflow. So the benchmark needs a content gate similar to the Validity metric in the layout literature, or a completeness check in the style of QuizBank/PresentBench **[INFERRED]**.

To be credible, the benchmark also needs the following **[INFERRED]**:

- Collect **human pairwise votes** on a subset, with multiple raters per item, and report ρ against the human–human ceiling, as PresentBench did.
- Report **per-rule precision/recall** against human-labeled errors. SlideAudit (CC BY) could serve partly as an external test set, if its slides can be converted to PPTX. This is uncertain, since the dataset may be images only.
- **Freeze the rule set version** for each release and publish the linter version alongside each score.
- Do not depend on a preview judge model, since those models will be retired.
- State the scope clearly: the benchmark measures **"design-system compliance and layout hygiene"**, not overall aesthetics.

On naming, **avoid every variant of "Slide Bench"**:

- **SlidesBench** is AutoPresent's benchmark (CVPR 2025) and has a dataset on HuggingFace.
- **SlideBench** is both slidebench.org, "AI Presentation Tool Benchmark & Head-to-Head Comparisons", a live leaderboard in the same field, and SlideChat's pathology benchmark (CVPR 2025) **[VERIFIED]** ([AutoPresent](https://github.com/para-lost/AutoPresent); [slidebench.org](https://www.slidebench.org/); [SlideChat](https://openaccess.thecvf.com/content/CVPR2025/papers/Chen_SlideChat_A_Large_Vision-Language_Assistant_for_Whole-Slide_Pathology_Image_Understanding_CVPR_2025_paper.pdf)).
- The names PresentBench, DECKBench, PPTBench, PPTEval, PPT-Eval, PPTArena, TSBench, SlideAudit and DeckCraft (a commercial product) are all taken.
- Even **"deck-lint" collides with bunchc/deck-lint**, a config linter for Kong decK. The risk is low because the domain is different. "slidelint" is a linter for PDF slides, Apache-2.0 **[VERIFIED]** ([bunchc/deck-lint](https://github.com/bunchc/deck-lint); [slidelint](https://github.com/enkidulan/slidelint)).
- **"DeckEval"** appears to be free, but the evidence is weak because it comes only from web search, and the GitHub, PyPI, HF and arXiv search APIs were all blocked during the research **[VERIFIED as to search scope]** ([sample search result](https://www.jotform.com/form-templates/presentation-evaluation-form)).

Recommendation: name the project after its differentiator (deterministic OOXML linting under a fixed design system), and run exact collision checks on GitHub, PyPI, npm, HF and arXiv full text before creating the package **[INFERRED]**.

## The Opus 5.5 "artistic" trend transfers process, not material

The "artistic" works of September 2026 did not come from a magic prompt. They came from a process written down into files.

For PDoomVideo, the README says the video "took two generations, both in Claude Code": the first pass used Opus 5.5 (Medium), the second used Opus 5.5. The README also says "ANIMATION_GUIDE.md was written by Opus to brief the subagents it ran in parallel" **[VERIFIED]** ([PDoomVideo README](https://raw.githubusercontent.com/JohnHeibel/PDoomVideo/main/README.md)). That guide is in effect a **contract for subagents**:

- One file per chapter, and "Only edit your own chapter file".
- Each shot must be "a pure function of `t`", with no `Math.random()`.
- A safe zone for the karaoke band.
- A budget of "≤ 2.5 s per frame".
- Each subagent renders its own contact sheet and then opens it to look **[VERIFIED]** ([PDoom ANIMATION_GUIDE](https://raw.githubusercontent.com/JohnHeibel/PDoomVideo/main/ANIMATION_GUIDE.md)).

ClaudeAnimationBase is the second generation, built from "an analysis of what the model did and didn't do well". Its guide is a **taste document** containing:

- 3 goals and 7 rules.
- A storyboard with a self-check.
- A render/review loop at three zoom levels (sheet, strip, crop), with a minimum budget.
- A "Common failures" list, i.e. "the things that make a Clawd video look generated".
- Worked examples marked "one idea, not a template".

The user prompt is a single line: "Read ANIMATION_GUIDE.md, then make a 15-second video…". The author also notes that "the reasoning level corresponds to how 'extravagant' and detail-oriented the model makes the scene", with every test clip run at xhigh **[VERIFIED]** ([ClaudeAnimationBase README](https://raw.githubusercontent.com/JohnHeibel/ClaudeAnimationBase/main/README.md); [Base ANIMATION_GUIDE](https://raw.githubusercontent.com/JohnHeibel/ClaudeAnimationBase/main/ANIMATION_GUIDE.md)).

Ishaan Kalra's riso-rooms skill was inspired by Kevin Ngo's page "a small light, room by room", which he labeled "Created with Claude Opus 5". The skill goes further: **style lives in the engine, not in prose**. The four rules of the look (4-ink Riso halftone, multiply overprint, ~1 px misregistration, hand-wobbled strokes with a 12 fps "boil") are all enforced by the engine. The model handles only composition, and is forbidden: "Don't use `ctx.fillStyle = '#hex'` … Always go through the pen" **[VERIFIED]** ([riso-rooms SKILL.md](https://raw.githubusercontent.com/IshaanKalra2103/riso-rooms/main/skills/riso-rooms/SKILL.md); [Kevin Ngo's X post](https://x.com/kevin_t_ngo/status/2100238648218427563)).

The same repo has **slide-craft**, which applies exactly this discipline to 1280×720 HTML decks:

- "nothing gets built before the spine exists".
- "A heading states the finding, not the topic".
- A table of type-size tokens.
- A space budget: "720 tall… leaves about 500px of body… a content slide holds one component and at most one line of lede".
- A list titled "Never do these (they are what 'AI slop' looks like)" **[VERIFIED]** ([slide-craft SKILL.md](https://raw.githubusercontent.com/IshaanKalra2103/creative-skills/main/skills/slide-craft/SKILL.md)).

The official documentation says the same thing. The prompting guide for Opus 5.5 says that "Generic instructions like 'avoid a generic AI look' swap one default for another" and recommends **a concrete avoidance list that names each pattern, then extending it gradually over iterations** **[VERIFIED-S]** ([Prompting Claude Opus 5.5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5)). Anthropic's frontend-design skill adds three things **[VERIFIED]** ([frontend-design SKILL.md](https://raw.githubusercontent.com/anthropics/skills/main/skills/frontend-design/SKILL.md)):

- A two-pass process: plan the tokens, check the plan against five "AI-design clusters", and only then build.
- The principle "Spend your boldness in one place".
- Anchor every aesthetic choice in the subject's own materials and language.

What transfers to a deck toolchain is the **process** **[INFERRED]**:

1. **Separate "what" from "how".** A `DECK_GUIDE.md` file following the Base guide's framework, with a priority clause: the user decides the *content*, the guide decides the *method*, and if the user asks for something the guide forbids, follow the user.
2. **A storyboard with "reads" before any OfficeCLI command.** Each slide records: its purpose, the finding the title asserts, the list of what the audience must understand in order, and the bridge to the next slide. The line "For every moment, ask what the viewer needs to understand and how long that will take them" is Duarte's 3-second Glance Test written in the language of animation. If the reads do not fit on one slide, split the slide; do not cram.
3. **A "pen" API that accepts only token names** (`title()`, `statement()`, `figure()`, `chart()`, `caption()`), and forbids ad hoc hex values and pt sizes. An accompanying linter catches any color, font size or font outside the tokens.
4. **A short contract for parallel workers**: each worker edits only its own slide file; safe zones for footer, logo and page number; a budget for the number of shapes and text runs per slide.
5. **An anti-"twinning" rule**: code copies values and so produces identical card grids. Add a lint rule "at most N consecutive slides with the same layout", and state explicitly that the sample deck is "one idea, not a template".
6. **Ask only one high-value question** instead of a long interview.
7. **"One piece" continuity**: one visual world, one color or intensity arc across sections, one motif that repeats and escalates, and a final slide that "rhymes" with the first.

Allie K. Miller's workflow in the same week is a hybrid variant worth learning from: Claude Code generated six slide options as PNGs through an image model, then "converted her two picks into editable PowerPoint text boxes and shapes" **[VERIFIED-S]** ([The Neuron, Sep 23](https://www.theneuron.ai/digest/everything-that-happened-in-ai-today-wednesday-september-23-2026/)).

What **does not transfer is the material**. A .pptx is a static scene graph. Boil, per-frame redraw, rotated halftone with multiply, and p5.brush-style watercolor have no native equivalent. Getting them requires baking them into images (losing editability) or generating freeform vectors from seeded noise (editable but static). This is a **[GUESS]** at the level of OOXML capability in the original notes. However, one related point has been verified: Google Slides converts pattern fills to solid colors on import **[VERIFIED]** ([BrightCarbon](https://www.brightcarbon.com/blog/convert-powerpoint-google-slides/)).

The costs are real too:

- Serious works run from about 40 minutes to nearly 6 hours, for example "339 minutes alone overnight in headless Claude Code at xhigh" **[VERIFIED]** ([frontier-games](https://raw.githubusercontent.com/theolundqvist/frontier-games/main/README.md)).
- Two runs at max effort exhausted the 128K reasoning budget **[VERIFIED-S]** ([The Neuron, Sep 22](https://www.theneuron.ai/digest/everything-that-happened-in-ai-today-tuesday-september-22-2026/)).
- The "one-shot" label is self-reported by the authors. PDoom was in fact two generations, with human feedback in between **[VERIFIED-S]** ([OrcaRouter](https://orcarouter.ai/blog/claude-opus-5-5-video-plan-one-shot)).

Opus 5.5 defaults to `medium` effort and advises "Reserve xhigh and max for measured quality gains" **[VERIFIED-S]**. A sensible allocation is **[GUESS]**: the planner (storyboard, style choice, critique) runs at high or xhigh; per-slide workers run at medium; checkpoint to files instead of relying on one long max pass.

## .pptx keeps embedded fonts only on PowerPoint desktop, and OfficeCLI needs three patches

Typography is the biggest design lever, and it is also where .pptx is weakest.

Structurally, font embedding needs four components **[VERIFIED]** ([pptxboss PR #14](https://github.com/4thel00z/pptxboss/pull/14); [pandoc #11492](https://github.com/jgm/pandoc/issues/11492)):

- The `p:embeddedFontLst` element in `presentation.xml`, placed after `p:notesSz`.
- `ppt/fonts/fontN.fntdata` parts in EOT format.
- Relationships of type `font`.
- The entry `<Default Extension="fntdata" ContentType="application/x-fontdata"/>`. Without this entry, PowerPoint reports the file as corrupt.

OfficeCLI 1.0.152 **has no prop or command for embedding fonts in PPTX**. `embedFonts` exists only for docx, and `add-part` accepts only charts **[VERIFIED – sandbox `officecli help all`, `officecli help pptx add-part`]**. A Python post-processor of about 150 lines solves this. It wraps the TTF in an uncompressed EOT 2.2 header and adds the part, relationship and content type. The resulting deck **passes `officecli validate`**, and the font parts **survive OfficeCLI's `raw-set` and `close`** **[VERIFIED – sandbox `A_eot22.pptx`, `D_hybrid.pptx`]**. The validator catches element-order errors but does not inspect font bytes, so "validate pass" does not mean PowerPoint will accept the payload **[VERIFIED/INFERRED – sandbox `B_rawttf.pptx`]**. Size cost: two IBM Plex Serif styles took the deck from 9.9 KB to 151.6 KB **[VERIFIED – sandbox]**.

Viewer support for embedded fonts varies widely:

| Viewer | Shows embedded fonts? | Label |
|---|---|---|
| PowerPoint for Windows | Yes | [VERIFIED] ([RDP FAQ](https://www.rdpslides.com/pptfaq/FAQ00076_Embedding_fonts.htm)) |
| PowerPoint for Mac, subscription version (16.11+ per RDP, "2019+/M365" per another source) | Yes | [VERIFIED, version cutoff still conflicting] ([MS Q&A 5012732](https://learn.microsoft.com/en-us/answers/questions/5012732/limitations-and-issues-when-embedding-fonts-in-pow)) |
| PowerPoint for the web | Partly: TTF embedded from Windows displays correctly, files embedded from Mac report "Missing font" | [VERIFIED] ([MS Q&A 5619322](https://learn.microsoft.com/en-us/answers/questions/5619322/font-not-displaying-on-powerpoint-online)) |
| PowerPoint for Android / iOS | Android yes (per a vendor FAQ); iOS unclear | [VERIFIED-weak / GAP] ([Moonleo FAQ](https://www.moonleo.com/presentation-font-embedder-for-mac/frequently-asked-questions/)) |
| Keynote | No: "Unsupported fonts are substituted" | [VERIFIED] ([Apple](https://www.apple.com/keynote/compatibility/)) |
| Google Slides | No: non-Google fonts are replaced with Arial; embedded fonts also revert to Arial on edit. Google Fonts names are usually preserved | [VERIFIED + INFERRED] ([BrightCarbon](https://www.brightcarbon.com/blog/convert-powerpoint-google-slides/)) |
| LibreOffice 24.2 / 25.8+ | 24.2 ignores them (tested in the sandbox); 25.8 adds font embedding for PPTX | [VERIFIED] ([Collabora](https://www.collaboraonline.com/blog/collabora-productivity-contributions-in-libreoffice-25-8/)) |

A few more risks to know about **[VERIFIED]**:

- Windows PowerPoint version 2410 (November 2024) stopped displaying embedded fonts in **programmatically generated** decks. That question was never answered, so it is unclear whether it has been fixed ([MS Q&A 2120886](https://learn.microsoft.com/en-us/answers/questions/2120886/embedded-fonts-dont-work-on-windows-powerpoint-aft)).
- Embedded `.otf` files with CFF outlines are unreliable ("We see many more embedding problems with .OTF than .TTF").
- Font subsetting prevents recipients from editing the text.
- OFL permits font embedding, and documents created with OFL fonts are not bound by that license ([Neuxpower](https://support.neuxpower.com/hc/en-us/articles/360007786978-Embed-subset-or-remove-embedded-fonts-in-PowerPoint-or-Word)).

What nobody has tested is whether PowerPoint accepts **uncompressed** EOT written by a third party. PowerPoint itself writes MTX-compressed EOT. LibreOffice and dom-to-pptx write the uncompressed form, so it will likely work, but it has not been tested.

From this, the most robust font strategy has three layers **[INFERRED]**:

1. Embed TTF (`glyf` outlines, OFL, no subsetting) for PowerPoint users.
2. Choose font families that are on Google Fonts, so Google Slides and Keynote can find them by name.
3. Keep a metric-compatible system fallback for the remaining viewers.

A cross-cutting note: IBM Plex is on impeccable's "reflex font" list ([new-work.md](https://github.com/pbakaus/impeccable/blob/e0881d2/skill/reference/new-work.md)). Using Plex Serif for a technical spike is fine, but it should not become a style pack's default font **[INFERRED]**.

The second patch is **render QA**. OfficeCLI's renderer outputs a font stack that ends in `sans-serif` and has no `@font-face`. So every serif font that is not installed shows up as sans in QA screenshots. The PNG renders with and without `FONTCONFIG_FILE` were byte-identical (27,699 bytes) **[VERIFIED – sandbox]**. LibreOffice does render the correct font if `FONTCONFIG_FILE` points to the project's local font directory. The approach that works for the OfficeCLI pipeline is **injecting base64 `@font-face` into the `officecli view html` output and capturing it with headless Chrome**. This rendered Plex Serif Regular and Bold correctly **[VERIFIED – sandbox `shot_fontface.png`]**. Anthropic's pptx skill also warns that LibreOffice QA substitutes fonts with different widths, so "your QA preview can show text overflow (or fit) that the real deck won't have" **[VERIFIED]** ([Anthropic pptx SKILL.md](https://github.com/anthropics/skills/blob/main/skills/pptx/SKILL.md)). Consequence: every deck-lint overflow rule must declare its font metric source, like pptlint's `fallback_policy: forbid` **[INFERRED]**. The only automated way to check that embedded fonts actually display is `view screenshot --render native` on a Windows runner with PowerPoint **[INFERRED from `officecli help view`]**.

For effects, the set that is safe on every viewer tested is: solid fill, gradient and alpha; a simple outer shadow; preset and custom geometry; rotation; `spc`; and `cap` **[VERIFIED – sandbox `effects.pptx` + BrightCarbon/Apple]**. The risky effects are:

- Glow, soft edge and bevel are removed by Google Slides.
- LibreOffice 24.2 drops reflection and bevel, and draws glow as a hard outline.
- WordArt and text effects are not supported by Keynote.
- Gradient strokes are collapsed to a solid color by Keynote.
- Text transparency is lost in Google Slides.
- Morph is lost in Google Slides.

Sources: [BrightCarbon](https://www.brightcarbon.com/blog/convert-powerpoint-google-slides/), [Apple](https://www.apple.com/keynote/compatibility/) **[VERIFIED]**.

Even the two renderers in the sandbox disagreed on vertical anchor and on text color inside a shape at 40% opacity. This means **QA screenshots can mislead in both directions** **[VERIFIED/INFERRED]**. A "portable-beautiful" profile should rely on typography, fill, alpha, at most one soft shadow, geometry and letter-spacing. Glow, bevel, reflection and WordArt should only be accents reserved for PowerPoint **[INFERRED]**.

The "design in HTML, convert to editable PPTX" route is feasible for flat, box-model designs. **dom-to-pptx 2.1.2** (npm, 2026-09-14, MIT) is the strongest option: it maps the live DOM to native PptxGenJS text boxes and shapes, keeps SVG as vectors, and **embeds web fonts as EOT** **[VERIFIED]** ([dom-to-pptx](https://github.com/atharva9167j/dom-to-pptx)). Other tools are weaker **[VERIFIED]**:

- Marp's `--pptx-editable` goes through PDF via LibreOffice: "text doesn't reflow; long runs overlap on edit". The maintainer declined a native mode using the dom-to-pptx engine ([marp-cli #725](https://github.com/marp-team/marp-cli/issues/725)).
- Slidev has just added `pptx-editable` ([Slidev docs](https://sli.dev/guide/exporting.html)).
- Anthropic's pptx skill dropped html2pptx and moved to pptxgenjs directly. Someone asked why, but nobody answered ([issue #531](https://github.com/anthropics/skills/issues/531)).

Recommendation: use HTML as **a design and QA surface, not the source of truth**. dom-to-pptx could be an optional second back end for layouts that are easy to express in CSS, accepting that it does not reuse masters/layouts **[INFERRED; the lack of master reuse is a GUESS]**.

Summary of OfficeCLI capabilities **[VERIFIED – sandbox `officecli help`]**:

- **Can do:** the full set of effect props (`gradient`, `opacity`, `shadow`, `glow`, `softEdge`, `reflection`, `bevel`, `geometry`, `spc`, `cap`, `lineSpacing`); `morph` plus a transition gallery; theme fonts `headingFont`/`bodyFont`; `{{key}}` template merge; raw XML via `raw-set`; `validate`; `view html`/`screenshot`; an MCP server; and bundled skills.
- **Cannot do:** HTML import (`import` only loads CSV/TSV into Excel); font embedding for PPTX; `@font-face` in the renderer.

Two quirks from the sandbox need handling directly in deck-lint **[VERIFIED – sandbox]**:

- `officecli dump` returns a flat list of `add`/`set` commands, with geometry in cm, font, size, color and zorder. The linter has to "fold" this list back into individual shapes.
- The positional path `shape[N]` counts only shapes and textboxes, **skipping charts**. This is undocumented, and it is what caused the index bug in the prototype. The adapter must resolve by shape `id`, not by position.

The most valuable upstream contributions, in order **[INFERRED]**:

1. An `embedFont` prop on `/presentation`, using the font part already available in the Open XML SDK. The SDK API details are from memory and unchecked.
2. Emit `@font-face` in `view html` from `.fntdata` files or a `--font-dir`.
3. Make the serif fallback land on a serif instead of on sans.
4. Document how `shape[N]` is counted.

## impeccable is a thin router over a deterministic binary: port the contract layer as is, rewrite the material layer

Internally, impeccable (commit `e0881d2`, skill 4.3.1) consists of a single source skill, `SKILL.src.md` at about 12.5 KB, plus 36 `reference/*.md` playbooks loaded only when needed, 4 subagents, and a launcher for a self-contained Rust binary ("There is no Node at runtime"). The build step generates about 18 variants for different harnesses **[VERIFIED]** ([SKILL.src.md](https://github.com/pbakaus/impeccable/blob/e0881d2/skill/SKILL.src.md); [ENGINE.md](https://github.com/pbakaus/impeccable/blob/e0881d2/docs/ENGINE.md)).

SKILL.md is deliberately thin. It contains:

- A "permission to be bold" statement.
- A 3-step setup: run `impeccable context` once; load the command's playbook; read `craft-floor.md` right before every UI edit.
- 3 design rules: "The brief wins", "Refinement preserves; redesign replaces", "Visual authority is evidence, not a filename".
- 4 visitor modes.
- A table of 24 commands.
- Routing rules.

The binary emits uppercase directive tokens (`NO_PRODUCT_MD`, `CONTEXT_STALE`, `MANUAL_DETECTOR_REQUIRED`…) that the skill text reacts to. Every normative sentence carries a `<!-- rule:id -->` anchor that tests reference **[VERIFIED]**. The overall architecture is **thin router + thick playbooks + deterministic binary with verbs**: judgment lives in markdown, and the deterministic parts live in testable code **[INFERRED]**.

One historical detail matters for the port. On 2026-05-28, impeccable **deleted its standalone principle files** (typography, color-and-contrast, spatial-design…) and merged them into the per-command playbooks (typeset, colorize, layout) **[VERIFIED]** ([commit 9ffd3211](https://github.com/pbakaus/impeccable/commit/9ffd3211)). The slide version should go straight to that approach: put slide-specific numbers (minimum pt size per mode, words per slide) into `typeset.md`, `layout.md` and `craft-floor.md`, instead of rebuilding a generic `typography.md` **[INFERRED]**.

The context layer has three tiers **[VERIFIED]** ([new-work.md](https://github.com/pbakaus/impeccable/blob/e0881d2/skill/reference/new-work.md); [document.md](https://github.com/pbakaus/impeccable/blob/e0881d2/skill/reference/document.md); [init.md](https://github.com/pbakaus/impeccable/blob/e0881d2/skill/reference/init.md)):

- **`PRODUCT.md`** holds the "product truth". It contains nothing visual, and has an "Evidence on Hand" section that records what *must not be invented*.
- **`DESIGN.md`** follows the Google Stitch format: YAML frontmatter holding tokens ("Tokens are normative; prose provides context") plus 8 fixed sections. A `.impeccable/design.json` sidecar holds what the frontmatter cannot.
- A **surface brief** for each surface contains a 6-block "Direction contract": THESIS, OWN-WORLD, STORY, FIRST VIEWPORT, FORM, FINISH. It comes with a test sentence: "If a block reads like a mood, the direction is not decided yet".

The detector is a Rust registry of **61 rules: 32 `slop` and 29 `quality`**. Each rule has an `id`, `category`, `scopes` (`type`, `layout`), `severity` (`warning` by default; `advisory`, which never fails; or `error`) and a backlink to the corresponding skill passage. Rules run on 4 engines: regex, static-html, browser via CDP, and visual contrast. The output contract includes **[VERIFIED]** ([registry.rs](https://github.com/pbakaus/impeccable/blob/e0881d2/crates/foundation/src/registry.rs); [CLI-CONTRACT.md](https://github.com/pbakaus/impeccable/blob/e0881d2/docs/CLI-CONTRACT.md)):

- Finding JSON with a fixed key order: `antipattern, name, description, severity, category, file, line, snippet`.
- Human output to stderr, JSON to stdout.
- Exit codes **0 = clean, 1 = could not scan, 2 = findings present**.
- Ignores via config (`ignoreRules`, `ignoreFiles`, `ignoreValues` with a reason) and inline ignores.

The hook registers two events: **PostToolUse (matcher `Edit|Write`, 5-second timeout)** and **Stop (30 seconds)**. Each edit runs only the **immediate tier of 13 mechanical rules**. The full rule set runs once at Stop, on every file touched in the session. Output policy **[VERIFIED]** ([hooks.md](https://github.com/pbakaus/impeccable/blob/e0881d2/skill/reference/hooks.md); [.claude/settings.json](https://github.com/pbakaus/impeccable/blob/e0881d2/.claude/settings.json); [stop_baseline.rs](https://github.com/pbakaus/impeccable/blob/e0881d2/crates/hook/src/stop_baseline.rs)):

- Findings are deduplicated per session and capped at **5 findings / 8,000 characters**.
- Findings are injected via `additionalContext`; the exit code is always 0, and the hook never blocks.
- A triage footer is attached, including the line "Self-serve ends at ignore-value".
- A `stop_hook_active` guard prevents loops.
- Baseline suppression, based only on a verified preimage.

On verification, impeccable hard-codes: "Verify in bounded passes, not a loop… two rounds is the ceiling". After that, review moves to a **finish-reviewer subagent with fresh context**. This subagent has only 4 disposition words (`recapture`, `rebuild`, `fix`, `ship`), a 5-section output, at most 8 fixes, and a budget of about 10 turns **[VERIFIED]** ([finish-reviewer](https://github.com/pbakaus/impeccable/blob/e0881d2/skill/agents/impeccable-finish-reviewer.md)). The reason comp-first needs a state machine with measurable gates is stated outright: "Models systematically believe their HTML, CSS, and SVG recreation of an image succeeded when it did not" **[VERIFIED]**.

The table below gives the port verdict for each component (the verdict column is **[INFERRED]**, except where marked GUESS):

| impeccable component | Verdict | Deck version |
|---|---|---|
| SKILL.md shape, routing, per-command playbooks, `rule:id` anchors | Port as is | Setup runs `deck context`, loads `reference/<cmd>.md`, loads `craft-floor.md` before every .pptx write. Supports only Claude Code for now |
| "Verify in bounded passes", finish reviewer, documenter | Port as is | Render every slide to PNG plus a contact sheet in one batch; fix in one batch; at most 1 confirmation round |
| PRODUCT.md, Direction contract | Port, rename fields | Audience, the decision the deck must drive, Evidence on Hand. FIRST VIEWPORT becomes OPENING SLIDE; add HEADLINE SPINE [GUESS] |
| Visitor modes | Light rewrite [GUESS] | Pitch / Pre-read / Training / Keynote, plus a Delivery axis: projected, screen-share, async |
| DESIGN.md (Stitch) and design.json | Moderate rewrite | Keep color, type and spacing tokens (in pt, mapped to theme slots `accent1..6`, `dk1/lt1`). "Components" becomes a layout catalog with placeholder boxes in % or EMU and master names in the .potx |
| Registry schema, finding JSON, exit 0/1/2, advisory, config ignore | Port as is | `line` = slide number, add a `shape` field (shape id). Inline ignores go in slide notes or the shape's `descr`, because .pptx has no source comments |
| 4 detector engines | Rewrite | OOXML model engine (from `dump` + lxml), text, render (PNG), visual contrast |
| 61 rules | ~25 translatable, ~15 not applicable, many new rules | Translatable: `side-tab`, `gradient-text`, `cream-palette`, `ai-color-palette`, `kicker-above-heading`, `icon-tile-stack`, `nested-cards`, `low-contrast`, `gray-on-color`, `tiny-text`, `text-overflow`, `design-system-*`… Not applicable: `marquee`, `script-error`, `layout-transition`… |
| Hook | Rewrite the trigger, keep the policy | Matcher `Bash` (plus `Write` for deck-generating scripts), parse `tool_input.command` to find officecli commands and the target .pptx file. Immediate tier = rules on the XML model; Stop = render-based rules and cross-slide rules |
| Baseline suppression | Rewrite, simpler | Lint the .pptx file before the session's first write command and store the set of `rule:slide:shape` hashes. Dedupe key `rule:slideN:shapeId` |
| Critique A/B split into subagents, audit /20 | Keep the structure, rewrite the heuristics | Replace Nielsen-10 with presentation heuristics: one message per slide, headlines that tell the story, legibility at a distance, data honesty… [GUESS] |
| live / generate / browser extension / native refs | Not applicable | Could be replaced by `variants N <slide>`, which generates N options with a comparison contact sheet [GUESS] |

On commands: init, shape, critique, polish, bolder, quieter, distill, typeset, layout, colorize, clarify, document and extract port with light edits. Audit, harden, adapt, animate, delight and optimize need substantial reinterpretation. Live, generate, onboard and overdrive do not apply. Deck-specific commands such as `storyline`, `notes`, `handout`, `rehearse` and `variants` can be added. The "skeleton test" in `bolder` becomes a "headline test": read only the titles in order, and they must tell the story **[INFERRED/GUESS]** ([bolder.md](https://github.com/pbakaus/impeccable/blob/e0881d2/skill/reference/bolder.md)).

If the agent drives OfficeCLI through the MCP server instead of Bash, the hook matcher must catch MCP tool names (of the form `mcp__<server>__…`). This is a reason to standardize on calling OfficeCLI through Bash from the start, since it is easier to observe **[GUESS]**.

## A measurable canon, style packs with switches, and "editorial" has become Claude's signature

### The canon agrees on "one claim per slide" and disagrees on density

The classic authors agree on a small set of measurable rules:

- **Alley (assertion–evidence):** the title is an assertion of "no more than two lines", body 18–24 pt, lists of "no more than four items". A controlled study (55 and 56 participants) found that assertion–evidence slides averaged **19.3 words/slide**, and 100% of slides had a relevant illustration. This group recalled complex concepts better on a delayed multiple-choice test (2.17 vs 1.84, p = 0.038). The evidence is modest: the essay test did not reach significance, and the bullet group recalled minor details better (69% vs 39%) **[VERIFIED]** ([ASEE](https://peer.asee.org/assertion-evidence-slides-appear-to-lead-to-better-comprehension-and-recall-of-more-complex-concepts.pdf); [PSU](https://cpb-us-e1.wpmucdn.com/sites.psu.edu/dist/7/13153/files/2008/10/Assertion-Evidence-Slides-Instruction_Set.pdf)).
- **Tufte:** charts in PowerPoint textbooks average only **12 numbers per chart**, versus 120+ in the *New York Times* **[VERIFIED]** ([Tufte](https://www.fceia.unr.edu.ar/~mcristia/tufte-powerpoint.pdf)).
- **Duarte:** the audience must understand a slide "in three seconds or less" **[VERIFIED]** ([Glance Test](https://www.duarte.com/resources/guides-tools/the-glance-test/)).
- **Consulting:** action titles of "Maximum 15 words", "Never exceed two lines", "Every data point has a source", the same title size on every slide **[VERIFIED, secondary source]** ([Deckary](https://deckary.com/blog/consulting-slide-standards); [Slideworks](https://slideworks.io/resources/how-mckinsey-consultants-make-presentations)).
- **Reynolds:** "2–3 consistent colors", and chart titles must be assertions **[VERIFIED]** ([garrreynolds.com](https://www.garrreynolds.com/design-tips)).
- **Kawasaki:** "no font smaller than thirty points" **[VERIFIED]** ([guykawasaki.com](https://guykawasaki.com/the_102030_rule/)).
- **Swiss style:** grid, sans type, "flush left, ragged right", asymmetric layout **[VERIFIED]** ([OpenTextBC](https://opentextbc.ca/graphicdesign/chapter/1-6-its/)).
- **Refactoring UI:** "Labels are a last resort", "Use fewer borders", no gray text on colored backgrounds **[VERIFIED]** ([Refactoring UI notes](https://gist.github.com/selcukcihan/b9418596a98abfcd4bbc622550820cc5)).

The disagreement is about density. Tufte and the consultants want it dense. Reynolds, Kawasaki and Hale want it sparse. The resolution is two **modes** that must not be mixed **[INFERRED]**:

- **Presented:** about 7–20 words per slide, body ≥ 24 pt, title ≥ 36 pt.
- **Read** (slidedoc): about 100–250 words, body 12–20 pt. This figure comes from a secondary summary and is not confirmed as Duarte's number ([Pallotta](https://www.lucapallotta.com/slidedocs/)).

One important conflict must be recorded: Anthropic's pptx skill prescribes body text at **14–16 pt**. That is a read-mode size, lower than every presented-mode source **[VERIFIED]** ([Whitepage](https://www.whitepage.studio/blog/presentation-font-sizes); [Anthropic pptx SKILL.md](https://github.com/anthropics/skills/blob/main/skills/pptx/SKILL.md)).

A few technical numbers to put in DESIGN.md:

- **Tracking:** caps should be spaced 5–12%, lowercase should not ([Butterick](https://practicaltypography.com/letterspacing.html)). In OOXML, `a:rPr/@spc` is measured in hundredths of a point, so one can lint "caps ≤ 14 pt have `spc` in the range [5×size, 12×size]" **[INFERRED; the `spc` unit is from memory, unchecked]**.
- **Figures:** numeric columns must use tabular figures ([Butterick](https://practicaltypography.com/alternate-figures.html)). PowerPoint has no UI for OpenType features, so the font's *default* figures determine alignment **[VERIFIED]** ([MS Q&A](https://learn.microsoft.com/en-us/answers/questions/5217674/is-there-any-way-to-access-stylistic-alternates-or)).
- **Color:** 2–4 colors, one accent ("Two accents are no accent"), contrast ≥ 4.5:1. The 7:1 target for projectors has only one source, and that source cites nothing **[VERIFIED, SINGLE]** ([designwithjack](https://designwithjack.dev/)).

### "Editorial" has become Claude's look: the Swiss pack needs hard guards

This is the most important warning for DESIGN.md.

On June 29, 2026, Kyle Chayka described the generic AI design style: "beige- and cream-colored backgrounds, rusty orange-hued accents", large "italicized" serifs, "tracked out" subheadings and "ticker-like text bars". Celine Nguyen, quoted in the piece, admits she is now "instinctively repulsed by the warm tones" **[VERIFIED]** ([Chayka](https://kylechayka.substack.com/p/the-generic-style-of-ai-web-design); [Pixel Envy](https://pxlnv.com/linklog/claude-aesthetic/)). For slides specifically, Plus AI (July 15, 2026) lists four signs **[VERIFIED]** ([Plus AI](https://plusai.com/blog/how-to-make-ai-slides-that-dont-look-like-ai-slop/)):

- "The warm cream canvas with muted red accents… the *same* palette on every AI-generated deck".
- Titles with an inserted italic serif phrase.
- "Every content block gets a tiny colored bar on top or on the side, along with an all-caps mini-label".
- Oversized rows of stat tiles.

Anthropic's own documentation also puts this look among the defaults to avoid **[VERIFIED/VERIFIED-S]**:

- frontend-design Cluster 1: cream background near `#F4F1EA`, display serif, terracotta accent near `#D97757`.
- frontend-design Cluster 5: letter-spaced uppercase eyebrows, meta joined with middle dots, a mono font for labels.
- The Opus 5.5 guide uses "cream or off-white background… monospace labels" as an example for an avoidance list.
- A dedicated `<claude>` block in impeccable states that Claude's prior for warm, bookish subjects is "cream grounds, serif display with italic accents… Treat that first palette as already spent".

Claude's own brand tokens (`#f4f3ee`, `#c96442`) are grouped into the "Warm Editorial" family **[VERIFIED]** ([awesome-claude-design](https://github.com/rohitg00/awesome-claude-design)).

The editorial rebuild in the sandbox (off-white, red, uppercase labels) is one step away from this tell. It works because it follows the canon: one claim, the evidence as a dense table, no boxes, flush-left, one accent. But the guards must be encoded as rules, not left to taste **[INFERRED]**:

- **Paper:** hue-neutral (chroma ≈ 0 or HSL saturation ≤ 4%, L ≥ 95%). Ban the cream codes `#F5F5DC`, `#FAF0E6`, `#FAEBD7`, `#FFF8E1`, `#f4f3ee`.
- **Accent:** must be a **true signal red** (hue ≈ 0–8°, high saturation). Not rust red or terracotta (hue ~15–25°, medium saturation, like `#c96442`).
- **Title:** no italic serif inserted into a sans title.
- **Letter-spaced caps:** use only when tied to data (column headers, axis labels, metadata). Do not use them as eyebrows on ≥ 50% of blocks.

This last point directly contradicts impeccable, where "kicker above heading" is banned outright ("no brief earns it back") **[VERIFIED]** ([craft-floor.md](https://github.com/pbakaus/impeccable/blob/e0881d2/skill/reference/craft-floor.md)). So deck-lint rules must be **context-dependent and per-pack**, not absolute.

Style families that already have concrete parameters for building packs (the source for each family is a vendor or aggregator spec, **[VERIFIED, SINGLE]**):

- **Keynote-minimal:** headline 72–140 pt, "hard budget of seven words", accent used "at most once per slide" ([SlideSpeak Keynote Minimal](https://slidespeak.co/slide-design-prompts/prompts/keynote-minimal)). The "everything centered both ways" default should be changed to a flush-left layout on Reynolds's 3×3 grid, because centering is a tell.
- **Economist / data-journalism:** white background, red rule `#E3120B` with a tag, horizontal gridlines only, a "Source:" line at the bottom left. Ban rounded cards, centering and bullets ([SlideSpeak Economist](https://slidespeak.co/slide-design-prompts/prompts/economist-style); [Ritz](https://medium.com/data-science/making-economist-style-plots-in-matplotlib-e7de6d679739)).
- **Consulting:** action titles of the same size on every slide, a source line plus page number, 3–4 colors.
- **Brutalist:** one saturated hue plus black and white, hard edges.
- **Riso:** 2–3 spot inks, grain, bone paper background ([freedesignmd](https://freedesignmd.com/lexicon/risograph)).

Each pack must declare four switches: **mode** (presented or read), **accent budget** (elements per slide), **container policy** (rules, boxes or nothing), and **alignment default**. A pack must also have an allowlist of "deliberately accepted defaults". The riso pack uses a cream background on purpose, while slide-craft bans cream **[INFERRED]**.

### ANTI-TELLS.md should start from about 30 tells with measurable signatures

The root cause for Claude-made pptx lies in the skill itself. Anthropic's pptx skill *recommends* "Icon + text rows (icon in colored circle…)", "Large stat callouts (big numbers 60-72pt with small labels below)", "Italic accent text for key stats" and "Every slide needs a visual element". These are all documented tells **[VERIFIED – pptx skill file installed in the environment, lines 92, 113–128]**. OfficeCLI's KPI card recipe produced a slide that looks AI-made. The editorial rebuild with the same tool looked professional **[VERIFIED – sandbox]**. The reason is that the KPI slide stacks five structural tells at once: three equal cards, cards everywhere, stat tiles, centering, and a flat hierarchy. The rebuild drops all five **[INFERRED]**. So DESIGN.md must **override** these defaults, not just add taste. The good parts of Anthropic's skill should be kept: the ban on accent lines under titles and on stripe bands, the cream hex list, and "don't center body text".

The table below is the seed for ANTI-TELLS.md. Every signature can be computed from the XML or from `dump`. Thresholds marked G are **[GUESS]** and need calibration:

| Tell | Measurable signature in .pptx | Source |
|---|---|---|
| Three equal cards regardless of item count | ≥ 3 sibling shapes with equal w/h (±3%, G), same fill, evenly spaced, each containing text | [decksmith](https://dev.to/decksmith/seven-signs-a-slide-deck-was-made-by-ai-1828); [Adpharm](https://www.theadpharm.com/insights/claude-design-without-the-ai-slop-look) |
| Cards everywhere / nested cards | Share of text frames inside a filled `roundRect`/`rect`; nesting depth ≥ 2 | [impeccable README](https://raw.githubusercontent.com/pbakaus/impeccable/main/README.md); [Chayka](https://kylechayka.substack.com/p/the-generic-style-of-ai-web-design) |
| KPI stat tile row | ≥ 3 text frames ≥ 48 pt, mostly digits/%/$, arranged in a row, label ≤ 16 pt below, no "Source" | [Plus AI](https://plusai.com/blog/how-to-make-ai-slides-that-dont-look-like-ai-slop/) |
| Everything centered | > 50% of paragraphs have `algn="ctr"`; a centered paragraph longer than 2 lines | [decksmith](https://dev.to/decksmith/seven-signs-a-slide-deck-was-made-by-ai-1828) |
| Every slide has the same layout | Number of layout fingerprint clusters ÷ number of slides < ~0.3 (G); low coefficient of variation of words per slide | [Beale](https://medium.com/design-bootcamp/a-designers-teardown-of-ai-slides-and-the-fixes-that-actually-move-them-7149203ed6ce) |
| Flat hierarchy / too many type sizes | Title/body ratio < ~1.5 (G); > 4 sizes per slide or > 6 sizes per deck | [Beale](https://medium.com/design-bootcamp/a-designers-teardown-of-ai-slides-and-the-fixes-that-actually-move-them-7149203ed6ce); [designwithjack](https://designwithjack.dev/) |
| Position drift across slides | Title x/y differs by > 0.05 in between slides; inconsistent body size | [decksmith](https://dev.to/decksmith/seven-signs-a-slide-deck-was-made-by-ai-1828) |
| No "confident emptiness" | No slide with ≥ 60% empty area and ≤ 7 words (G) | [2Slides](https://2slides.com/blog/why-ai-slides-look-fake-and-how-to-fix) |
| Dead band | A horizontal band > 25% of the slide height with nothing in it (prototype R4) | Sandbox; SlideAudit "Unbalanced Space" |
| Accent line under title / edge stripe / side-tab | Shape with one dimension ≤ 0.08 in, within 0.35 in below the title; rect ≤ 2% flush against a card edge | [Anthropic pptx](https://raw.githubusercontent.com/anthropics/skills/main/skills/pptx/SKILL.md); [Plus AI](https://plusai.com/blog/how-to-make-ai-slides-that-dont-look-like-ai-slop/) |
| Icon in a colored circle | Ellipse/roundRect ≤ 1 in with a centered glyph, repeated ≥ 3 times per slide | [impeccable README](https://raw.githubusercontent.com/pbakaus/impeccable/main/README.md); [ChatSlide](https://www.chatslide.ai/guides/how-to-make-ai-slides-not-look-ai-generated) |
| Uppercase eyebrow on every block | `cap="all"` run ≤ 14 pt, `spc` > 0, directly above a heading, present on ≥ 50% of blocks | [Plus AI](https://plusai.com/blog/how-to-make-ai-slides-that-dont-look-like-ai-slop/); [Chayka](https://kylechayka.substack.com/p/the-generic-style-of-ai-web-design) |
| Cream + rust ("Claude look") | Background hue 30–60°, S 15–60%, L ≥ 88%; accent hue 10–25°; matches the hex list | [Plus AI](https://plusai.com/blog/how-to-make-ai-slides-that-dont-look-like-ai-slop/); [awesome-claude-design](https://github.com/rohitg00/awesome-claude-design) |
| Italic serif phrase in a sans title | Title paragraph with ≥ 2 runs, one run `i="1"` in a different serif family | [Plus AI](https://plusai.com/blog/how-to-make-ai-slides-that-dont-look-like-ai-slop/) |
| Purple–blue gradient; identical shadows; glow | `gradFill` with a stop at hue 230–290°; `outerShdw` with the same parameters on ≥ 50% of shapes; `glow`/`softEdge` | [impeccable README](https://raw.githubusercontent.com/pbakaus/impeccable/main/README.md); [Adpharm](https://www.theadpharm.com/insights/claude-design-without-the-ai-slop-look) |
| Numbers without a source | Numeric tokens (≥ 2 digits, %, $, ×) with no text matching `^(Source\|Nguồn)[:：]` in the bottom 12% | [Deckary](https://deckary.com/blog/consulting-slide-standards) |
| Hype vocabulary, "not X but Y", em-dash, emoji/✓ bullets | Regex. Pangram: em-dashes 10× as often as humans, checkmarks 167×, "not X but Y" 3× | [Pangram](https://www.pangram.com/signs-of-ai-writing) |
| "Thank You" / "Questions?" closing slide | Title regex `^(thank you\|questions\??\|key takeaways\|in conclusion)$` | [Worldcom/Wikipedia](https://worldcomgroup.com/insights/how-to-spot-ai-writing-tips-from-wikipedia-on/) |
| Ticker bar | Full-width horizontal band ≤ 0.4 in tall, a single line of caps or items joined by · \| • | [Chayka on X](https://x.com/chaykak/status/2069787733648723979) |

Three points still in dispute should be written directly into ANTI-TELLS.md **[VERIFIED as to the existence of the disagreement]**:

- **Sentence titles.** decksmith treats sentence titles as a tell. Alley, consulting and Reynolds *require* titles to be assertions. Resolution: the red flag is a long, descriptive title that is neither a claim nor a label. Lint "≤ 2 lines, ≤ 15 words" in read mode and "≤ 7–10 words" in presented mode **[INFERRED]**.
- **How much palette matters.** Beale argues color is "almost never the problem", but many other sources treat purple gradients as a main tell.
- **"Intentional imperfections"** is a tip from exactly one vendor, and it conflicts with grid discipline.

Starting weights should rank **structure > decoration > language** (3/2/1). Reason: the only source that ranks causes (Beale) says structure dominates, and the KPI test in the sandbox also failed precisely on structure **[INFERRED/GUESS]**. Many "AI tell" sources are blogs of vendors that sell slide tools, so there is a conflict of interest, although their lists match those of independent sources **[INFERRED]**.

## Proposed architecture: deck-lint is the core, the skill is the shell

### Four layers, one shared contract

The proposed architecture has four layers:

1. **deck-lint**: a standalone Python package, usable outside the skill.
2. **deck CLI**: deterministic verbs that the skill calls, like impeccable's binary.
3. **Skill**: thin router, playbooks, style packs.
4. **Hooks**: wire lint into the agent loop.

All four layers share **impeccable's finding contract**: a row schema with `id`, `category`, `scopes`, `severity` and an anchor back to the skill; JSON to stdout, human-readable text to stderr; exit 0/1/2. This way CI, hooks and the benchmark share one pipeline **[INFERRED]**.

```
<project-name>/                      # check for name collisions at M0
├── deck-lint/                       # pip package, no dependency on the skill
│   ├── adapters/officecli_dump.py   # fold add/set → model; resolve by shape id (shape[N] skips charts)
│   ├── adapters/ooxml.py            # lxml: resolved theme colors, autofit, spc/cap, effects, notes, alt text
│   ├── engines/{model,text,render,visual}.py
│   ├── registry.py                  # id · slop|quality · scopes · severity · per-mode/pack thresholds · anchor
│   └── cli.py                       # --json --scope --tier immediate|full --pack --mode ; exit 0/1/2
├── deck-cli/                        # context · signals · render · embed-fonts · brief · critique-storage
├── skill/
│   ├── SKILL.src.md                 # stance + 3-step setup + command table + routing, anchors <!-- rule:id -->
│   ├── reference/{init,storyline,critique,polish,distill,bolder,quieter,typeset,layout,colorize,clarify,audit,harden,adapt,variants}.md
│   ├── reference/craft-floor.md     # Verify + Refuse; loaded right before every .pptx write
│   ├── ANTI-TELLS.md                # versioned; each tell ↔ rule id ↔ per-pack override
│   ├── agents/finish-reviewer.md    # 4 dispositions, ≤ 8 fixes, fresh context
│   └── packs/<swiss|economist|consulting|keynote|riso>/{SKILL.md,template.potx,examples/,api.md,pack.json}
├── pen/                             # token-only helper that wraps OfficeCLI
└── hooks/hooks.json                 # PostToolUse(Bash|Write) 5s + Stop 30s
# In the consuming repo: PRODUCT.md · DESIGN.md · .deck/briefs/<deck>.md · .deck/config.json
```

A working session runs as follows:

1. The skill runs `deck context` to load PRODUCT.md (audience, the decision to drive, Evidence on Hand), DESIGN.md and the deck brief. The brief contains the Direction contract, the HEADLINE SPINE and the storyboard with "reads".
2. The agent builds slides through `pen`. `pen` issues `officecli` commands via Bash.
3. The PostToolUse hook recognizes a .pptx write command, runs `deck-lint --tier immediate` on the model from `dump` within a budget of under 5 seconds, then injects at most 5 findings via `additionalContext`.
4. At Stop, the hook runs the full rule set plus the cross-slide rules. `deck render` (view html + `@font-face` + headless Chrome) produces a PNG per slide and a contact sheet. Only findings that are *new* relative to the baseline taken before the first write are reported.
5. The finish reviewer, in fresh context, reads the PNGs, the contract and the findings, then returns a disposition. The whole cycle is limited to at most two rounds.

Two design choices need discipline **[INFERRED]**:

- **Style lives in `pen` and `template.potx`, not in prose.** This is the lesson of riso-rooms. `pen` forbids raw hex values and pt sizes. The `design-system-*` rules catch anything that escapes the tokens.
- **MCP comes later.** OfficeCLI already has an MCP server **[VERIFIED]**, while impeccable reached 70k stars with only a CLI and hooks, without relying on MCP **[INFERRED]**. An MCP wrapper for deck-lint is only worth building when there is a need to serve hosts without hooks, such as Claude Desktop or Cowork **[GUESS]**.

### Build order: measure first, teach later

| Milestone | Deliverables | Exit criteria | Why it goes here |
|---|---|---|---|
| **M0 – Measurement foundation** | Name collision check (GitHub, PyPI, npm, HF, arXiv); `dump` adapter that resolves by id; registry schema; finding JSON + exit 0/1/2; port the 9 prototype rules to stable IDs; golden fixtures: the KPI-recipe deck **must fail**, the editorial deck **must pass** | Deterministic output with snapshot tests; the `shape[N]` index bug fix has a regression test | Every later layer calls the linter; the package name must be settled before publishing |
| **M1 – deck-lint v0.1** | ~25–30 rules: immediate tier (overflow/autofit, contrast that accounts for stacked shapes, tiny-text per mode, `design-system-*`, leftover placeholders, margin overflow) and deep tier (dead-band, structural tells, cross-slide drift, language tells); per-mode/pack thresholds; config ignore + ignore in notes | Runs without crashing on .pptx from ≥ 3 generation sources (OfficeCLI, pptxgenjs, python-pptx); every rule has positive and negative fixtures | This is the differentiating asset; ship it early to attract rule contributions |
| **M2 – Render & fonts** | `deck render` (view html + `@font-face` + Chrome → PNG + contact sheet); `deck embed-fonts` (checks `glyf`/`fsType`, no subsetting); `validate` as a gate; open upstream PRs to OfficeCLI (`embedFont`, `@font-face`, serif fallback, `shape[N]` docs) | Serif shows as serif in QA; one manual check on PowerPoint Win + Mac with uncompressed EOT | Without correct font QA, every visual critique is wrong |
| **M3 – Hooks** | PostToolUse(`Bash`\|`Write`) with a command resolver; Stop deep pass; baseline before the first write; `rule:slide:shape` dedupe; 5/8k cap; triage footer; `stop_hook_active` guard | A session building a KPI slide receives findings and fixes itself; no Stop loop | Turns the linter into an agent reflex |
| **M4 – Skill v0 + 1 pack** | SKILL.md router; craft-floor; init/PRODUCT.md; DESIGN.md (Stitch, pt units, layout catalog); ANTI-TELLS.md v1; brief + storyboard "reads"; `pen`; Swiss/editorial pack **with guards against the Claude look**; commands critique/polish/typeset/layout/distill/quieter/bolder | Blind A/B on a fixed brief, against Anthropic's pptx skill and the officecli-pptx skill (hands-on-deck has run this kind of eval) | At this point the skill stands on a measurable foundation |
| **M5 – Verification & expansion** | Finish-reviewer subagent + bounded passes; a second pack (Economist/data or consulting); .potx import as incumbent authority; `variants`; dom-to-pptx as an optional back end | A deck from a real corporate template keeps its master/layout, 0 `design-system-*` findings | Answers the "native corporate templates" question from HN |
| **M6 – Calibration → benchmark** | Labeled corpus of human-designed and AI decks (multiple raters); per-rule precision/recall; "AI-look score" weights; "same brief + same design system" pilot across multiple models; human pairwise-vote subset; frozen rule set | Report ρ against the human–human ceiling and against a VLM-judge baseline; publish the linter version with the scores | Publish the benchmark only once the rules have accuracy data |

## Conclusion

What protects the project from forks is not the prompt or the tell list. Both are already common and can be copied in an afternoon. What protects it is a **rule catalog with IDs, fixtures and precision/recall measurements on a labeled corpus**, plus OOXML adapters that correctly handle quirks that only someone who has run the sandbox knows about, such as `shape[N]` skipping charts or the renderer falling back to sans. The "Claude look" itself switched sides, from taste to tell, within a few months. This shows that anti-tells are not a static list but a **dataset that drifts over time**. ANTI-TELLS.md must therefore be versioned, per-pack, and extended through each iteration, exactly as the Opus 5.5 guide advises ("extend the avoidance list as needed").

For the same reason, "Slide Bench" (whatever it ends up being called) should promise only what the linter measures reliably: compliance with a declared design system and layout hygiene, with a content gate against Goodhart. It should not promise to measure "beauty". The "as beautiful as possible" part is still decided by humans and pairwise judges. The job of deck-lint is to make everything that is *not beautiful for known reasons* impossible to ship.

## Sources

**Prior art and market**
- https://github.com/anthropics/skills
- https://raw.githubusercontent.com/anthropics/skills/main/skills/pptx/SKILL.md
- https://github.com/anthropics/skills/blob/main/skills/pptx/SKILL.md
- https://github.com/anthropics/skills/issues/531
- https://github.com/iOfficeAI/OfficeCLI
- https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/skills/officecli-pptx/SKILL.md
- https://github.com/hugohe3/ppt-master
- https://github.com/zarazhangrui/frontend-slides
- https://raw.githubusercontent.com/EveryInc/hands-on-deck/main/README.md
- https://raw.githubusercontent.com/SlideSpeak/slide-design-skill/main/README.md
- https://raw.githubusercontent.com/ItsssssJack/power-design/main/README.md
- https://raw.githubusercontent.com/BDBDDSCAT/pptx-qc/master/README.md
- https://raw.githubusercontent.com/heroak2008/ppt-linter/main/README.md
- https://raw.githubusercontent.com/nibzard/slidegauge/main/README.md
- https://raw.githubusercontent.com/ToseaAI/awesome-html-slide-skills/main/README.md
- https://raw.githubusercontent.com/ningzimu/awesome-ai-ppt/main/README.md
- https://2slides.com/blog/best-ppt-skills-claude-code-codex-2026
- https://news.ycombinator.com/item?id=46998194
- https://www.serverman.co.uk/ai/claude/claude-docs-and-slides-what-they-can-and-cant-do/
- https://www.remio.ai/post/claude-slides-launch-brings-editable-decks-into-every-conversation
- https://www.beautiful.ai/blog/ai-can-build-slides-fast--but-great-presentations-still-need-design-rules
- https://moda.app/blog/gamma-ai-presentation

**Benchmarks and evaluation**
- https://arxiv.org/html/2501.00912v1
- https://github.com/para-lost/AutoPresent
- https://arxiv.org/html/2501.03936v3
- https://arxiv.org/html/2603.07244v1
- https://github.com/YunqiaoYang/SlidesGen-Bench
- https://lacuna.tiptreesystems.com/work/slidesgen-bench-evaluating-slides-generation-via-computational-and-quantitative/wrk_90ee3a8643a27771eb4d8c52917916ce
- https://arxiv.org/html/2512.03042v3
- https://arxiv.org/html/2512.02624v1
- https://arxiv.org/html/2508.03630v1
- https://arxiv.org/html/2602.13318
- https://notes.designarena.ai/methodology/
- https://arxiv.org/html/2604.25235v1
- https://arxiv.org/html/2603.01083v1
- https://arxiv.org/html/2404.00995v3
- https://arxiv.org/html/2508.11177v2
- https://lintbench.ai/
- https://www.slidebench.org/
- https://openaccess.thecvf.com/content/CVPR2025/papers/Chen_SlideChat_A_Large_Vision-Language_Assistant_for_Whole-Slide_Pathology_Image_Understanding_CVPR_2025_paper.pdf
- https://github.com/bunchc/deck-lint
- https://github.com/enkidulan/slidelint
- https://www.jotform.com/form-templates/presentation-evaluation-form

**The Opus 5 / 5.5 artistic trend**
- https://raw.githubusercontent.com/JohnHeibel/PDoomVideo/main/README.md
- https://raw.githubusercontent.com/JohnHeibel/PDoomVideo/main/ANIMATION_GUIDE.md
- https://raw.githubusercontent.com/JohnHeibel/ClaudeAnimationBase/main/README.md
- https://raw.githubusercontent.com/JohnHeibel/ClaudeAnimationBase/main/ANIMATION_GUIDE.md
- https://raw.githubusercontent.com/IshaanKalra2103/riso-rooms/main/skills/riso-rooms/SKILL.md
- https://raw.githubusercontent.com/IshaanKalra2103/creative-skills/main/skills/slide-craft/SKILL.md
- https://x.com/kevin_t_ngo/status/2100238648218427563
- https://raw.githubusercontent.com/theolundqvist/frontier-games/main/README.md
- https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5
- https://raw.githubusercontent.com/anthropics/skills/main/skills/frontend-design/SKILL.md
- https://www.theneuron.ai/digest/everything-that-happened-in-ai-today-tuesday-september-22-2026/
- https://www.theneuron.ai/digest/everything-that-happened-in-ai-today-wednesday-september-23-2026/
- https://orcarouter.ai/blog/claude-opus-5-5-video-plan-one-shot

**Technical limits of .pptx**
- https://www.rdpslides.com/pptfaq/FAQ00076_Embedding_fonts.htm
- https://learn.microsoft.com/en-us/answers/questions/5012732/limitations-and-issues-when-embedding-fonts-in-pow
- https://learn.microsoft.com/en-us/answers/questions/5619322/font-not-displaying-on-powerpoint-online
- https://learn.microsoft.com/en-us/answers/questions/2120886/embedded-fonts-dont-work-on-windows-powerpoint-aft
- https://www.moonleo.com/presentation-font-embedder-for-mac/frequently-asked-questions/
- https://www.apple.com/keynote/compatibility/
- https://www.brightcarbon.com/blog/convert-powerpoint-google-slides/
- https://www.collaboraonline.com/blog/collabora-productivity-contributions-in-libreoffice-25-8/
- https://github.com/4thel00z/pptxboss/pull/14
- https://github.com/jgm/pandoc/issues/11492
- https://support.neuxpower.com/hc/en-us/articles/360007786978-Embed-subset-or-remove-embedded-fonts-in-PowerPoint-or-Word
- https://github.com/atharva9167j/dom-to-pptx
- https://github.com/marp-team/marp-cli/issues/725
- https://sli.dev/guide/exporting.html

**impeccable internals** (pinned to commit e0881d2)
- https://github.com/pbakaus/impeccable
- https://raw.githubusercontent.com/pbakaus/impeccable/main/README.md
- https://github.com/pbakaus/impeccable/blob/e0881d2/skill/SKILL.src.md
- https://github.com/pbakaus/impeccable/blob/e0881d2/docs/ENGINE.md
- https://github.com/pbakaus/impeccable/blob/e0881d2/docs/CLI-CONTRACT.md
- https://github.com/pbakaus/impeccable/blob/e0881d2/crates/foundation/src/registry.rs
- https://github.com/pbakaus/impeccable/blob/e0881d2/skill/reference/new-work.md
- https://github.com/pbakaus/impeccable/blob/e0881d2/skill/reference/craft-floor.md
- https://github.com/pbakaus/impeccable/blob/e0881d2/skill/reference/document.md
- https://github.com/pbakaus/impeccable/blob/e0881d2/skill/reference/init.md
- https://github.com/pbakaus/impeccable/blob/e0881d2/skill/reference/hooks.md
- https://github.com/pbakaus/impeccable/blob/e0881d2/skill/reference/bolder.md
- https://github.com/pbakaus/impeccable/blob/e0881d2/skill/agents/impeccable-finish-reviewer.md
- https://github.com/pbakaus/impeccable/blob/e0881d2/.claude/settings.json
- https://github.com/pbakaus/impeccable/blob/e0881d2/crates/hook/src/stop_baseline.rs
- https://github.com/pbakaus/impeccable/commit/9ffd3211

**Design canon, style families and AI tells**
- https://cpb-us-e1.wpmucdn.com/sites.psu.edu/dist/7/13153/files/2008/10/Assertion-Evidence-Slides-Instruction_Set.pdf
- https://peer.asee.org/assertion-evidence-slides-appear-to-lead-to-better-comprehension-and-recall-of-more-complex-concepts.pdf
- https://www.fceia.unr.edu.ar/~mcristia/tufte-powerpoint.pdf
- https://www.garrreynolds.com/design-tips
- https://www.duarte.com/resources/guides-tools/the-glance-test/
- https://www.lucapallotta.com/slidedocs/
- https://deckary.com/blog/consulting-slide-standards
- https://slideworks.io/resources/how-mckinsey-consultants-make-presentations
- https://guykawasaki.com/the_102030_rule/
- https://opentextbc.ca/graphicdesign/chapter/1-6-its/
- https://medium.com/data-science/making-economist-style-plots-in-matplotlib-e7de6d679739
- https://gist.github.com/selcukcihan/b9418596a98abfcd4bbc622550820cc5
- https://medium.com/design-bootcamp/a-designers-teardown-of-ai-slides-and-the-fixes-that-actually-move-them-7149203ed6ce
- https://2slides.com/blog/why-ai-slides-look-fake-and-how-to-fix
- https://designwithjack.dev/
- https://kylechayka.substack.com/p/the-generic-style-of-ai-web-design
- https://pxlnv.com/linklog/claude-aesthetic/
- https://x.com/chaykak/status/2069787733648723979
- https://plusai.com/blog/how-to-make-ai-slides-that-dont-look-like-ai-slop/
- https://github.com/rohitg00/awesome-claude-design
- https://slidespeak.co/slide-design-prompts/prompts/keynote-minimal
- https://slidespeak.co/slide-design-prompts/prompts/economist-style
- https://freedesignmd.com/lexicon/risograph
- https://dev.to/decksmith/seven-signs-a-slide-deck-was-made-by-ai-1828
- https://www.chatslide.ai/guides/how-to-make-ai-slides-not-look-ai-generated
- https://www.theadpharm.com/insights/claude-design-without-the-ai-slop-look
- https://www.pangram.com/signs-of-ai-writing
- https://worldcomgroup.com/insights/how-to-spot-ai-writing-tips-from-wikipedia-on/
- https://practicaltypography.com/letterspacing.html
- https://practicaltypography.com/alternate-figures.html
- https://learn.microsoft.com/en-us/answers/questions/5217674/is-there-any-way-to-access-stylistic-alternates-or
- https://www.whitepage.studio/blog/presentation-font-sizes
