# keyline stress test: notes

- **Target:** `/home/claude/kl`, branch `001-lint-core` at `589d693` ("docs: report for spec 001 (T-25)"). Nothing inside the repo was modified.
- **Claim under test:** constitution III: `keyline lint` works on any .pptx, whatever made it, and never crashes. Exit contract: 0 clean, 2 findings, 1 "cannot scan" with a one-line reason; any other code, or a traceback, is a crash.
- **Rules read first:** `keyline rules --json` lists 13 ids: the 11 rules plus the two adapter advisories (`adapter-unresolved`, `unsupported-content`). Spec sections 5 and 6 and amendments A-1 to A-10 were read before building decks. The project's tests and fixtures were **not** read.
- **Tools:** pptxgenjs 4.0.1, python-pptx 1.0.2, LibreOffice 24.2.7.2 (via `soffice.py`), OfficeCLI 1.0.152, lxml 6.1.3 / libxml2 2.14.6, Python 3.11.15. Machine: 2 vCPU Xeon @ 2.80 GHz.
- **Reproduce:** `bash src/build_all.sh` rebuilds every deck and reruns every check (about 2.5 min). A full rebuild reproduced identical findings for all 25 main decks.
- **Housekeeping:** `/home/claude/stress` already held files from an earlier, interrupted attempt (last write 00:59, before this session started). I moved them untouched into `prior_run/` so that `src/` and `decks/` contain only this run. I reused none of their conclusions. After my own corpus was done, I ran keyline over their decks as a crash sweep only; it pointed at int-parsing crashes, which I then reproduced with my own files (o51 to o56).
- **Verdicts:** TRUE = the finding is correct under the rule definition. FALSE-POSITIVE = the finding claims a defect that the rendered slide does not have (checked with `officecli view … screenshot` and, where the renderers could disagree, a LibreOffice PDF render). DEBATABLE = correct by the letter of the rule, but arguably not a defect, or the rule's scope is unclear. Renders are in `png/`.

## 1. Summary

**Counts**

- **Decks:** 25 hand-designed decks (d01 to d27; d22 and d24 are the perf and oddity sets) from 5 generators: pptxgenjs, python-pptx, LibreOffice, OfficeCLI, and raw XML/zip surgery on python-pptx output. There are also 105 derived stress files: 37 malformed or unusual package files, 60 schema-oddity variants, and 8 performance decks. On top of those, a directory path and a non-existent path were passed. That is 130 files in total.
- **Crashes (tracebacks):** 4 distinct defects, reproduced in 7 files:
  - C-1: `--json` output-encoding crash (lint and check);
  - C-2: a percent-string or float value in a color transform;
  - C-3: a non-integer connector id;
  - C-4: a 40-digit length.

  None of the 25 main decks crashes under a UTF-8 stdout. d25 crashes under a cp1252 stdout.
- **False positives:** 6 findings, confirmed by render, from 5 root causes. There are also 1,000 and 9,000 repeat instances of FP-1 in the perf decks.
- **False negatives:** 6. Two of them (FN-5, FN-6) are acknowledged in-tool by the `unsupported-content` advisory "table text is not read in M1". Another 6 debatable gaps are listed but not counted.
- **Refusals of valid packages (exit 1, not crashes):**
  - a Strict-conformance .pptx (d27), with a misleading reason;
  - a deck with more than 512 MB of embedded media (v09);
  - case-mismatched and percent-encoded part names (v04 and v05; debatable);
  - `sldSz` absent (o12; schema-optional);
  - 300-deep group nesting (o20; libxml2 depth limit, unrealistic).
- **Performance:** every realistic deck lints in 0.11 to 0.26 s, and the 60-slide deck takes 0.21 s. The 1 s budget is exceeded at about 1,000 shapes on one slide (1.52 s) and on 60 slides × 150 shapes (5.87 s), because box-overlap is O(n²) and uses `Fraction`.
- **Determinism:** byte-identical JSON and stderr across 3 runs, 3 fixed `PYTHONHASHSEED`s and both modes, on 5 decks from 4 generators.

**Main decks (presented-mode findings; exit shown for both modes)**

| Deck | Generator | Exit (presented / read) | Findings E/W/A | TRUE | FP | DEBATABLE | Crash |
|---|---|---|---|---|---|---|---|
| d01_pgx_basic | pptxgenjs 4.0.1 | 2 / 2 | 0/6/1 | 7 | 0 | 0 | no |
| d02_ppx_layouts | python-pptx 1.0.2 | 2 / 2 | 0/19/0 | 17 | 0 | 2 | no |
| d03_ppx_misc | python-pptx 1.0.2 | 2 / 2 | 1/18/8 | 27 | 0 | 0 | no |
| d04_lo_from_ppx | LibreOffice 24.2 (round-trip of d02) | 2 / 2 | 0/19/0 | 17 | 0 | 2 | no |
| d05_lo_from_pgx | LibreOffice 24.2 (round-trip of d01) | 2 / 2 | 0/6/1 | 7 | 0 | 0 | no |
| d06_oc_deck | OfficeCLI 1.0.152 | 2 / 2 | 0/5/17 | 22 | 0 | 0 | no |
| d07_pgx_60slides | pptxgenjs | 2 / 0 | 0/24/10 | 34 | 0 | 0 | no |
| d08_pgx_4x3 | pptxgenjs | 2 / 2 | 1/2/0 | 3 | 0 | 0 | no |
| d09_ppx_portrait | python-pptx | 2 / 2 | 0/2/0 | 2 | 0 | 0 | no |
| d10_ppx_nomasterbg | python-pptx + lxml | 2 / 2 | 0/3/2 | 5 | 0 | 0 | no |
| d11_oc_vietnamese | OfficeCLI | 2 / 2 | 0/4/3 | 7 | 0 | 0 | no |
| d12_ppx_empty_slides | python-pptx | 2 / 2 | 0/5/0 | 1 | 0 | 4 | no |
| d13_ppx_zero_slides | python-pptx | 0 / 0 | 0/0/0 | 0 | 0 | 0 | no |
| d14_oc_implicit_font | OfficeCLI | 0 / 0 | 0/0/4 | 4 | 0 | 0 | no |
| d15_ppx_style_fontref | python-pptx | 2 / 2 | 0/4/0 | 3 | 1 | 0 | no |
| d16_raw_color | python-pptx + lxml | 2 / 2 | 0/9/6 | 13 | 2 | 0 | no |
| d17_raw_geometry | python-pptx + raw XML | 2 / 2 | 4/8/4 | 11 | 2 | 3 | no |
| d18_lo_autofit | python-pptx -> LibreOffice | 2 / 2 | 0/2/0 | 1 | 1 | 0 | no |
| d19_raw_notes | python-pptx + raw XML | 2 / 2 | 0/9/0 | 7 | 0 | 2 | no |
| d20_pgx_slop | pptxgenjs | 2 / 2 | 0/9/3 | 9 | 0 | 3 | no |
| d21_raw_two_masters | python-pptx + zip surgery | 2 / 2 | 0/6/0 | 6 | 0 | 0 | no |
| d23_pgx_cjk_thai | pptxgenjs | 2 / 2 | 0/1/0 | 1 | 0 | 0 | no |
| d25_ppx_localized_names | python-pptx | 2 / 2 | 0/8/0 | 8 | 0 | 0 | no |
| d26_oc_default_text | OfficeCLI | 2 / 2 | 0/2/5 | 7 | 0 | 0 | no |
| d27_strict_from_ppx | d02 converted to ISO/IEC 29500 Strict | 1 / 1 | 0/0/0 | 0 | 0 | 0 | no |
| **total** | | | 241 findings | 219 | 6 | 16 | |

**Stress corpora**

| Corpus | Files | Result |
|---|---|---|
| Malformed, required (m01 to m07, plus m03b as a second broken-relationship case) | 8 paths (6 files, a directory, a missing path) | All exit 1 with one line, no traceback (section 7.2) |
| Malformed or unusual, extra (x01 to x22, v01 to v09) | 31 | No traceback. Valid packages v01, v02, v03, v06, v07, v08 lint normally. v04, v05, v09 refused (section 7.2) |
| Schema oddities (o01 to o60) | 60 | 6 tracebacks (o51 to o56): crashes C-2, C-3, C-4. Others exit 1 or 2 cleanly (section 7.3) |
| Performance (perf_*) | 8 | No traceback. 4 decks exceed 1 s: perf_1000, perf_1000_overlap, perf_2000, perf_150_x60 (section 5) |
| Output encoding (d25 and d01 under 4 stdout encodings) | 16 runs + 2 | `--json` crashes (C-1) whenever stdout cannot encode a character in the output |

## 2. Crashes (full tracebacks)

### C-1 · `lint --json` / `check --json` crash when stdout is not UTF-8 (UnicodeEncodeError)

`findings.to_json` uses `json.dumps(..., ensure_ascii=False)`, and `cli._out` writes it with `sys.stdout.write`. On Windows, Python 3.10 to 3.14 encode a redirected or piped stdout in the ANSI code page (cp1252 on Western systems) unless `PYTHONUTF8=1` is set. That is the normal way a tool or skill captures `--json`. There is no Windows machine here, so I simulated this with `PYTHONIOENCODING=cp1252`, which sets the same stdout codec. Any shape name or font name outside that code page then crashes the run before one byte is written. Localized PowerPoint names shapes in the UI language ("Tiêu đề 1", "タイトル 1"), so a deck authored in Japan and linted on a US Windows machine is enough to trigger it. stderr survives because Python uses `backslashreplace` there.

Repro: `PYTHONIOENCODING=cp1252 keyline lint decks/d25_ppx_localized_names.pptx --json > out.json` gives exit 1, 0 bytes of JSON, and this traceback:

```
Traceback (most recent call last):
  File "/home/claude/kl/.venv/bin/keyline", line 8, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/claude/kl/src/keyline/cli.py", line 151, in main
    return args.func(args)
           ^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/cli.py", line 45, in cmd_lint
    _out(to_json(result.findings))
  File "/home/claude/kl/src/keyline/cli.py", line 26, in _out
    sys.stdout.write(text)
  File "/usr/lib/python3.11/encodings/cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'charmap' codec can't encode characters in position 146-147: character maps to <undefined>
```

Matrix (`src/encoding_check.sh`):

```
d25_ppx_localized_names.pptx         utf-8    lint        exit=2 traceback=0 bytes_out=0
d25_ppx_localized_names.pptx         utf-8    lint --json exit=2 traceback=0 bytes_out=2235
d25_ppx_localized_names.pptx         cp1252   lint        exit=2 traceback=0 bytes_out=0
d25_ppx_localized_names.pptx         cp1252   lint --json exit=1 traceback=1 bytes_out=0
d25_ppx_localized_names.pptx         latin-1  lint        exit=2 traceback=0 bytes_out=0
d25_ppx_localized_names.pptx         latin-1  lint --json exit=1 traceback=1 bytes_out=0
d25_ppx_localized_names.pptx         ascii    lint        exit=2 traceback=0 bytes_out=0
d25_ppx_localized_names.pptx         ascii    lint --json exit=1 traceback=1 bytes_out=0
d01_pgx_basic.pptx                   utf-8    lint        exit=2 traceback=0 bytes_out=0
d01_pgx_basic.pptx                   utf-8    lint --json exit=2 traceback=0 bytes_out=1890
d01_pgx_basic.pptx                   cp1252   lint        exit=2 traceback=0 bytes_out=0
d01_pgx_basic.pptx                   cp1252   lint --json exit=2 traceback=0 bytes_out=1887
d01_pgx_basic.pptx                   latin-1  lint        exit=2 traceback=0 bytes_out=0
d01_pgx_basic.pptx                   latin-1  lint --json exit=2 traceback=0 bytes_out=1887
d01_pgx_basic.pptx                   ascii    lint        exit=2 traceback=0 bytes_out=0
d01_pgx_basic.pptx                   ascii    lint --json exit=1 traceback=1 bytes_out=0
rules --json cp1252 exit=0 traceback=0
rules --json ascii exit=1 traceback=1
```

