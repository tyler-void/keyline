"""FX-22/23: random verb sequences with refusals. After each refused verb, the builder's and
the deck's full __dict__ must equal the snapshot before it; save() must equal a replay of
only the accepted calls (byte-identical, §6.5)."""
import copy, random, sys, hashlib
from pathlib import Path
from PIL import Image
from keyline.pen import Deck, PenError, DoesNotFit
W = Path("/tmp/keyline-audit06")
ev = W / "ev-txn.toml"
ev.write_text('''schema = 1
[product]
name = "Txn"
fictional = true
disclosure = "Fictional product for a test"
[[evidence]]
id = "v1"
label = "a value"
source = "Source one"
value = "42%"
[[evidence]]
id = "v2"
label = "long value"
source = "Source two"
value = "1,234,567,890,123,456,789"
[[evidence]]
id = "s1"
label = "series"
source = "Source three"
series = [["a", 1], ["b", 2], ["c", 3]]
''')
Image.new("RGB", (40, 30), "red").save(W / "img.png")
(W / "bad.webp").write_bytes(b"RIFF\x00\x00\x00\x00WEBPVP8 ")
LONG = "word " * 120
def snap(deck):
    def clean(d):
        return {k: v for k, v in d.items() if k not in ("_deck", "_pack", "_template", "_cfg", "_voice", "_evidence", "_brief", "_role", "_brief_slide", "_slides")}
    return copy.deepcopy((clean(deck.__dict__) | {"slides": [clean(b.__dict__) for b in deck._slides]}))
TEXTS = ["Short text", LONG, "a\tb", "Two words", "x" * 300, "ok\nsecond paragraph", "ẩm thực"]
def rand_call(rng, b):
    v = rng.choice(["text", "bullets", "figure", "table", "chart_bar", "image", "source", "note", "notes", "attribution"])
    region = rng.choice(["main", "side", "footer", "title", "nope"])
    t = rng.choice(TEXTS)
    if v == "text": return v, (t,), dict(style=rng.choice(["body", "lede", "label", "numeral"]), region=region)
    if v == "bullets": return v, ([rng.choice(TEXTS) for _ in range(rng.randint(1, 7))],), dict(region=region)
    if v == "figure": return v, (rng.choice(["v1", "v2", "s1", "zz"]),), dict(region=region, accent=rng.choice([True, False, 1]), label=rng.choice([None, "a label", LONG]))
    if v == "table": return v, ([["H1", "H2"]] + [[rng.choice(TEXTS), "c"] for _ in range(rng.randint(1, 12))],), dict(region=region, header=rng.choice([True, False]))
    if v == "chart_bar": return v, (rng.choice(["s1", "v1"]),), dict(region=region, highlight=rng.choice([None, "a", "zz"]))
    if v == "image": return v, (str(W / rng.choice(["img.png", "bad.webp", "missing.png"])),), dict(region=region, alt=rng.choice(["alt", "", "a\tb"]))
    if v == "source": return v, (rng.choice([None, "Our survey", LONG]),), {}
    if v == "note": return v, (rng.choice([None, "A note", LONG]),), {}
    if v == "notes": return v, (rng.choice(TEXTS),), {}
    return v, (rng.choice(["Someone", LONG]),), {}
ROLES = ["cover", "section", "statement", "evidence", "quote", "close"]
bad = 0; import collections; C = collections.Counter()
for seed in range(300):
    rng = random.Random(seed)
    mode = rng.choice(["presented", "read"])
    d = Deck("swiss", mode, rng.choice(["neutral", "field"]), evidence=str(ev))
    log = []
    for _ in range(rng.randint(1, 5)):
        role = rng.choice(ROLES); variant = "figure" if role == "evidence" and rng.random() < .5 else None
        head = rng.choice(["Title", LONG, "Short title here"])
        before = snap(d)
        try:
            b = d.add(role, head, variant=variant); log.append(("add", (role, head), dict(variant=variant)))
        except (PenError, DoesNotFit):
            if snap(d) != before: print("seed", seed, "add() refusal changed state"); bad += 1
            continue
        for _ in range(rng.randint(1, 10)):
            v, a, k = rand_call(rng, b)
            before = snap(d)
            try:
                getattr(b, v)(*a, **k); log.append((v, a, k)); C["ok " + v] += 1
            except (PenError, DoesNotFit) as e:
                C["refused " + v] += 1
                if snap(d) != before:
                    bad += 1; print("seed", seed, v, a[:1], k, "refused but state changed:", e)
            except Exception as e:
                bad += 1; print("seed", seed, v, k, "raised non-PenError", type(e).__name__, e)
    # replay accepted calls
    try:
        d.save(str(W / "txn-a.pptx"))
    except PenError as e:
        print("seed", seed, "save failed", e); bad += 1; continue
    r = Deck("swiss", mode, d._voice.name if d._voice.name in ("neutral", "field") else "neutral", evidence=str(ev))
    cur = None
    for v, a, k in log:
        if v == "add": cur = r.add(*a, **k)
        else: getattr(cur, v)(*a, **k)
    r.save(str(W / "txn-b.pptx"))
    ha = hashlib.sha256((W / "txn-a.pptx").read_bytes()).hexdigest(); hb = hashlib.sha256((W / "txn-b.pptx").read_bytes()).hexdigest()
    if ha != hb: bad += 1; print("seed", seed, "save differs from replay of accepted calls")
print("problems:", bad, sorted(C.items()))
