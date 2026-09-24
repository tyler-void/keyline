#!/usr/bin/env python3
"""REFERENCE ONLY - do not ship, do not import.

deck-lint v0 prototype written during research (2026-09-24). Reads `officecli dump` JSON.
Known problems, all addressed by specs/001-lint-core/spec.md:
  - folds `set` commands by positional shape[N]; officecli skips charts in that count (fixed once, still fragile)
  - text-overlap compares bounding boxes, not ink: 6 false positives on fixtures/golden/editorial.pptx
  - body-too-small has no mode: flags read-mode decks with presented-mode floors
  - depends on officecli; keyline lint must read .pptx directly

Original docstring:
deck-lint v0 — deterministic design rules for .pptx, read from `officecli dump` JSON.
Usage:  officecli dump deck.pptx -o bp.json && python3 deck_lint.py bp.json [--json]
Exit:   0 clean · 2 findings · 1 could not scan   (same contract as `impeccable detect`)
"""
import json, sys, re
from collections import defaultdict

SLIDE_W, SLIDE_H = 33.87, 19.05          # cm, widescreen
EDGE_MIN, GAP_MIN = 1.27, 0.76           # cm
BODY_MIN_PT, TITLE_RATIO = 18.0, 2.0
EMU_PER_CM = 360000.0

def to_cm(v):
    if v is None: return None
    s = str(v).strip()
    m = re.match(r"^(-?[\d.]+)\s*(cm|mm|in|pt|px|)$", s)
    if not m: return None
    n, u = float(m.group(1)), m.group(2)
    return {"cm": n, "mm": n/10, "in": n*2.54, "pt": n*2.54/72,
            "px": n*2.54/96, "": n/EMU_PER_CM}[u]

def to_pt(v):
    if v is None: return None
    m = re.match(r"^([\d.]+)\s*(pt)?$", str(v).strip())
    return float(m.group(1)) if m else None

def brightness(hexc):
    if not hexc: return None
    h = str(hexc).lstrip("#")
    if len(h) != 6: return None
    try: r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    except ValueError: return None
    return (0.299*r + 0.587*g + 0.114*b) / 255

class Box:
    __slots__ = ("slide","path","name","x","y","w","h","font","size","color","fill","text","z","kind")

def load(bp):
    """Fold the dump's `add` + `set` command stream into one box per shape."""
    boxes, by_path = [], {}
    for it in bp:
        if it.get("command") != "add" or it.get("type") not in (
                "shape","textbox","chart","picture","table","group","connector"):
            continue
        p = it.get("props", {})
        b = Box()
        b.slide = it.get("parent","")
        b.kind  = it["type"]
        b.name  = p.get("name","")
        b.x, b.y = to_cm(p.get("x")), to_cm(p.get("y"))
        b.w, b.h = to_cm(p.get("width")), to_cm(p.get("height"))
        b.font, b.size = p.get("font") or p.get("font.latin"), to_pt(p.get("size"))
        b.color, b.fill = p.get("color"), p.get("fill")
        b.text, b.z = p.get("text","") or "", int(p.get("zorder") or 0)
        sid = p.get("id")
        if sid: by_path[f"{b.slide}/shape[@id={sid}]"] = b
        boxes.append(b)
    # `set` on a paragraph carries the real text/size/font — fold it back in
    for it in bp:
        if it.get("command") != "set": continue
        path, p = it.get("path",""), it.get("props",{})
        m = re.match(r"^(/slide\[\d+\])/(?:shape|textbox)\[(\d+)\]", path)
        if not m: continue
        slide, idx = m.group(1), int(m.group(2))
        # officecli's positional shape[N] counts shape+textbox and SKIPS chart/
        # picture/table/connector. Indexing the raw add-order shifts after any
        # chart. (Verified against `dump` output — undocumented.)
        cand = [b for b in boxes if b.slide == slide and b.kind in ("shape","textbox")]
        if idx-1 >= len(cand): continue
        b = cand[idx-1]
        if p.get("text"): b.text = (b.text + " " + p["text"]).strip()
        if p.get("size"): b.size = to_pt(p["size"]) or b.size
        f = p.get("font") or p.get("font.latin")
        if f: b.font = f
        if p.get("color"): b.color = p["color"]
    return boxes

def slide_no(s):
    m = re.search(r"\[(\d+)\]", s or "")
    return int(m.group(1)) if m else 0