`check --json` fails the same way (exit 1, traceback). With an `ascii` stdout, even ASCII-named decks crash, because messages contain `×` and `·`, and so does `keyline rules --json` (`§`).

### C-2 · Color transform value that is not a plain integer (ValueError in `color._pct`)

`_pct` does `int(el.get("val"))`. ISO/IEC 29500 **Strict** writes these percentages as `"75%"`, and some generators write floats (`"25000.0"`). Both crash in the text-color path (o51, o52, o54) and in the background path (o53, `a:tint val="95%"` in the master `p:bgPr`). PowerPoint would ask to repair a transitional file with such values, so realism is moderate. It is still a traceback.

Repro: `keyline lint decks/odd/o51_lummod_percent_string.pptx`

```
Traceback (most recent call last):
  File "/home/claude/kl/.venv/bin/keyline", line 8, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/claude/kl/src/keyline/cli.py", line 151, in main
    return args.func(args)
           ^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/cli.py", line 40, in cmd_lint
    result = _lint(args.deck, args.mode)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/cli.py", line 35, in _lint
    return lint_path(path, mode)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/lint.py", line 34, in lint_path
    deck, diags = load_deck(path)
                  ^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/ooxml/adapter.py", line 319, in load_deck
    return build_deck(pkg)
           ^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/ooxml/adapter.py", line 377, in build_deck
    slide.shapes.append(_build_shape(el, groups, gfill, ctx))
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/ooxml/adapter.py", line 285, in _build_shape
    shape.paragraphs = paragraphs(el.find("p:txBody", NS), src)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/ooxml/text.py", line 194, in paragraphs
    runs.append(_run(text, child.find("a:rPr", NS), level, src))
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/ooxml/text.py", line 160, in _run
    color, hidden = _color(chain, src)
                    ^^^^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/ooxml/text.py", line 129, in _color
    r = resolve(find_color(child), src.color_ctx)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/ooxml/color.py", line 139, in resolve
    lum = lum * _pct(t) if name == "lumMod" else lum + _pct(t)
                ^^^^^^^
  File "/home/claude/kl/src/keyline/ooxml/color.py", line 98, in _pct
    return int(el.get("val", "0")) / 100000
           ^^^^^^^^^^^^^^^^^^^^^^^
ValueError: invalid literal for int() with base 10: '75%'
```

o53 (background path):

```
Traceback (most recent call last):
  File "/home/claude/kl/.venv/bin/keyline", line 8, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/claude/kl/src/keyline/cli.py", line 151, in main
    return args.func(args)
           ^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/cli.py", line 40, in cmd_lint
    result = _lint(args.deck, args.mode)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/cli.py", line 35, in _lint
    return lint_path(path, mode)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/lint.py", line 34, in lint_path
    deck, diags = load_deck(path)
                  ^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/ooxml/adapter.py", line 319, in load_deck
    return build_deck(pkg)
           ^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/ooxml/adapter.py", line 364, in build_deck
    bg = background([slide_root, layout_root, master.root], master.theme, color)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/ooxml/fill.py", line 106, in background
    r = _from_fill_element(child, ctx, "none")
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/ooxml/fill.py", line 43, in _from_fill_element
    r = resolve(find_color(el), ctx)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/ooxml/color.py", line 142, in resolve
    v = _pct(t)
        ^^^^^^^
  File "/home/claude/kl/src/keyline/ooxml/color.py", line 98, in _pct
    return int(el.get("val", "0")) / 100000
           ^^^^^^^^^^^^^^^^^^^^^^^
ValueError: invalid literal for int() with base 10: '95%'
```

o54 (float) fails at the same line: `ValueError: invalid literal for int() with base 10: '25000.0'`. o52 (`a:alpha val="50%"`) fails with `'50%'`.

### C-3 · Non-integer connector id (ValueError in `adapter._build_shape`)

Repro: `keyline lint decks/odd/o55_cxn_id_word.pptx` (`<a:stCxn id="first" …/>`)

```
Traceback (most recent call last):
  File "/home/claude/kl/.venv/bin/keyline", line 8, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/claude/kl/src/keyline/cli.py", line 151, in main
    return args.func(args)
           ^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/cli.py", line 40, in cmd_lint
    result = _lint(args.deck, args.mode)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/cli.py", line 35, in _lint
    return lint_path(path, mode)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/lint.py", line 34, in lint_path
    deck, diags = load_deck(path)
                  ^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/ooxml/adapter.py", line 319, in load_deck
    return build_deck(pkg)
           ^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/ooxml/adapter.py", line 377, in build_deck
    slide.shapes.append(_build_shape(el, groups, gfill, ctx))
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/ooxml/adapter.py", line 269, in _build_shape
    shape.st_cxn = int(st.get("id")) if st is not None and st.get("id") else None
                   ^^^^^^^^^^^^^^^^^
ValueError: invalid literal for int() with base 10: 'first'
```

### C-4 · Extreme length breaks message formatting (decimal.InvalidOperation in `units._quantize`)

Repro: `keyline lint decks/odd/o56_ext_40_digits.pptx` (a text box with `a:ext cx` of 40 digits). The shape is correctly found off-slide, but formatting the message overflows the `Decimal` context:

```
Traceback (most recent call last):
  File "/home/claude/kl/.venv/bin/keyline", line 8, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/claude/kl/src/keyline/cli.py", line 151, in main
    return args.func(args)
           ^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/cli.py", line 40, in cmd_lint
    result = _lint(args.deck, args.mode)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/cli.py", line 35, in _lint
    return lint_path(path, mode)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/lint.py", line 35, in lint_path
    findings = lint_deck(deck, diags, cfg)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/lint.py", line 27, in lint_deck
    out.extend(spec.check(deck, cfg))
  File "/home/claude/kl/src/keyline/rules/off_slide.py", line 47, in check
    msg = f"runs {fmt_cm(amount)} cm past the {side} edge"
                  ^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/units.py", line 69, in fmt_cm
    return f"{_quantize(emu_to_cm(emu), 2)}"
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/claude/kl/src/keyline/units.py", line 54, in _quantize
    return d.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
decimal.InvalidOperation: [<class 'decimal.InvalidOperation'>]
```

Garbage input, low realism. 2^63 (o10) and a 25-digit rotated width (o57) do **not** crash.

## 3. False positives

All six are confirmed by render. "Spec-level" means the implementation follows the spec text and the spec itself leads to the wrong answer.

**FP-1 · text-contrast: `p:style/a:fontRef` color loses to the master `otherStyle`** (d15 slide 2; also 1,000 and 9,000 repeats in `perf_1000` and `perf_150_x60`)

- python-pptx `add_shape()` writes `<p:style>…<a:fontRef idx="minor"><a:schemeClr val="lt1"/></a:fontRef></p:style>`. PowerPoint's own Insert › Shape default style carries the same `fontRef … lt1`; that comes from my knowledge of PowerPoint's output and could not be checked here, since there is no PowerPoint on this machine. The user sets `<a:solidFill><a:srgbClr val="1F3864"/>` and no run color.
- The text renders **white** on navy in both renderers (`png/d15_s2.png`, `png/d15_lo_s2_s3.png`); white on 1F3864 is 11.62:1.
- keyline reports `000000 on 1F3864 (Rectangle 2) is 1.81:1`. `ooxml/text.py` consults `fontRef` only after the whole A-4 cascade, and the master `otherStyle` lvl1 already supplies `<a:schemeClr val="tx1"/>`. In PowerPoint the shape style's font color overrides the master text styles.
- A-4 does not mention `fontRef` at all, so this is both a spec gap and an implementation issue. The mirror image is FN-1. Every python-pptx or PowerPoint autoshape whose fill the user changed is affected.

**FP-2 · text-contrast ignores shapes on the layout (spec-level)** (d16 slide 4)

- The "Title Only" layout carries a non-placeholder navy panel (`<p:cNvPr id="90" name="Navy panel"/>`, `a:off 0,0`, `a:ext 5486400 x 6858000`, fill 14213D). Its title placeholder, which is inside the panel, has a white `lstStyle`.
- The slide's title renders white on navy (`png/d16_s4_s6.png`, left); that is 15.97:1.
- keyline: `FFFFFF on FFFFFF (slide background) is 1:1 at 40 pt`. The spec's "effective background" looks only at slide shapes and then the slide/layout/master **background**. Layout and master decoration is common in corporate templates. The same gap gives the inverse false negative (dark text on a layout panel).

**FP-3 · text-contrast containment near-miss (spec-level)** (d16 slide 6)

- A navy card at `a:off 914400,2286000` with `a:ext 10332720 x 3200400` sits under a white text box at `a:off 822960,2194560` with `a:ext 10515600 x 3383280`. The text box is 0.1 in larger on every side.
- The text renders on the card (`png/d16_s4_s6.png`, right); white on 1F3864 is 11.62:1.
- keyline: `FFFFFF on FFFFFF (slide background) is 1:1`. The spec's rule, "the topmost filled shape beneath the run **whose box fully contains the run's shape**", falls through to the slide background. pptxgenjs and AI-generated decks often size text boxes independently of their cards.

**FP-4 and FP-5 · off-slide and text-contrast on hidden shapes** (d17 slide 4)

