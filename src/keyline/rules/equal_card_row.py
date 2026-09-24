from __future__ import annotations

from keyline.geom import contains
from keyline.registry import rule
from keyline.rules._common import cm_emu, is_background, is_text_bearing
from keyline.units import fmt_cm


def _has_text_over(card, slide, cfg) -> bool:
    """P-31: the card carries text, or a text-bearing shape sits inside it, horizontally
    centered within card_center_tolerance of its width."""
    if is_text_bearing(card):
        return True
    tol = cfg.card_center_tolerance * card.box.w
    center2 = 2 * card.box.x + card.box.w  # doubled centers keep integers exact
    for s in slide.shapes:
        if s is card or s.box is None or not is_text_bearing(s):
            continue
        if contains(card.box, s.box) and abs(2 * s.box.x + s.box.w - center2) <= 2 * tol:
            return True
    return False


def _rows(cards, row_tol):
    rows: list[list] = []
    for c in sorted(cards, key=lambda c: (c.box.top, c.box.left, c.z)):
        if rows and abs(c.box.top - rows[-1][0].box.top) <= row_tol:
            rows[-1].append(c)
        else:
            rows.append([c])
    return [sorted(r, key=lambda c: (c.box.left, c.z)) for r in rows]


def _connected(members, slide) -> bool:
    """P-32: connectors whose both ends are members join all members into one component."""
    ids = {m.id for m in members}
    parent = {i: i for i in ids}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for s in slide.shapes:
        if s.kind == "cxnSp" and s.st_cxn in ids and s.end_cxn in ids:
            parent[find(s.st_cxn)] = find(s.end_cxn)
    return len({find(i) for i in ids}) == 1


@rule(
    id="equal-card-row",
    category="slop",
    severity="warning",
    scope="slide",
    basis="geometry",
    since="0.1.0",
    summary="Three or more equal filled cards in an evenly spaced row, each with text",
    rationale="L-004",
)
def check(deck, cfg):
    row_tol = cm_emu(cfg.card_row_tolerance_cm)
    gap_tol = cm_emu(cfg.card_gap_tolerance_cm)
    size_tol = cfg.card_size_tolerance
    min_count = cfg.as_int("card_min_count")
    for slide in deck.slides:
        cards = [
            s
            for s in slide.shapes
            if s.kind == "sp"
            and s.box is not None
            and s.fill != "none"
            and not is_background(s, deck, cfg)
            and _has_text_over(s, slide, cfg)
        ]
        for row in _rows(cards, row_tol):
            i = 0
            while i < len(row):
                first = row[i].box
                run = [row[i]]
                gap0 = None
                for c in row[i + 1 :]:
                    b, prev = c.box, run[-1].box
                    gap = b.left - prev.right
                    same = (
                        abs(b.w - first.w) <= size_tol * first.w
                        and abs(b.h - first.h) <= size_tol * first.h
                    )
                    if not same or gap < 0:
                        break
                    if gap0 is None:
                        gap0 = gap
                    elif abs(gap - gap0) > gap_tol:
                        break
                    run.append(c)
                if len(run) >= min_count and not _connected(run, slide):
                    yield check.finding(
                        slide.index,
                        run[0],
                        f"{len(run)} equal cards in a row ({fmt_cm(first.w)} × "
                        f"{fmt_cm(first.h)} cm, gaps {fmt_cm(gap0)} cm), each with text",
                        measured=len(run),
                        threshold=min_count,
                    )
                i += len(run) if len(run) >= min_count else 1