def lint(bp):
    boxes = load(bp)
    slides = defaultdict(list)
    for b in boxes: slides[b.slide].append(b)
    notes = {it.get("parent") for it in bp
             if it.get("command")=="add" and it.get("type")=="notes"}
    out = []
    def flag(slide, rule, msg):
        out.append({"slide": slide_no(slide), "rule": rule, "message": msg})

    fonts_all = set()
    for slide, bs in sorted(slides.items(), key=lambda kv: slide_no(kv[0])):
        texts = [b for b in bs if b.text.strip() and b.size]
        for b in bs:
            if b.font: fonts_all.add(b.font)

        # R1 body-too-small
        for b in texts:
            words = len(b.text.split())
            if b.size < BODY_MIN_PT and words > 5:
                flag(slide, "body-too-small",
                     f"{b.size:g}pt on {words}-word text (floor {BODY_MIN_PT:g}pt): {b.text[:40]!r}")

        # R2 title-not-dominant. A big short string is a KPI number, not a title.
        titlish = [b for b in texts if not (b.size >= 48 and len(b.text.split()) <= 5)]
        if titlish:
            big = max(titlish, key=lambda b: b.size)
            body = [b for b in titlish if b is not big and len(b.text.split()) > 4]
            if body:
                bmax = max(b.size for b in body)
                if big.size < bmax * TITLE_RATIO:
                    flag(slide, "title-not-dominant",
                         f"largest text {big.size:g}pt vs body {bmax:g}pt (needs {TITLE_RATIO:g}x)")

        # R3 edge-margin
        for b in bs:
            if None in (b.x, b.y, b.w, b.h) or b.kind == "connector": continue
            if b.w >= SLIDE_W - 0.1 and b.h >= SLIDE_H - 0.1: continue   # full-bleed bg
            for side, v in (("left", b.x), ("top", b.y),
                            ("right", SLIDE_W-(b.x+b.w)), ("bottom", SLIDE_H-(b.y+b.h))):
                if v < -0.05:
                    flag(slide, "off-slide", f"{b.name or b.kind} runs {abs(v):.2f}cm past {side} edge")
                elif v < EDGE_MIN - 0.05:
                    flag(slide, "edge-margin",
                         f"{b.name or b.kind} {v:.2f}cm from {side} edge (floor {EDGE_MIN}cm)")

        # R4 dead-band — a horizontal band >25% of slide height with nothing in it
        occupied = [(b.y, b.y+b.h) for b in bs
                    if b.y is not None and b.h and not (b.w and b.w >= SLIDE_W-0.1 and b.h >= SLIDE_H-0.1)]
        if occupied:
            occupied.sort()
            merged, cur = [], list(occupied[0])
            for s0, e0 in occupied[1:]:
                if s0 <= cur[1] + 0.01: cur[1] = max(cur[1], e0)
                else: merged.append(tuple(cur)); cur = [s0, e0]
            merged.append(tuple(cur))
            gaps = [(0.0, merged[0][0])] + \
                   [(merged[i][1], merged[i+1][0]) for i in range(len(merged)-1)] + \
                   [(merged[-1][1], SLIDE_H)]
            for g0, g1 in gaps:
                band = g1 - g0
                where = "bottom" if g1 >= SLIDE_H - 0.1 else ("top" if g0 <= 0.1 else "middle")
                # A cover/divider is deliberately top- or bottom-weighted; only
                # flag dead space on content slides.
                if band > SLIDE_H * 0.25 and slide_no(slide) > 1:
                    flag(slide, "dead-band",
                         f"{band:.1f}cm empty {where} band ({band/SLIDE_H*100:.0f}% of slide height)")

        # R5 overlap (text-bearing shapes only, ignore z-ordered backing cards)
        tb = [b for b in bs if b.text.strip() and None not in (b.x,b.y,b.w,b.h)]
        for i in range(len(tb)):
            for j in range(i+1, len(tb)):
                a, c = tb[i], tb[j]
                ox = min(a.x+a.w, c.x+c.w) - max(a.x, c.x)
                oy = min(a.y+a.h, c.y+c.h) - max(a.y, c.y)
                if ox > 0.1 and oy > 0.1:
                    flag(slide, "text-overlap",
                         f"{a.text[:20]!r} and {c.text[:20]!r} overlap {ox:.1f}x{oy:.1f}cm")

        # R6 title-underline — the classic AI tell: a thin bar just under the biggest text
        if texts:
            big = max(texts, key=lambda b: b.size)
            for b in bs:
                if b.text.strip() or None in (b.x,b.y,b.w,b.h): continue
                if b.h <= 0.35 and b.w >= 1.0 and big.y is not None \
                   and 0 <= b.y - (big.y + big.h) <= 1.0:
                    flag(slide, "title-underline",
                         f"{b.h:.2f}cm bar sits under the title — reads as AI filler")

        # R7 dark-on-dark across separate shapes (what `view issues` cannot see)
        fills = [b for b in bs if b.fill and not b.text.strip() and None not in (b.x,b.y,b.w,b.h)]
        for t in texts:
            if t.color is None or None in (t.x,t.y,t.w,t.h): continue
            tb_ = brightness(t.color)
            if tb_ is None: continue
            for f in fills:
                fb = brightness(f.fill)
                if fb is None or f.z > t.z: continue
                inside = (f.x-0.2 <= t.x and f.y-0.2 <= t.y
                          and f.x+f.w+0.2 >= t.x+t.w and f.y+f.h+0.2 >= t.y+t.h)
                if inside and fb < 0.30 and tb_ < 0.80:
                    flag(slide, "low-contrast",
                         f"text {t.color} ({tb_*100:.0f}%) on backing fill {f.fill} ({fb*100:.0f}%)")

        # R8 notes-missing
        if slide not in notes and slide_no(slide) > 1 and texts:
            flag(slide, "notes-missing", "content slide has no speaker notes")

    # R9 font-count (deck-level)
    if len(fonts_all) > 2:
        out.append({"slide": 0, "rule": "font-count",
                    "message": f"{len(fonts_all)} font families in deck: {sorted(fonts_all)} (max 2)"})
    return out

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("usage: deck_lint.py <dump.json> [--json]", file=sys.stderr); return 1
    try:
        bp = json.load(open(args[0], encoding="utf-8"))
    except Exception as e:
        print(f"could not scan {args[0]}: {e}", file=sys.stderr); return 1
    findings = lint(bp)
    if "--json" in sys.argv:
        print(json.dumps(findings, indent=2, ensure_ascii=False))
    else:
        for f in sorted(findings, key=lambda f: (f["slide"], f["rule"])):
            where = f"slide {f['slide']}" if f["slide"] else "deck"
            print(f"{where}: [{f['rule']}] {f['message']}", file=sys.stderr)
        print(f"\n{len(findings)} finding(s)", file=sys.stderr)
    return 2 if findings else 0

if __name__ == "__main__":
    sys.exit(main())