- `<p:cNvPr … name="Parked note" hidden="1"/>` at x = -9 cm draws `off-slide · error · runs 9.00 cm past the left edge`.
- `<p:cNvPr … name="Hidden white" hidden="1"/>` draws `text-contrast · warning · FFFFFF on FFFFFF`.
- LibreOffice (and PowerPoint, via the Selection Pane's visibility flag) does not draw hidden shapes (`png/d17_s4_oc_vs_lo.png`, right). Note that OfficeCLI's renderer, which `keyline render` uses, **does** draw them (left).
- The adapter never reads `cNvPr/@hidden`. The same cause produces FN-2.

**FP-6 · title-not-dominant under autofit shrink** (d18 slide 2)

- LibreOffice itself wrote `<a:normAutofit fontScale="28122"/>` on the 20-line body. The body renders at 32 × 0.281 ≈ **9.0 pt** in both renderers (`png/d18_s2_oc_vs_lo.png`), so the title is 44 / 9 ≈ 4.9× the body.
- keyline: `title 44 pt is 1.38× the largest body text (32 pt); needs 2×`. `normAutofit/@fontScale` is ignored. The same cause produces FN-3.

## 4. False negatives

These are judged against the rule definitions only.

| # | Rule | Deck / slide | What is on the slide | keyline |
|---|---|---|---|---|
| FN-1 | text-contrast | d15 s3 | Text renders white (fontRef lt1) on FFF2CC: **1.12:1** (`png/d15_s3.png`, `png/d15_lo_s2_s3.png`) | nothing (computes black on FFF2CC) |
| FN-2 | dead-band | d17 s4 | Visible content ends at 8.0 cm; 8.0 to 19.05 cm (58%) is empty on screen (`png/d17_s4_oc_vs_lo.png`, right) | nothing: the `hidden="1"` box at 11 to 17.5 cm counts as content |
| FN-3 | body-too-small | d18 s2 | 20 bullet paragraphs of 7 to 12 words at ≈9.0 pt (fontScale 28.1%), below 18 pt presented and 11 pt read | nothing, in both modes (reads 32 pt) |
| FN-4 | off-slide (error) | d20 s6 | A table with text runs **5.00 cm** past the right edge; its last column is cut (`png/d20_s6.png`) | `off-slide · advisory · … (non-text shape: possible bleed)`. On its own this slide would exit 0 |
| FN-5 | font-count | d03 s3 | Table cells in Comic Sans MS and Courier New plus Calibri: 3 families on screen (`png/d03_s3.png`) | nothing; only the advisory "table text is not read in M1" |
| FN-6 | text-contrast | d03 s3 | Row 4 text DDDDDD on the table style's band DCE6F2 (sampled from the render): **1.08:1** | nothing; same advisory |

Debatable, not counted:

- The d20 s6 chart runs 2.54 cm off the bottom with its category labels cut, but gets only an advisory; a chart may be "non-text".
- d14: three families on screen (Georgia, Verdana, and Calibri via the theme fallback), but the implicit font is "unresolved" under A-4, so font-count sees 2.
- d23: 10 to 12 pt Japanese, Chinese and Thai paragraphs never count as body. A-7 counts whitespace-separated words, so every CJK or Thai paragraph is "1 to 2 words". Text rules are silently blind for these scripts.
- d16 s5 and s7: alpha colors are skipped with an advisory, as the spec requires. White on a 15% black overlay really is 1.41:1.
- d17 s6: `fontScale` 55% on text that actually fits. LibreOffice recomputes it, so the case is contrived; d18 is the realistic version.
- d17 s5: the `mc:Choice` text of an equation box is not read (advisory). No defect was hidden in my deck.

Not false negatives by definition: a title "underline" drawn as a 3 pt line (d20 s7), because the rule requires a *filled* shape.

## 5. Performance

Wall time for the whole CLI process (`src/timeit.py`, including interpreter start of about 0.1 s):

```
decks/d07_pgx_60slides.pptx: exit=2 min=0.203s median=0.211s max=0.216s (n=5)
decks/d01_pgx_basic.pptx: exit=2 min=0.124s median=0.128s max=0.131s (n=5)
decks/perf/perf_100.pptx: exit=2 min=0.161s median=0.161s max=0.211s (n=3)
decks/perf/perf_250.pptx: exit=2 min=0.272s median=0.274s max=0.278s (n=3)
decks/perf/perf_500.pptx: exit=2 min=0.558s median=0.583s max=0.689s (n=3)
decks/perf/perf_1000.pptx: exit=2 min=1.512s median=1.519s max=1.605s (n=3)
decks/perf/perf_2000.pptx: exit=2 min=4.673s median=4.872s max=4.960s (n=3)
decks/perf/perf_500_overlap.pptx: exit=2 min=0.660s median=0.672s max=0.674s (n=3)
decks/perf/perf_1000_overlap.pptx: exit=2 min=1.668s median=1.676s max=1.704s (n=3)
decks/perf/perf_150_x60.pptx: exit=2 min=5.642s median=5.869s max=5.883s (n=3)
```

- All 25 main decks: 0.11 to 0.26 s each (`out/run_all.txt`). The 60-slide pptxgenjs deck (d07: charts, tables and photos) takes **0.21 s median**, well under 1 s.
- Scaling with shapes per slide is superlinear: 500 shapes take 0.58 s, 1,000 take 1.52 s, 2,000 take 4.87 s. 60 slides × 150 shapes take 5.87 s.
- A `cProfile` of `perf_2000` (19.6 s under the profiler) puts 15.9 s in `rules/box_overlap.check`: 2,001,000 calls to `geom.overlap`, whose comparisons go through `fractions.Fraction.__lt__` (2.0 M calls, 4.3 s). The rule is O(n²) with Fraction arithmetic.
- A realistic trigger is a data-driven slide (a dot map, a heat grid, a large org chart) or a template with many small shapes on every slide.

## 6. Determinism

`src/determinism.sh` covers d01 (pptxgenjs), d04 (LibreOffice), d06 (OfficeCLI), d17 (raw XML) and perf_1000. For each deck it runs 3 plain `--json` runs, then 3 runs with `PYTHONHASHSEED` = 0, 1, 12345, then 2 `--mode read` runs. Columns: sha256 prefix of stdout JSON, then of stderr.

```
== decks/d01_pgx_basic.pptx
338720c37a070f76 4d0471d2f2bc3e95
338720c37a070f76 4d0471d2f2bc3e95
338720c37a070f76 4d0471d2f2bc3e95
338720c37a070f76 4d0471d2f2bc3e95 (seed=0)
338720c37a070f76 4d0471d2f2bc3e95 (seed=1)
338720c37a070f76 4d0471d2f2bc3e95 (seed=12345)
e9a6839b3635f1f6
e9a6839b3635f1f6
== decks/d04_lo_from_ppx.pptx
bf759aa7244c1ab6 38e9113b793a38d2
bf759aa7244c1ab6 38e9113b793a38d2
bf759aa7244c1ab6 38e9113b793a38d2
bf759aa7244c1ab6 38e9113b793a38d2 (seed=0)
bf759aa7244c1ab6 38e9113b793a38d2 (seed=1)
bf759aa7244c1ab6 38e9113b793a38d2 (seed=12345)
d332775e5bdf43af
d332775e5bdf43af
== decks/d06_oc_deck.pptx
65ec1a67ffa21373 d17344ee7b4d9324
65ec1a67ffa21373 d17344ee7b4d9324
65ec1a67ffa21373 d17344ee7b4d9324
65ec1a67ffa21373 d17344ee7b4d9324 (seed=0)
65ec1a67ffa21373 d17344ee7b4d9324 (seed=1)
65ec1a67ffa21373 d17344ee7b4d9324 (seed=12345)
08a15ee41e437b15
08a15ee41e437b15
== decks/d17_raw_geometry.pptx
f7c44ef15498eb48 755559741ae01e1e
f7c44ef15498eb48 755559741ae01e1e
f7c44ef15498eb48 755559741ae01e1e
f7c44ef15498eb48 755559741ae01e1e (seed=0)
f7c44ef15498eb48 755559741ae01e1e (seed=1)
f7c44ef15498eb48 755559741ae01e1e (seed=12345)
6e6226091f0c5ca8
6e6226091f0c5ca8
== decks/perf/perf_1000.pptx
09e9f27944f1f0f2 82c6d14a07ebd7f6
09e9f27944f1f0f2 82c6d14a07ebd7f6
09e9f27944f1f0f2 82c6d14a07ebd7f6
09e9f27944f1f0f2 82c6d14a07ebd7f6 (seed=0)
09e9f27944f1f0f2 82c6d14a07ebd7f6 (seed=1)
09e9f27944f1f0f2 82c6d14a07ebd7f6 (seed=12345)
09e9f27944f1f0f2
09e9f27944f1f0f2
```

Every column is identical within each deck. Rebuilding every deck from scratch (`build_all.sh`) also reproduced identical findings for all 25 main decks.

## Other observations (not counted above)

- **Strict .pptx refused, with a misleading reason (d27).** PowerPoint can save "Strict Open XML Presentation" (.pptx). keyline follows the officeDocument relationship but then reports `presentation.xml has no valid p:sldSz`, exit 1. LibreOffice opens the same file and renders all 11 slides correctly (`png/d27_lo_2to5.png`). If Strict namespaces were accepted, crash C-2 would follow at once, because Strict percentages are `"NN%"`.
- **512 MB zip-bomb guard counts media (v09).** A deck with a 600 MB embedded video is refused: `uncompressed size 629323583 bytes exceeds the 536870912 limit`. keyline never decompresses media, so the cap could count only the XML parts it parses.
- **Case-insensitive and percent-encoded part names (v04, v05).** OPC part names compare case-insensitively. LibreOffice opens both files (10 PDF pages each). python-pptx (KeyError) and OfficeCLI also fail. Debatable.
- **Directory path (m06)** gives the message `no such file`, which is misleading because the path exists. Exit 1 is correct.
- **Usage errors exit 2** (`--mode bogus`, a missing deck, `--jsonx`). That is argparse's default, and it collides with "2 = findings".
- **`-0.00 cm`** appears in edge-margin messages and as `"measured": -0.0` in the JSON when a shape sits 1 EMU past the edge (d17 s7).
- **A-5 advisory:** one per slide, and `what = background-default` is only in the message text; the fixed JSON keys have no slot for it.
- **Behaviors verified correct** (candidate false positives or crashes that did not happen):
  - `clrMapOvr` (d16 s2 and s3);
  - per-master themes (d21);
  - group composition with scale and **rotation** (d03 s5, d17 s3);
  - single-shape rotation AABB (d17 s2);
  - `fillRef` index (d03 s5, gradient);
  - `a:noFill` hidden text excluded (d03 s10);
  - empty placeholders excluded (d03 s8);
  - notes detection ignores the slide-number field and header placeholders (d19);
  - 4:3 and portrait geometry (d08, d09);
  - NFD Vietnamese word counts (d11);
  - UTF-16 parts, absolute rel targets, a relocated main part, and ppsx/pptm content types (v01 to v08);
  - XXE and billion-laughs rejected (x11 to x13);
  - zero-slide deck (d13).

## 7. Per-deck appendix

Scripts in `src/`:

| Deck(s) | Script |
|---|---|
| d01 | `pgx_basic.js` |
| d02 | `ppx_layouts.py` |
| d03 | `ppx_misc.py` |
| d04, d05 | `lo_roundtrip.sh` |
| d06 | `oc_deck.sh` |
| d07, d08 | `pgx_edge.js` |
| d09, d10, d12, d13 | `ppx_edge.py` |
| d11, d14 | `oc_vietnamese.py` |
| d15 | `ppx_style_text.py` |
| d16 | `raw_color.py` |
| d17 | `raw_geometry.py` |
| d18 | `lo_autofit.py` + `lo_autofit.sh` |
| d19 | `raw_notes.py` |
| d20 | `pgx_slop.js` |
| d21 | `raw_two_masters.py` |
| d23 | `pgx_cjk.js` |
| d25 | `ppx_localized_names.py` |
| d26 | `oc_default_text.sh` |
| d27 | `strict_convert.py` |
| perf set | `perf_shapes.py` |
| oddity set | `raw_oddities.py` |
| malformed set | `malformed.py`, `big_media.py` |
| verdicts | `judgments.py` |
| appendix | `make_appendix.py` |

Raw results are in `out/results.json`.

### 7.1 Main decks

### d01_pgx_basic

- **Generator:** pptxgenjs 4.0.1
- **Contents:** 6 slides 16:9: cover; title + 14 pt bullets (planted); native bar chart; table; photo + caption 0.2 in from the left/bottom edge (planted); three equal accent1 cards with bg1 text (planted), AAAAAA sentence on white (planted), no notes on slide 6 (planted).
- **Exit:** presented 2, read 2; wall 0.145 s; stderr summary: `7 findings: 0 error, 6 warning, 1 advisory`
- **Script:** `src/pgx_basic.js`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| 2 | body-too-small | warning | Text 1 | 14 pt text in a 9-word paragraph (min 18 pt in presented mode) | **TRUE** planted: 14 pt, 9-word paragraph |
| 4 | unsupported-content | advisory | Table 0 | table text is not read in M1 | **TRUE** table text is not read (advisory) |
| 5 | edge-margin | warning | Text 1 | 0.51 cm from the left edge (min 1.27 cm) | **TRUE** planted: caption x = 0.2 in = 0.51 cm (bottom is also 0.51 cm; one edge reported) |
| 6 | equal-card-row | warning | Text 1 | 3 equal cards in a row (9.14 × 7.62 cm, gaps 1.02 cm), each with text | **TRUE** planted: 3 equal accent1 cards, equal 0.4 in gaps |
| 6 | notes-missing | warning |  | content slide has no speaker notes | **TRUE** planted |
| 6 | text-contrast | warning | Text 4 | AAAAAA on FFFFFF (slide background) is 2.32:1 at 20 pt (needs 3:1) | **TRUE** planted: AAAAAA on white = 2.32:1 |
| 6 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 pt vs 20 pt 11-word paragraph = 1.8x |

### d02_ppx_layouts

- **Generator:** python-pptx 1.0.2
- **Contents:** Default 4:3 template, one slide per default layout (all 11), placeholders filled without xfrm, notes everywhere. Nothing planted.
- **Exit:** presented 2, read 2; wall 0.212 s; stderr summary: `19 findings: 0 error, 19 warning, 0 advisory`
- **Script:** `src/ppx_layouts.py`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| 2 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title/body at y = 274638 or 273050 EMU = 0.76 cm < 1.22 cm |
| 2 | title-not-dominant | warning | Title 1 | title 44 pt is 1.38× the largest body text (32 pt); needs 2× | **TRUE** template sizes (44/32, 20/32, 20/14) are below 2x; verified against the layout lstStyle |
| 3 | dead-band | warning |  | 8.07 cm empty top band from 0.00 to 8.07 cm (42% of slide height) | **DEBATABLE** Section Header slide: empty top 42% is the layout's design; M1 treats every slide after 1 as content (documented limitation) |
| 4 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title/body at y = 274638 or 273050 EMU = 0.76 cm < 1.22 cm |
| 5 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title/body at y = 274638 or 273050 EMU = 0.76 cm < 1.22 cm |
| 6 | dead-band | warning |  | 15.11 cm empty bottom band from 3.94 to 19.05 cm (79% of slide height) | **TRUE** Title Only slide: 79% empty below the title |
| 6 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title/body at y = 274638 or 273050 EMU = 0.76 cm < 1.22 cm |
| 7 | dead-band | warning |  | 19.05 cm empty top band from 0.00 to 19.05 cm (100% of slide height) | **DEBATABLE** Blank layout, no shapes: an empty slide, not a content slide with a gap |
| 8 | body-too-small | warning | Text Placeholder 3 | 14 pt text in a 13-word paragraph (min 18 pt in presented mode) | **TRUE** template caption style is 14 pt (layout lstStyle lvl1 sz=1400) |
| 8 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title/body at y = 274638 or 273050 EMU = 0.76 cm < 1.22 cm |
| 8 | edge-margin | warning | Content Placeholder 2 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title/body at y = 274638 or 273050 EMU = 0.76 cm < 1.22 cm |
| 8 | title-not-dominant | warning | Title 1 | title 20 pt is 0.63× the largest body text (32 pt); needs 2× | **TRUE** template sizes (44/32, 20/32, 20/14) are below 2x; verified against the layout lstStyle |
| 9 | body-too-small | warning | Text Placeholder 3 | 14 pt text in a 9-word paragraph (min 18 pt in presented mode) | **TRUE** template caption style is 14 pt (layout lstStyle lvl1 sz=1400) |
| 9 | title-not-dominant | warning | Title 1 | title 20 pt is 1.43× the largest body text (14 pt); needs 2× | **TRUE** template sizes (44/32, 20/32, 20/14) are below 2x; verified against the layout lstStyle |
| 10 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title/body at y = 274638 or 273050 EMU = 0.76 cm < 1.22 cm |
| 10 | title-not-dominant | warning | Title 1 | title 44 pt is 1.38× the largest body text (32 pt); needs 2× | **TRUE** template sizes (44/32, 20/32, 20/14) are below 2x; verified against the layout lstStyle |
| 11 | edge-margin | warning | Vertical Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title/body at y = 274638 or 273050 EMU = 0.76 cm < 1.22 cm |
| 11 | edge-margin | warning | Vertical Text Placeholder 2 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title/body at y = 274638 or 273050 EMU = 0.76 cm < 1.22 cm |
| 11 | title-not-dominant | warning | Vertical Title 1 | title 44 pt is 1.38× the largest body text (32 pt); needs 2× | **TRUE** template sizes (44/32, 20/32, 20/14) are below 2x; verified against the layout lstStyle |

### d03_ppx_misc

- **Generator:** python-pptx 1.0.2
- **Contents:** 4:3, 10 slides: cover; column chart; table (Comic Sans + Courier cells, DDDDDD row); photo with white caption on it; scaled groups (group B child 2 in off-slide); lumMod/lumOff colors (BFBFBF text planted); gradient slide background; empty body placeholder; no-notes slide; a:noFill hidden text.
- **Exit:** presented 2, read 2; wall 0.204 s; stderr summary: `27 findings: 1 error, 18 warning, 8 advisory`
- **Script:** `src/ppx_misc.py`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| 2 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title at 0.76 cm from the top |
| 3 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title at 0.76 cm from the top |
| 3 | unsupported-content | advisory | Table 2 | table text is not read in M1 | **TRUE** advisory; the table hides two defects (see FN-5, FN-6) |
| 4 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title at 0.76 cm from the top |
| 4 | text-contrast | advisory | TextBox 3 | contrast not checked: background is the picture Picture 2 | **TRUE** advisory: white caption over the photo is correctly skipped |
| 5 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title at 0.76 cm from the top |
| 5 | off-slide | error | Rectangle 6 | runs 5.08 cm past the right edge | **TRUE** group B child composes to x 8..12 in on a 10 in slide: 2 in = 5.08 cm |
| 5 | text-contrast | advisory | Rectangle 3 | contrast not checked: background is the gradient fill of Rectangle 3 | **TRUE** advisory: python-pptx writes fillRef idx=3, the theme's gradient fill style |
| 5 | text-contrast | advisory | Rectangle 4 | contrast not checked: background is the gradient fill of Rectangle 4 | **TRUE** advisory: python-pptx writes fillRef idx=3, the theme's gradient fill style |
| 5 | text-contrast | advisory | Rectangle 6 | contrast not checked: background is the gradient fill of Rectangle 6 | **TRUE** advisory: python-pptx writes fillRef idx=3, the theme's gradient fill style |
| 6 | dead-band | warning |  | 5.59 cm empty bottom band from 13.46 to 19.05 cm (29% of slide height) | **TRUE** 13.46..19.05 cm empty (29%) |
| 6 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title at 0.76 cm from the top |
| 6 | text-contrast | warning | TextBox 3 | BFBFBF on FFFFFF (slide background) is 1.84:1 at 24 pt (needs 3:1) | **TRUE** planted: tx1 lumMod 25% lumOff 75% = BFBFBF, 1.84:1 |
| 6 | title-not-dominant | warning | Title 1 | title 44 pt is 1.83× the largest body text (24 pt); needs 2× | **TRUE** 44 pt vs 24/32 pt |
| 7 | adapter-unresolved | advisory |  | background is not a solid fill (background:gradient); background rules skip this slide | **TRUE** gradient background |
| 7 | dead-band | warning |  | 11.43 cm empty bottom band from 7.62 to 19.05 cm (60% of slide height) | **TRUE** 60% empty |
| 7 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title at 0.76 cm from the top |
| 7 | text-contrast | advisory | Title 1 | contrast not checked: background is the slide background (not a solid fill) | **TRUE** advisory: gradient background |
| 7 | text-contrast | advisory | TextBox 2 | contrast not checked: background is the slide background (not a solid fill) | **TRUE** advisory: gradient background |
| 7 | title-not-dominant | warning | Title 1 | title 44 pt is 1.83× the largest body text (24 pt); needs 2× | **TRUE** 44 pt vs 24/32 pt |
| 8 | dead-band | warning |  | 15.11 cm empty bottom band from 3.94 to 19.05 cm (79% of slide height) | **TRUE** the empty body placeholder is invisible in the show, so 79% is empty |
| 8 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title at 0.76 cm from the top |
| 9 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title at 0.76 cm from the top |
| 9 | notes-missing | warning |  | content slide has no speaker notes | **TRUE** planted |
| 9 | title-not-dominant | warning | Title 1 | title 44 pt is 1.38× the largest body text (32 pt); needs 2× | **TRUE** 44 pt vs 24/32 pt |
| 10 | dead-band | warning |  | 9.40 cm empty bottom band from 9.65 to 19.05 cm (49% of slide height) | **TRUE** the a:noFill text box is invisible and correctly not counted |
| 10 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title at 0.76 cm from the top |

### d04_lo_from_ppx

- **Generator:** LibreOffice 24.2 (round-trip of d02)
- **Contents:** d02 re-written by soffice --convert-to pptx.
- **Exit:** presented 2, read 2; wall 0.238 s; stderr summary: `19 findings: 0 error, 19 warning, 0 advisory`
- **Script:** `src/lo_roundtrip.sh`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| 2 | edge-margin | warning | PlaceHolder 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title/body at y = 274638 or 273050 EMU = 0.76 cm < 1.22 cm |
| 2 | title-not-dominant | warning | PlaceHolder 1 | title 44 pt is 1.38× the largest body text (32 pt); needs 2× | **TRUE** template sizes (44/32, 20/32, 20/14) are below 2x; verified against the layout lstStyle |
| 3 | dead-band | warning |  | 8.07 cm empty top band from 0.00 to 8.07 cm (42% of slide height) | **DEBATABLE** Section Header slide: empty top 42% is the layout's design; M1 treats every slide after 1 as content (documented limitation) |
| 4 | edge-margin | warning | PlaceHolder 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title/body at y = 274638 or 273050 EMU = 0.76 cm < 1.22 cm |
| 5 | edge-margin | warning | PlaceHolder 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title/body at y = 274638 or 273050 EMU = 0.76 cm < 1.22 cm |
| 6 | dead-band | warning |  | 15.11 cm empty bottom band from 3.94 to 19.05 cm (79% of slide height) | **TRUE** Title Only slide: 79% empty below the title |
| 6 | edge-margin | warning | PlaceHolder 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title/body at y = 274638 or 273050 EMU = 0.76 cm < 1.22 cm |
| 7 | dead-band | warning |  | 19.05 cm empty top band from 0.00 to 19.05 cm (100% of slide height) | **DEBATABLE** Blank layout, no shapes: an empty slide, not a content slide with a gap |
| 8 | body-too-small | warning | PlaceHolder 3 | 14 pt text in a 13-word paragraph (min 18 pt in presented mode) | **TRUE** template caption style is 14 pt (layout lstStyle lvl1 sz=1400) |
| 8 | edge-margin | warning | PlaceHolder 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title/body at y = 274638 or 273050 EMU = 0.76 cm < 1.22 cm |
| 8 | edge-margin | warning | PlaceHolder 2 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title/body at y = 274638 or 273050 EMU = 0.76 cm < 1.22 cm |
| 8 | title-not-dominant | warning | PlaceHolder 1 | title 20 pt is 0.63× the largest body text (32 pt); needs 2× | **TRUE** template sizes (44/32, 20/32, 20/14) are below 2x; verified against the layout lstStyle |
| 9 | body-too-small | warning | PlaceHolder 2 | 14 pt text in a 9-word paragraph (min 18 pt in presented mode) | **TRUE** template caption style is 14 pt (layout lstStyle lvl1 sz=1400) |
| 9 | title-not-dominant | warning | PlaceHolder 1 | title 20 pt is 1.43× the largest body text (14 pt); needs 2× | **TRUE** template sizes (44/32, 20/32, 20/14) are below 2x; verified against the layout lstStyle |
| 10 | edge-margin | warning | PlaceHolder 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title/body at y = 274638 or 273050 EMU = 0.76 cm < 1.22 cm |
| 10 | title-not-dominant | warning | PlaceHolder 1 | title 44 pt is 1.38× the largest body text (32 pt); needs 2× | **TRUE** template sizes (44/32, 20/32, 20/14) are below 2x; verified against the layout lstStyle |
| 11 | edge-margin | warning | PlaceHolder 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title/body at y = 274638 or 273050 EMU = 0.76 cm < 1.22 cm |
| 11 | edge-margin | warning | PlaceHolder 2 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title/body at y = 274638 or 273050 EMU = 0.76 cm < 1.22 cm |
| 11 | title-not-dominant | warning | PlaceHolder 1 | title 44 pt is 1.38× the largest body text (32 pt); needs 2× | **TRUE** template sizes (44/32, 20/32, 20/14) are below 2x; verified against the layout lstStyle |

### d05_lo_from_pgx

- **Generator:** LibreOffice 24.2 (round-trip of d01)
- **Contents:** d01 re-written by soffice --convert-to pptx.
- **Exit:** presented 2, read 2; wall 0.130 s; stderr summary: `7 findings: 0 error, 6 warning, 1 advisory`
- **Script:** `src/lo_roundtrip.sh`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| 2 | body-too-small | warning | Text 1 | 14 pt text in a 9-word paragraph (min 18 pt in presented mode) | **TRUE** planted: 14 pt, 9-word paragraph |
| 4 | unsupported-content | advisory | Table 0 | table text is not read in M1 | **TRUE** table text is not read (advisory) |
| 5 | edge-margin | warning | Text 1 | 0.51 cm from the left edge (min 1.27 cm) | **TRUE** planted: caption x = 0.2 in = 0.51 cm (bottom is also 0.51 cm; one edge reported) |
| 6 | equal-card-row | warning | Text 1 | 3 equal cards in a row (9.14 × 7.62 cm, gaps 1.02 cm), each with text | **TRUE** planted: 3 equal accent1 cards, equal 0.4 in gaps |
| 6 | notes-missing | warning |  | content slide has no speaker notes | **TRUE** planted |
| 6 | text-contrast | warning | Text 4 | AAAAAA on FFFFFF (slide background) is 2.32:1 at 20 pt (needs 3:1) | **TRUE** planted: AAAAAA on white = 2.32:1 |
| 6 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 pt vs 20 pt 11-word paragraph = 1.8x |

### d06_oc_deck

- **Generator:** OfficeCLI 1.0.152
- **Contents:** 6 slides 16:9: cover; column chart at x = 0.5 cm (A-3); table; 3 equal boxes linked by glued connectors; photo + a circle photo bleeding off the corner; Georgia/Verdana/Courier New + theme-font text.
- **Exit:** presented 2, read 2; wall 0.196 s; stderr summary: `22 findings: 0 error, 5 warning, 17 advisory`
- **Script:** `src/oc_deck.sh`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| deck | font-count | warning |  | 3 font families: Courier New, Georgia, Verdana (max 2) | **TRUE** Courier New, Georgia, Verdana (plus implicit Calibri on screen) |
| 1 | adapter-unresolved | advisory |  | no background found; assuming white (A-5) | **TRUE** OfficeCLI blank master has no p:bg (A-5), no txStyles and no defaultTextStyle |
| 1 | adapter-unresolved | advisory | CoverTitle | latin font could not be resolved | **TRUE** OfficeCLI blank master has no p:bg (A-5), no txStyles and no defaultTextStyle |
| 2 | adapter-unresolved | advisory |  | no background found; assuming white (A-5) | **TRUE** OfficeCLI blank master has no p:bg (A-5), no txStyles and no defaultTextStyle |
| 2 | adapter-unresolved | advisory | T2 | latin font could not be resolved | **TRUE** OfficeCLI blank master has no p:bg (A-5), no txStyles and no defaultTextStyle |
| 2 | edge-margin | warning | EdgeChart | 0.50 cm from the left edge (min 1.27 cm) | **TRUE** A-3: chart at x = 0.5 cm |
| 3 | adapter-unresolved | advisory |  | no background found; assuming white (A-5) | **TRUE** OfficeCLI blank master has no p:bg (A-5), no txStyles and no defaultTextStyle |
| 3 | adapter-unresolved | advisory | T3 | latin font could not be resolved | **TRUE** OfficeCLI blank master has no p:bg (A-5), no txStyles and no defaultTextStyle |
| 3 | dead-band | warning |  | 6.55 cm empty bottom band from 12.50 to 19.05 cm (34% of slide height) | **TRUE** table frame ends at 12.50 cm; 34% empty below |
| 3 | unsupported-content | advisory | CarrierTable | table text is not read in M1 | **TRUE** table text not read |
| 4 | adapter-unresolved | advisory |  | no background found; assuming white (A-5) | **TRUE** OfficeCLI blank master has no p:bg (A-5), no txStyles and no defaultTextStyle |
| 4 | adapter-unresolved | advisory | T4 | latin font could not be resolved | **TRUE** OfficeCLI blank master has no p:bg (A-5), no txStyles and no defaultTextStyle |
| 4 | adapter-unresolved | advisory | StepA | latin font could not be resolved | **TRUE** OfficeCLI blank master has no p:bg (A-5), no txStyles and no defaultTextStyle |
| 4 | adapter-unresolved | advisory | StepB | latin font could not be resolved | **TRUE** OfficeCLI blank master has no p:bg (A-5), no txStyles and no defaultTextStyle |
| 4 | adapter-unresolved | advisory | StepC | latin font could not be resolved | **TRUE** OfficeCLI blank master has no p:bg (A-5), no txStyles and no defaultTextStyle |
| 4 | dead-band | warning |  | 7.05 cm empty bottom band from 12.00 to 19.05 cm (37% of slide height) | **TRUE** 37% empty below the flow; equal-card-row correctly exempt (glued connectors) |
| 5 | adapter-unresolved | advisory |  | no background found; assuming white (A-5) | **TRUE** OfficeCLI blank master has no p:bg (A-5), no txStyles and no defaultTextStyle |
| 5 | adapter-unresolved | advisory | T5 | latin font could not be resolved | **TRUE** OfficeCLI blank master has no p:bg (A-5), no txStyles and no defaultTextStyle |
| 5 | off-slide | advisory | BleedPhoto | runs 2.95 cm past the bottom edge (non-text shape: possible bleed) | **TRUE** advisory: non-text photo 2.95 cm past the bottom (bleed) |
| 6 | adapter-unresolved | advisory |  | no background found; assuming white (A-5) | **TRUE** OfficeCLI blank master has no p:bg (A-5), no txStyles and no defaultTextStyle |
| 6 | adapter-unresolved | advisory | D6 | latin font could not be resolved | **TRUE** OfficeCLI blank master has no p:bg (A-5), no txStyles and no defaultTextStyle |
| 6 | title-not-dominant | warning | T6 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt |

### d07_pgx_60slides

- **Generator:** pptxgenjs
- **Contents:** 60 slides 16:9: title + bullets / line chart every 3rd / table every 4th / photo every 5th; notes on all.
- **Exit:** presented 2, read 0; wall 0.214 s; stderr summary: `34 findings: 0 error, 24 warning, 10 advisory`
- **Script:** `src/pgx_edge.js big60`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| 1 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 2 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 4 | unsupported-content | advisory | Table 0 | table text is not read in M1 | **TRUE** tables |
| 7 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 8 | unsupported-content | advisory | Table 0 | table text is not read in M1 | **TRUE** tables |
| 11 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 13 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 14 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 16 | unsupported-content | advisory | Table 0 | table text is not read in M1 | **TRUE** tables |
| 17 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 19 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 20 | unsupported-content | advisory | Table 0 | table text is not read in M1 | **TRUE** tables |
| 22 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 23 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 26 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 28 | unsupported-content | advisory | Table 0 | table text is not read in M1 | **TRUE** tables |
| 29 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 31 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 32 | unsupported-content | advisory | Table 0 | table text is not read in M1 | **TRUE** tables |
| 34 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 37 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 38 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 40 | unsupported-content | advisory | Table 0 | table text is not read in M1 | **TRUE** tables |
| 41 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 43 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 44 | unsupported-content | advisory | Table 0 | table text is not read in M1 | **TRUE** tables |
| 46 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 47 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 49 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 52 | unsupported-content | advisory | Table 0 | table text is not read in M1 | **TRUE** tables |
| 53 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 56 | unsupported-content | advisory | Table 0 | table text is not read in M1 | **TRUE** tables |
| 58 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |
| 59 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt bullets = 1.8x (presented only) |

### d08_pgx_4x3

- **Generator:** pptxgenjs
- **Contents:** LAYOUT_4x3 (10 x 7.5 in): boxes ending 1.02 cm, exactly 1.27 cm, and -0.51 cm from the right edge.
- **Exit:** presented 2, read 2; wall 0.131 s; stderr summary: `3 findings: 1 error, 2 warning, 0 advisory`
- **Script:** `src/pgx_edge.js ratio43`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| 2 | edge-margin | warning | Text 1 | 1.02 cm from the right edge (min 1.27 cm) | **TRUE** right edge at 9.6 in of 10 in = 1.02 cm; the 1.27 cm box is correctly not flagged |
| 2 | off-slide | error | Text 3 | runs 0.51 cm past the right edge | **TRUE** right edge at 10.2 in = 0.51 cm past |
| 2 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt |

### d09_ppx_portrait

- **Generator:** python-pptx
- **Contents:** Portrait 7.5 x 13.333 in: a 22.5% gap (no dead-band expected), a 30% gap and a box 0.3 in from the bottom.
- **Exit:** presented 2, read 2; wall 0.152 s; stderr summary: `2 findings: 0 error, 2 warning, 0 advisory`
- **Script:** `src/ppx_edge.py`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| 3 | dead-band | warning |  | 10.16 cm empty middle band from 12.70 to 22.86 cm (30% of slide height) | **TRUE** 4.0 in gap = 30% of 13.333 in; the 22.5% gap on slide 2 is correctly not flagged |
| 3 | edge-margin | warning | TextBox 3 | 0.76 cm from the bottom edge (min 1.27 cm) | **TRUE** bottom at 13.033 in = 0.76 cm from the edge |

### d10_ppx_nomasterbg

- **Generator:** python-pptx + lxml
- **Contents:** Default template with p:bg deleted from the master; C8C8C8 text and dark text on the (white) default.
- **Exit:** presented 2, read 2; wall 0.130 s; stderr summary: `5 findings: 0 error, 3 warning, 2 advisory`
- **Script:** `src/ppx_edge.py`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| 1 | adapter-unresolved | advisory |  | no background found; assuming white (A-5) | **TRUE** A-5 background default (one per slide) |
| 2 | adapter-unresolved | advisory |  | no background found; assuming white (A-5) | **TRUE** A-5 background default (one per slide) |
| 2 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title |
| 2 | text-contrast | warning | TextBox 2 | C8C8C8 on FFFFFF (slide background) is 1.67:1 at 24 pt (needs 3:1) | **TRUE** C8C8C8 on the assumed white = 1.67:1 |
| 2 | title-not-dominant | warning | Title 1 | title 44 pt is 1.83× the largest body text (24 pt); needs 2× | **TRUE** 44 vs 24 pt |

### d11_oc_vietnamese

- **Generator:** OfficeCLI
- **Contents:** Vietnamese text, NFC and NFD (decomposed); 14 pt body paragraphs; BBBBBB text; Vietnamese notes.
- **Exit:** presented 2, read 2; wall 0.144 s; stderr summary: `7 findings: 0 error, 4 warning, 3 advisory`
- **Script:** `src/oc_vietnamese.py`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| 1 | adapter-unresolved | advisory |  | no background found; assuming white (A-5) | **TRUE** A-5 |
| 2 | adapter-unresolved | advisory |  | no background found; assuming white (A-5) | **TRUE** A-5 |
| 2 | body-too-small | warning | NoiDung2 | 14 pt text in a 13-word paragraph (min 18 pt in presented mode) | **TRUE** 14 pt, 13 syllable-words (my script comment said 10; I miscounted) |
| 2 | dead-band | warning |  | 7.00 cm empty middle band from 8.50 to 15.50 cm (37% of slide height) | **TRUE** 8.5..15.5 cm empty |
| 3 | adapter-unresolved | advisory |  | no background found; assuming white (A-5) | **TRUE** A-5 |
| 3 | body-too-small | warning | NoiDung3 | 14 pt text in a 11-word paragraph (min 18 pt in presented mode) | **TRUE** NFD text, 11 words counted correctly |
| 3 | text-contrast | warning | Nhat3 | BBBBBB on FFFFFF (slide background) is 1.92:1 at 20 pt (needs 3:1) | **TRUE** BBBBBB on white, NFD text |

### d12_ppx_empty_slides

- **Generator:** python-pptx
- **Contents:** Slide 2: no shapes, no notes. Slide 3: only an empty title placeholder. Slide 4: normal.
- **Exit:** presented 2, read 2; wall 0.133 s; stderr summary: `5 findings: 0 error, 5 warning, 0 advisory`
- **Script:** `src/ppx_edge.py`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| 2 | dead-band | warning |  | 19.05 cm empty top band from 0.00 to 19.05 cm (100% of slide height) | **DEBATABLE** an empty slide: 100% dead band and no notes are both literally true; whether an empty slide is a 'content slide' is open |
| 2 | notes-missing | warning |  | content slide has no speaker notes | **DEBATABLE** an empty slide: 100% dead band and no notes are both literally true; whether an empty slide is a 'content slide' is open |
| 3 | dead-band | warning |  | 19.05 cm empty top band from 0.00 to 19.05 cm (100% of slide height) | **DEBATABLE** only an empty (invisible) title placeholder |
| 3 | notes-missing | warning |  | content slide has no speaker notes | **DEBATABLE** only an empty (invisible) title placeholder |
| 4 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title |

### d13_ppx_zero_slides

- **Generator:** python-pptx
- **Contents:** A presentation with no slides.
- **Exit:** presented 0, read 0; wall 0.108 s; stderr summary: `0 findings: 0 error, 0 warning, 0 advisory`
- **Script:** `src/ppx_edge.py`

No findings.

### d14_oc_implicit_font

- **Generator:** OfficeCLI
- **Contents:** Georgia title, Verdana body, two paragraphs with no font anywhere in the cascade (render in the theme minor font, Calibri).
- **Exit:** presented 0, read 0; wall 0.116 s; stderr summary: `4 findings: 0 error, 0 warning, 4 advisory`
- **Script:** `src/oc_vietnamese.py`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| 1 | adapter-unresolved | advisory |  | no background found; assuming white (A-5) | **TRUE** A-5; latin font unresolved (nothing in the cascade) |
| 2 | adapter-unresolved | advisory |  | no background found; assuming white (A-5) | **TRUE** A-5; latin font unresolved (nothing in the cascade) |
| 2 | adapter-unresolved | advisory | Caption | latin font could not be resolved | **TRUE** A-5; latin font unresolved (nothing in the cascade) |
| 2 | adapter-unresolved | advisory | Footer | latin font could not be resolved | **TRUE** A-5; latin font unresolved (nothing in the cascade) |

### d15_ppx_style_fontref

- **Generator:** python-pptx
- **Contents:** add_shape() rectangles (p:style fontRef = lt1) with a user-set solid fill and no text color: navy card (renders white on navy), pale-yellow card (renders white on pale yellow), control with explicit black.
- **Exit:** presented 2, read 2; wall 0.119 s; stderr summary: `4 findings: 0 error, 4 warning, 0 advisory`
- **Script:** `src/ppx_style_text.py`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| 2 | text-contrast | warning | Rectangle 2 | 000000 on 1F3864 (Rectangle 2) is 1.81:1 at 24 pt (needs 3:1) | **FALSE-POSITIVE** renders WHITE on navy in both OfficeCLI and LibreOffice (p:style fontRef lt1); keyline reports 000000 on 1F3864, 1.81:1 |
| 2 | title-not-dominant | warning | TextBox 1 | title 40 pt is 1.67× the largest body text (24 pt); needs 2× | **TRUE** 40 vs 24 pt |
| 3 | title-not-dominant | warning | TextBox 1 | title 40 pt is 1.67× the largest body text (24 pt); needs 2× | **TRUE** 40 vs 24 pt |
| 4 | title-not-dominant | warning | TextBox 1 | title 40 pt is 1.67× the largest body text (24 pt); needs 2× | **TRUE** 40 vs 24 pt |

### d16_raw_color

- **Generator:** python-pptx + lxml
- **Contents:** clrMapOvr on two slides; a navy panel drawn on the layout with the title placeholder on it (white via layout lstStyle); alpha overlays; a white text box 0.1 in larger than its navy card; white text at 25% alpha.
- **Exit:** presented 2, read 2; wall 0.135 s; stderr summary: `15 findings: 0 error, 9 warning, 6 advisory`
- **Script:** `src/raw_color.py`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| 2 | title-not-dominant | warning | TextBox 1 | title 40 pt is 1.67× the largest body text (24 pt); needs 2× | **TRUE** 40 vs 24 pt |
| 3 | text-contrast | warning | TextBox 2 | 222222 on 000000 (slide background) is 1.32:1 at 24 pt (needs 3:1) | **TRUE** clrMapOvr honored: 222222 on bg1->dk1 = 000000 |
| 3 | title-not-dominant | warning | TextBox 1 | title 40 pt is 1.67× the largest body text (24 pt); needs 2× | **TRUE** 40 vs 24 pt |
| 4 | text-contrast | warning | Title 1 | FFFFFF on FFFFFF (slide background) is 1:1 at 40 pt (needs 3:1) | **FALSE-POSITIVE** the white title sits on the layout's navy panel (render); keyline compares with the white slide background because layout shapes are ignored |
| 4 | title-not-dominant | warning | Title 1 | title 40 pt is 1.67× the largest body text (24 pt); needs 2× | **TRUE** 40 vs 24 pt |
| 5 | adapter-unresolved | advisory | Rectangle 2 | color transform alpha is not supported | **TRUE** alpha is an unsupported transform: advisory, as the spec requires |
| 5 | adapter-unresolved | advisory | Rectangle 4 | color transform alpha is not supported | **TRUE** alpha is an unsupported transform: advisory, as the spec requires |
| 5 | text-contrast | advisory | TextBox 3 | contrast not checked: background is the unknown fill of Rectangle 2 | **TRUE** advisory: the overlay fill has an unsupported alpha, so contrast is skipped as the spec requires |
| 5 | text-contrast | advisory | TextBox 5 | contrast not checked: background is the unknown fill of Rectangle 4 | **TRUE** advisory: the overlay fill has an unsupported alpha, so contrast is skipped as the spec requires |
| 5 | title-not-dominant | warning | TextBox 1 | title 40 pt is 1.67× the largest body text (24 pt); needs 2× | **TRUE** 40 vs 24 pt |
| 6 | text-contrast | warning | TextBox 3 | FFFFFF on FFFFFF (slide background) is 1:1 at 24 pt (needs 3:1) | **FALSE-POSITIVE** white text on the navy card (render); the text box is 0.1 in larger than the card, so the spec's containment test falls back to the white slide background (spec-level) |
| 6 | title-not-dominant | warning | TextBox 1 | title 40 pt is 1.67× the largest body text (24 pt); needs 2× | **TRUE** 40 vs 24 pt |
| 7 | adapter-unresolved | advisory | TextBox 3 | color transform alpha is not supported | **TRUE** run alpha unsupported |
| 7 | text-contrast | advisory | TextBox 3 | contrast not checked for runs whose color could not be resolved | **TRUE** advisory |
| 7 | title-not-dominant | warning | TextBox 1 | title 40 pt is 1.67× the largest body text (24 pt); needs 2× | **TRUE** 40 vs 24 pt |

### d17_raw_geometry

- **Generator:** python-pptx + raw XML
- **Contents:** Rotated text boxes; a rotated group; hidden shapes (cNvPr hidden=1); mc:AlternateContent equation box at x = 0.3 cm; normAutofit fontScale 55%; full-width header band + half-slide bleed photo; full-slide photo.
- **Exit:** presented 2, read 2; wall 0.197 s; stderr summary: `16 findings: 4 error, 8 warning, 4 advisory`
- **Script:** `src/raw_geometry.py`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| 2 | box-overlap | advisory | Title | box overlaps R1 rotated inside by 2.00 × 2.18 cm (boxes, not ink) | **TRUE** advisory: rotated AABBs x 6..8 / 19..21 cm, y from 1.525 cm, do intersect the title box |
| 2 | box-overlap | advisory | Title | box overlaps R2 rotated outside by 2.00 × 2.20 cm (boxes, not ink) | **TRUE** advisory: rotated AABBs x 6..8 / 19..21 cm, y from 1.525 cm, do intersect the title box |
| 2 | off-slide | error | R2 rotated outside | runs 0.48 cm past the top edge | **TRUE** R2 rotated 90 deg: AABB y -0.475..19.525 cm; R1 (inside only when rotated) correctly not flagged |
| 3 | dead-band | warning |  | 11.83 cm empty middle band from 3.70 to 15.53 cm (62% of slide height) | **TRUE** 3.70..15.53 cm has no shape |
| 3 | off-slide | error | Child A | runs 0.48 cm past the top edge | **TRUE** rotated group composed correctly: children at y -0.475 and 19.525 cm |
| 3 | off-slide | error | Child B | runs 0.48 cm past the bottom edge | **TRUE** rotated group composed correctly: children at y -0.475 and 19.525 cm |
| 4 | off-slide | error | Parked note | runs 9.00 cm past the left edge | **FALSE-POSITIVE** 'Parked note' has cNvPr hidden=1: not shown (LibreOffice render; PowerPoint honors hidden) |
| 4 | text-contrast | warning | Hidden white | FFFFFF on FFFFFF (slide background) is 1:1 at 24 pt (needs 3:1) | **FALSE-POSITIVE** 'Hidden white' has hidden=1: not shown |
| 4 | title-not-dominant | warning | Title | title 40 pt is 1.67× the largest body text (24 pt); needs 2× | **TRUE** 40 vs 24 pt (visible body) |
| 5 | edge-margin | warning | TextBox 115 | 0.30 cm from the left edge (min 1.27 cm) | **TRUE** equation box at 0.30 cm (read from mc:Fallback, same xfrm) |
| 5 | unsupported-content | advisory | TextBox 115 | mc:AlternateContent: only the mc:Fallback content was read | **TRUE** mc:Choice not read |
| 7 | edge-margin | warning | Header band | -0.00 cm from the right edge (min 1.27 cm) | **DEBATABLE** full-width header band / half-slide bleed photo: fires by definition (not >= 95% of the slide), but an intentional bleed; message prints '-0.00 cm' (shape is 1 EMU past the edge) |
| 7 | edge-margin | warning | Picture 118 | -0.00 cm from the right edge (min 1.27 cm) | **DEBATABLE** full-width header band / half-slide bleed photo: fires by definition (not >= 95% of the slide), but an intentional bleed; message prints '-0.00 cm' (shape is 1 EMU past the edge) |
| 7 | title-not-dominant | warning | Header band | title 36 pt is 1.5× the largest body text (24 pt); needs 2× | **TRUE** 36 vs 24 pt |
| 8 | dead-band | warning |  | 15.35 cm empty bottom band from 3.70 to 19.05 cm (81% of slide height) | **DEBATABLE** full-slide photo: the spec excludes backgrounds from content, so 81% 'empty' although the photo fills the slide |
| 8 | text-contrast | advisory | Photo title | contrast not checked: background is the picture Picture 1 | **TRUE** advisory: text over a picture |

### d18_lo_autofit

- **Generator:** python-pptx -> LibreOffice
- **Contents:** 20-line body placeholder with normAutofit; LibreOffice computed and wrote fontScale=28122 (32 pt renders at about 9 pt).
- **Exit:** presented 2, read 2; wall 0.159 s; stderr summary: `2 findings: 0 error, 2 warning, 0 advisory`
- **Script:** `src/lo_autofit.py + lo_autofit.sh`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| 2 | edge-margin | warning | PlaceHolder 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title |
| 2 | title-not-dominant | warning | PlaceHolder 1 | title 44 pt is 1.38× the largest body text (32 pt); needs 2× | **FALSE-POSITIVE** LibreOffice wrote fontScale=28122: the body renders at 32 x 0.281 = 9.0 pt (both renderers), so the title is 4.9x the body, not 1.38x |

### d19_raw_notes

- **Generator:** python-pptx + raw XML
- **Contents:** Notes slides as PowerPoint writes them: slide-number field only, whitespace only, real text, header placeholder only; a hidden slide (show=0).
- **Exit:** presented 2, read 2; wall 0.173 s; stderr summary: `9 findings: 0 error, 9 warning, 0 advisory`
- **Script:** `src/raw_notes.py`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| 2 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title |
| 2 | notes-missing | warning |  | content slide has no speaker notes | **TRUE** slide-number field / whitespace / header text are correctly not counted as notes |
| 3 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title |
| 3 | notes-missing | warning |  | content slide has no speaker notes | **TRUE** slide-number field / whitespace / header text are correctly not counted as notes |
| 4 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title |
| 5 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **DEBATABLE** hidden slide (show=0): not presented |
| 5 | notes-missing | warning |  | content slide has no speaker notes | **DEBATABLE** hidden slide (show=0): not presented |
| 6 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title |
| 6 | notes-missing | warning |  | content slide has no speaker notes | **TRUE** slide-number field / whitespace / header text are correctly not counted as notes |

### d20_pgx_slop

- **Generator:** pptxgenjs
- **Contents:** Accent bar under title; 4 equal cards with separate text boxes; 3 cards joined by right-arrow shapes; 3 cards joined by pptxgenjs lines; a table 5 cm off the right edge and a chart 2.54 cm off the bottom; a 3 pt line under a title.
- **Exit:** presented 2, read 2; wall 0.155 s; stderr summary: `12 findings: 0 error, 9 warning, 3 advisory`
- **Script:** `src/pgx_slop.js`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| 2 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt |
| 2 | title-underline | warning | Shape 1 | 3.05 × 0.30 cm bar 0.25 cm below the title (10% of the content width) reads as an underline accent | **TRUE** 3.05 x 0.30 cm bar 0.25 cm under the title |
| 3 | equal-card-row | warning | Shape 1 | 4 equal cards in a row (7.11 × 9.14 cm, gaps 0.76 cm), each with text | **TRUE** 4 equal cards, text in separate text boxes |
| 3 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt |
| 4 | equal-card-row | warning | Text 1 | 3 equal cards in a row (8.38 × 9.14 cm, gaps 2.54 cm), each with text | **DEBATABLE** a 3-step flow joined by right-arrow shapes; only p:cxnSp connectors exempt, and pptxgenjs cannot write connectors |
| 4 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt |
| 5 | equal-card-row | warning | Text 1 | 3 equal cards in a row (8.38 × 9.14 cm, gaps 2.54 cm), each with text | **DEBATABLE** a 3-step flow joined by pptxgenjs lines (p:sp prst=line, not p:cxnSp) |
| 5 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt |
| 6 | off-slide | advisory | Chart 0 | runs 2.54 cm past the bottom edge (non-text shape: possible bleed) | **DEBATABLE** advisory only, but the render shows the category labels cut off |
| 6 | off-slide | advisory | Table 0 | runs 5.00 cm past the right edge (non-text shape: possible bleed) | **TRUE** position right, severity wrong: a table with text 5.00 cm off-slide is 'advisory (non-text)'; should be error (FN-4) |
| 6 | unsupported-content | advisory | Table 0 | table text is not read in M1 | **TRUE** table |
| 7 | title-not-dominant | warning | Text 0 | title 36 pt is 1.8× the largest body text (20 pt); needs 2× | **TRUE** 36 vs 20 pt |

### d21_raw_two_masters

- **Generator:** python-pptx + zip surgery
- **Contents:** Two slide masters with two themes (theme2: accent1 FFD166, Georgia/Verdana); slide 3 uses master 2.
- **Exit:** presented 2, read 2; wall 0.168 s; stderr summary: `6 findings: 0 error, 6 warning, 0 advisory`
- **Script:** `src/raw_two_masters.py`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| deck | font-count | warning |  | 3 font families: Calibri, Georgia, Verdana (max 2) | **TRUE** per-master theme fonts resolved: Calibri, Georgia, Verdana |
| 2 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title |
| 2 | title-not-dominant | warning | Title 1 | title 44 pt is 1.83× the largest body text (24 pt); needs 2× | **TRUE** 44 vs 24 pt |
| 3 | edge-margin | warning | Title 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** template title |
| 3 | text-contrast | warning | TextBox 2 | FFD166 on FFFFFF (slide background) is 1.44:1 at 24 pt (needs 3:1) | **TRUE** theme2 accent1 FFD166 on white = 1.44:1 (per-master theme honored) |
| 3 | title-not-dominant | warning | Title 1 | title 44 pt is 1.83× the largest body text (24 pt); needs 2× | **TRUE** 44 vs 24 pt |

### d23_pgx_cjk_thai

- **Generator:** pptxgenjs
- **Contents:** Japanese, Chinese and Thai slides; 10-12 pt body paragraphs (no spaces between words).
- **Exit:** presented 2, read 2; wall 0.143 s; stderr summary: `1 finding: 0 error, 1 warning, 0 advisory`
- **Script:** `src/pgx_cjk.js`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| deck | font-count | warning |  | 4 font families: Calibri, Meiryo, Microsoft YaHei, Tahoma (max 2) | **TRUE** Calibri, Meiryo, Microsoft YaHei, Tahoma |

### d25_ppx_localized_names

- **Generator:** python-pptx
- **Contents:** Shape names as a localized PowerPoint writes them (Tiêu đề 1, タイトル 2, Textfeld 3 – Übersicht, Box 🚀 4), each with a planted finding.
- **Exit:** presented 2, read 2; wall 0.157 s; stderr summary: `8 findings: 0 error, 8 warning, 0 advisory`
- **Script:** `src/ppx_localized_names.py`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| 1 | edge-margin | warning | Tiêu đề 1 | 0.76 cm from the top edge (min 1.27 cm) | **TRUE** planted (edge 0.51 cm, CCCCCC text, template title, 44 vs 24 pt) |
| 1 | edge-margin | warning | タイトル 2 | 0.51 cm from the left edge (min 1.27 cm) | **TRUE** planted (edge 0.51 cm, CCCCCC text, template title, 44 vs 24 pt) |
| 1 | edge-margin | warning | Textfeld 3 – Übersicht | 0.51 cm from the left edge (min 1.27 cm) | **TRUE** planted (edge 0.51 cm, CCCCCC text, template title, 44 vs 24 pt) |
| 1 | edge-margin | warning | Box 🚀 4 | 0.51 cm from the left edge (min 1.27 cm) | **TRUE** planted (edge 0.51 cm, CCCCCC text, template title, 44 vs 24 pt) |
| 1 | text-contrast | warning | タイトル 2 | CCCCCC on FFFFFF (slide background) is 1.61:1 at 24 pt (needs 3:1) | **TRUE** planted (edge 0.51 cm, CCCCCC text, template title, 44 vs 24 pt) |
| 1 | text-contrast | warning | Textfeld 3 – Übersicht | CCCCCC on FFFFFF (slide background) is 1.61:1 at 24 pt (needs 3:1) | **TRUE** planted (edge 0.51 cm, CCCCCC text, template title, 44 vs 24 pt) |
| 1 | text-contrast | warning | Box 🚀 4 | CCCCCC on FFFFFF (slide background) is 1.61:1 at 24 pt (needs 3:1) | **TRUE** planted (edge 0.51 cm, CCCCCC text, template title, 44 vs 24 pt) |
| 1 | title-not-dominant | warning | Tiêu đề 1 | title 44 pt is 1.83× the largest body text (24 pt); needs 2× | **TRUE** planted (edge 0.51 cm, CCCCCC text, template title, 44 vs 24 pt) |

### d26_oc_default_text

- **Generator:** OfficeCLI
- **Contents:** A navy-filled shape with no text color anywhere (no p:style, no txStyles).
- **Exit:** presented 2, read 2; wall 0.131 s; stderr summary: `7 findings: 0 error, 2 warning, 5 advisory`
- **Script:** `src/oc_default_text.sh`

| Slide | Rule | Severity | Shape | Message | Verdict |
|---|---|---|---|---|---|
| 1 | adapter-unresolved | advisory |  | no background found; assuming white (A-5) | **TRUE** A-5; fonts unresolved |
| 1 | adapter-unresolved | advisory | Cover | latin font could not be resolved | **TRUE** A-5; fonts unresolved |
| 2 | adapter-unresolved | advisory |  | no background found; assuming white (A-5) | **TRUE** A-5; fonts unresolved |
| 2 | adapter-unresolved | advisory | Head | latin font could not be resolved | **TRUE** A-5; fonts unresolved |
| 2 | adapter-unresolved | advisory | DarkCard | latin font could not be resolved | **TRUE** A-5; fonts unresolved |
| 2 | text-contrast | warning | DarkCard | 000000 on 1F3864 (DarkCard) is 1.81:1 at 24 pt (needs 3:1) | **TRUE** no color anywhere: PowerPoint draws black (OfficeCLI render agrees); LibreOffice's 'automatic' color draws white |
| 2 | title-not-dominant | warning | Head | title 40 pt is 1.67× the largest body text (24 pt); needs 2× | **TRUE** 40 vs 24 pt |

### d27_strict_from_ppx

- **Generator:** d02 converted to ISO/IEC 29500 Strict
- **Contents:** purl.oclc.org namespaces and relationship types, conformance=strict, percentages as "NN%". LibreOffice opens and renders all 11 slides.
- **Exit:** presented 1, read 1; wall 0.132 s; stderr summary: `keyline: cannot scan /home/claude/stress/decks/d27_strict_from_ppx.pptx: presentation.xml has no valid p:sldSz`
- **Script:** `src/strict_convert.py`

No findings.

### 7.2 Malformed and unusual packages (`src/malformed.py`, `src/big_media.py`, run by `src/run_bad.sh`)

Required cases:

| Case | Content |
|---|---|
| m01 | Truncated at 60% |
| m02 | `ppt/presentation.xml` removed |
| m03 | A slide's layout relationship points to a missing part |
| m03b | A presentation→slide relationship points to a missing part |
| m04 | Slide XML not well-formed |
| m05 | 0 bytes |
| m06 | A directory |
| m07 | A non-existent path |

Extra cases:

| Case | Content |
|---|---|
| x01 to x22 | Missing or broken parts, XXE/entity attacks, a renamed docx, a CFB (encrypted) file |
| v01 | Relocated main part (valid) |
| v02 | Absolute relationship targets (valid) |
| v03 | A UTF-16 slide part (valid) |
| v04 | Part-name case differs from the rels target |
| v05 | Percent-encoded part name |
| v06 | STORED zip with a comment (valid) |
| v07 | ppsx content type (valid) |
| v08 | pptm content type (valid) |
| v09 | 600 MB embedded video (valid) |

```
m01_truncated.pptx                       exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan m01_truncated.pptx: not a zip file: m01_truncated.pptx
m02_no_presentation_xml.pptx             exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan m02_no_presentation_xml.pptx: not a pptx: main part ppt/presentation.xml is missing
m03_broken_rel_layout.pptx               exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan m03_broken_rel_layout.pptx: ppt/slides/slide2.xml has no slide layout
m03b_broken_rel_slide.pptx               exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan m03b_broken_rel_slide.pptx: slide 4 (rId11) is missing from the package
m04_slide_not_wellformed.pptx            exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan m04_slide_not_wellformed.pptx: XML parse failure in ppt/slides/slide3.xml: Opening and ending tag mismatch: spTree line 2 and spT
m05_zero_bytes.pptx                      exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan m05_zero_bytes.pptx: not a zip file: m05_zero_bytes.pptx
m06_a_directory.pptx                     exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan m06_a_directory.pptx: no such file: m06_a_directory.pptx
v01_main_part_renamed.pptx               exit=2   stderr_lines=28  traceback=0 | 27 findings: 1 error, 18 warning, 8 advisory
v02_absolute_rel_targets.pptx            exit=2   stderr_lines=28  traceback=0 | 27 findings: 1 error, 18 warning, 8 advisory
v03_slide_utf16.pptx                     exit=2   stderr_lines=28  traceback=0 | 27 findings: 1 error, 18 warning, 8 advisory
v04_part_name_case.pptx                  exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan v04_part_name_case.pptx: slide 2 (rId9) is missing from the package
v05_percent_encoded_name.pptx            exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan v05_percent_encoded_name.pptx: slide 2 (rId9) is missing from the package
v06_stored_zip_comment.pptx              exit=2   stderr_lines=28  traceback=0 | 27 findings: 1 error, 18 warning, 8 advisory
v07_ppsx_content_type.pptx               exit=2   stderr_lines=28  traceback=0 | 27 findings: 1 error, 18 warning, 8 advisory
v08_pptm_content_type.pptx               exit=2   stderr_lines=28  traceback=0 | 27 findings: 1 error, 18 warning, 8 advisory
v09_embedded_video_600mb.pptx            exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan v09_embedded_video_600mb.pptx: uncompressed size 629323583 bytes exceeds the 536870912 limit
x01_random_bytes.pptx                    exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan x01_random_bytes.pptx: not a zip file: x01_random_bytes.pptx
x02_no_content_types.pptx                exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan x02_no_content_types.pptx: not an OOXML package: [Content_Types].xml is missing
x03_no_root_rels.pptx                    exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan x03_no_root_rels.pptx: not an OOXML package: no officeDocument relationship
x04_chart_part_missing.pptx              exit=2   stderr_lines=28  traceback=0 | 27 findings: 1 error, 18 warning, 8 advisory
x05_image_part_missing.pptx              exit=2   stderr_lines=28  traceback=0 | 27 findings: 1 error, 18 warning, 8 advisory
x06_notes_part_missing.pptx              exit=2   stderr_lines=29  traceback=0 | 28 findings: 1 error, 19 warning, 8 advisory
x07_theme_missing.pptx                   exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan x07_theme_missing.pptx: missing part ppt/theme/theme1.xml
x08_master_missing.pptx                  exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan x08_master_missing.pptx: ppt/slideLayouts/slideLayout1.xml has no slide master
x09_layout_part_missing.pptx             exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan x09_layout_part_missing.pptx: ppt/slides/slide2.xml has no slide layout
x10_sldid_rid_dangling.pptx              exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan x10_sldid_rid_dangling.pptx: slide 3 (rId999) is missing from the package
x11_billion_laughs.pptx                  exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan x11_billion_laughs.pptx: XML parse failure in ppt/slides/slide3.xml: Maximum entity amplification factor exceeded, see xmlCtxtSet
x12_xxe_local_file.pptx                  exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan x12_xxe_local_file.pptx: DOCTYPE not allowed in ppt/slides/slide3.xml
x13_xxe_dev_zero.pptx                    exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan x13_xxe_dev_zero.pptx: DOCTYPE not allowed in ppt/slides/slide3.xml
x14_docx_renamed.pptx                    exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan x14_docx_renamed.pptx: not a pptx: main part is word/document.xml (application/vnd.openxmlformats-officedocument.wordprocessingml
x15_cfb_encrypted.pptx                   exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan x15_cfb_encrypted.pptx: not a zip file: x15_cfb_encrypted.pptx
x16_presentation_not_wellformed.pptx     exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan x16_presentation_not_wellformed.pptx: XML parse failure in ppt/presentation.xml: expected '>', line 2, column 3444
x17_master_not_wellformed.pptx           exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan x17_master_not_wellformed.pptx: XML parse failure in ppt/slideMasters/slideMaster1.xml: expected '>', line 2, column 11870
x18_theme_not_wellformed.pptx            exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan x18_theme_not_wellformed.pptx: XML parse failure in ppt/theme/theme1.xml: expected '>', line 2, column 7491
x19_chart_not_wellformed.pptx            exit=2   stderr_lines=28  traceback=0 | 27 findings: 1 error, 18 warning, 8 advisory
x20_notes_not_wellformed.pptx            exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan x20_notes_not_wellformed.pptx: XML parse failure in ppt/notesSlides/notesSlide2.xml: Couldn't find end of Start Tag ma line 2, li
x21_layout_not_wellformed.pptx           exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan x21_layout_not_wellformed.pptx: XML parse failure in ppt/slideLayouts/slideLayout6.xml: Couldn't find end of Start Tag master lin
x22_slide_is_empty_file.pptx             exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan x22_slide_is_empty_file.pptx: XML parse failure in ppt/slides/slide5.xml: Document is empty, line 1, column 1
m07_does_not_exist.pptx                  exit=1   stderr_lines=1   traceback=0 | keyline: cannot scan /home/claude/stress/decks/bad/m07_does_not_exist.pptx: no such file: /home/claude/stress/decks/bad/m07_does_not_exist.pptx
```

### 7.3 Schema oddities (`src/raw_oddities.py`, run by `src/run_dir.sh decks/odd`)

The base is a python-pptx 4:3 deck: title slide, plus a content slide with a text box, a group of two rectangles and a glued connector. Each file changes one thing. Cases whose names end in `_valid` are schema-valid.

```
o01_xfrm_no_off                    exit=2   tb=0 | 7 findings: 0 error, 4 warning, 3 advisory
o02_xfrm_no_ext                    exit=2   tb=0 | 7 findings: 0 error, 4 warning, 3 advisory
o03_sp_no_xfrm_valid               exit=2   tb=0 | 7 findings: 0 error, 4 warning, 3 advisory
o04_grp_no_choff_chext_valid       exit=2   tb=0 | 7 findings: 2 error, 3 warning, 2 advisory
o05_grp_chext_zero                 exit=2   tb=0 | 5 findings: 0 error, 3 warning, 2 advisory
o06_grp_no_xfrm_valid              exit=2   tb=0 | 5 findings: 0 error, 3 warning, 2 advisory
o07_rot_negative                   exit=2   tb=0 | 7 findings: 1 error, 2 warning, 4 advisory
o08_rot_over_360                   exit=2   tb=0 | 5 findings: 0 error, 3 warning, 2 advisory
o09_coord_float_text               exit=2   tb=0 | 7 findings: 0 error, 4 warning, 3 advisory
o10_coord_huge                     exit=2   tb=0 | 6 findings: 1 error, 3 warning, 2 advisory
o11_ext_negative                   exit=2   tb=0 | 5 findings: 0 error, 3 warning, 2 advisory
o12_sldsz_missing                  exit=1   tb=0 | keyline: cannot scan decks/odd/o12_sldsz_missing.pptx: presentation.xml has no valid p:sldSz
o13_sldsz_zero                     exit=2   tb=0 | 10 findings: 6 error, 1 warning, 3 advisory
o14_graphicframe_no_xfrm           exit=2   tb=0 | 7 findings: 0 error, 3 warning, 4 advisory
o15_pic_no_blip                    exit=2   tb=0 | 6 findings: 0 error, 4 warning, 2 advisory
o16_cxn_dangling_ids               exit=2   tb=0 | 5 findings: 0 error, 3 warning, 2 advisory
o17_contentpart_ink                exit=2   tb=0 | 6 findings: 0 error, 3 warning, 3 advisory
o18_orphan_placeholder             exit=2   tb=0 | 7 findings: 0 error, 2 warning, 5 advisory
o19_nested_groups_40_valid         exit=2   tb=0 | 6 findings: 1 error, 3 warning, 2 advisory
o20_nested_groups_300_valid        exit=1   tb=0 | keyline: cannot scan decks/odd/o20_nested_groups_300_valid.pptx: XML parse failure in ppt/slides/slide2.xml: Excessive depth in document: 25
o21_sz_zero                        exit=2   tb=0 | 5 findings: 0 error, 3 warning, 2 advisory
o22_sz_huge                        exit=2   tb=0 | 5 findings: 0 error, 3 warning, 2 advisory
o23_sz_not_int                     exit=2   tb=0 | 5 findings: 0 error, 2 warning, 3 advisory
o24_txbody_no_p                    exit=2   tb=0 | 5 findings: 0 error, 3 warning, 2 advisory
o25_field_and_br_only              exit=2   tb=0 | 4 findings: 0 error, 2 warning, 2 advisory
o26_latin_theme_ea_ref             exit=2   tb=0 | 6 findings: 0 error, 3 warning, 3 advisory
o27_empty_typeface                 exit=2   tb=0 | 5 findings: 0 error, 3 warning, 2 advisory
o28_lvl_out_of_range               exit=2   tb=0 | 5 findings: 0 error, 3 warning, 2 advisory
o29_hslclr                         exit=2   tb=0 | 7 findings: 0 error, 3 warning, 4 advisory
o30_prstclr                        exit=2   tb=0 | 7 findings: 0 error, 3 warning, 4 advisory
o31_sysclr_no_lastclr              exit=2   tb=0 | 7 findings: 0 error, 3 warning, 4 advisory
o32_scrgbclr                       exit=2   tb=0 | 7 findings: 0 error, 3 warning, 4 advisory
o33_transforms_exotic              exit=2   tb=0 | 7 findings: 0 error, 3 warning, 4 advisory
o34_lummod_over                    exit=2   tb=0 | 5 findings: 0 error, 3 warning, 2 advisory
o35_phclr_bare                     exit=2   tb=0 | 7 findings: 0 error, 3 warning, 4 advisory
o36_srgb_bad_hex                   exit=2   tb=0 | 7 findings: 0 error, 3 warning, 4 advisory
o37_srgb_short_hex                 exit=2   tb=0 | 7 findings: 0 error, 3 warning, 4 advisory
o38_master_no_clrmap               exit=2   tb=0 | 5 findings: 0 error, 3 warning, 2 advisory
o39_master_no_txstyles_valid       exit=2   tb=0 | 5 findings: 0 error, 3 warning, 2 advisory
o40_theme_no_fontscheme            exit=2   tb=0 | 5 findings: 0 error, 3 warning, 2 advisory
o41_theme_no_clrscheme             exit=2   tb=0 | 16 findings: 0 error, 3 warning, 13 advisory
o42_bgref_idx_huge                 exit=2   tb=0 | 11 findings: 0 error, 3 warning, 8 advisory
o43_extlst_everywhere_valid        exit=2   tb=0 | 5 findings: 0 error, 3 warning, 2 advisory
o44_ac_in_group_valid              exit=2   tb=0 | 6 findings: 0 error, 3 warning, 3 advisory
o45_unknown_element_in_sptree      exit=2   tb=0 | 5 findings: 0 error, 3 warning, 2 advisory
o46_shape_id_duplicate_valid       exit=2   tb=0 | 5 findings: 0 error, 3 warning, 2 advisory
o47_shape_id_missing               exit=2   tb=0 | 5 findings: 0 error, 3 warning, 2 advisory
o48_shape_id_text                  exit=2   tb=0 | 5 findings: 0 error, 3 warning, 2 advisory
o49_notes_rel_to_slide             exit=2   tb=0 | 6 findings: 0 error, 4 warning, 2 advisory
o50_layout_rel_to_master           exit=1   tb=0 | keyline: cannot scan decks/odd/o50_layout_rel_to_master.pptx: ppt/slideMasters/slideMaster1.xml has no slide master
o51_lummod_percent_string          exit=1   tb=1 | ValueError: invalid literal for int() with base 10: '75%'
o52_alpha_percent_string           exit=1   tb=1 | ValueError: invalid literal for int() with base 10: '50%'
o53_tint_percent_in_master_bg      exit=1   tb=1 | ValueError: invalid literal for int() with base 10: '95%'
o54_lumoff_float                   exit=1   tb=1 | ValueError: invalid literal for int() with base 10: '25000.0'
o55_cxn_id_word                    exit=1   tb=1 | ValueError: invalid literal for int() with base 10: 'first'
o56_ext_40_digits                  exit=1   tb=1 | decimal.InvalidOperation: [<class 'decimal.InvalidOperation'>]
o57_rotated_ext_25_digits          exit=2   tb=0 | 5 findings: 1 error, 2 warning, 2 advisory
o58_off_universal_measure          exit=2   tb=0 | 7 findings: 0 error, 4 warning, 3 advisory
o59_sz_float                       exit=2   tb=0 | 5 findings: 0 error, 2 warning, 3 advisory
o60_rot_float                      exit=2   tb=0 | 5 findings: 0 error, 3 warning, 2 advisory
```
