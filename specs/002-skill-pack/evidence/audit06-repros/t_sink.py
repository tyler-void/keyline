"""B-23 invariant: legal pen calls with unusual but accepted characters; lint (error-level)
and officecli validate."""
import subprocess, sys, json
from pathlib import Path
from PIL import Image
from keyline.pen import Deck, PenError
W = Path("/tmp/keyline-audit06")
ev = W / "ev-sink.toml"
ev.write_text('''schema = 1
[product]
name = "Sink"
fictional = true
disclosure = "Fictional \\ufdd0 product"

[[evidence]]
id = "v1"
label = "odd \\U0010FFFF label"
source = "src \\U0001FFFE"
value = "42\\ufe0f"

[[evidence]]
id = "s1"
label = "series"
source = "s"
series = [["\\u202eabc", 1], ["\\U0001F469\\u200d\\U0001F4BB", 2], ["\\ue000", 3]]
''')
Image.new("RGB", (40, 30), "red").save(W / "img.png")
ODD = ["﷐", "\U0001fffe", "\U0010ffff", "", "‮", "⁦", "‎", "️", "‍", "͏", "᠎", "⁡", "\U000e0001", "\U000e0041", "_x0041_", "]]>", "\u0085"[:0]]
sink = " ".join(f"w{c}w" for c in ODD)
for mode in ("presented", "read"):
    for voice in ("neutral", "field", "night"):
        d = Deck("swiss", mode, voice, evidence=str(ev))
        log = []
        def tryit(label, f):
            try: f(); log.append(f"ok {label}")
            except (PenError, ValueError) as e: log.append(f"REFUSED {label}: {type(e).__name__}: {str(e)[:90]}")
        tryit("cover", lambda: d.add("cover", "Cover " + sink, notes="n " + sink).text("lede " + sink, style="lede").note())
        tryit("section", lambda: d.add("section", "Sec" + sink).text("lab " + ODD[0], style="label"))
        tryit("statement", lambda: d.add("statement", "St " + sink).figure("v1").source("src " + sink))
        tryit("evidence table", lambda: d.add("evidence", "Ev " + sink).table([["h‮", "h2"], [sink, "\U0010ffff"]]).source("s " + sink))
        tryit("evidence chart", lambda: d.add("evidence", "Ch", variant="figure").chart_bar("s1", highlight="‮abc").image(str(W / "img.png"), "side", alt="alt " + sink).source())
        tryit("quote", lambda: d.add("quote", "Q " + sink).attribution("A ﷐"))
        tryit("close", lambda: d.add("close", "Close").text("x " + sink, style="lede").note())
        out = W / f"sink-{mode}-{voice}.pptx"
        try:
            d.save(str(out), author="Tyler \U0010ffff")
        except PenError as e:
            print(mode, voice, "save failed", e); continue
        lint = subprocess.run([".venv/bin/keyline", "lint", str(out), "--pack", "swiss", "--voice", voice, "--mode", mode, "--json"], capture_output=True, text=True)
        try:
            fs = json.loads(lint.stdout)["findings"]
            errs = [(f["rule"], f.get("message")) for f in fs if f["severity"] == "error"]
            rules = sorted({f["rule"] + ":" + f["severity"] for f in fs})
        except Exception as e:
            errs = ("unparsed", lint.stdout[-300:], lint.stderr[-500:]); rules = []
        val = subprocess.run(["officecli", "validate", str(out)], capture_output=True, text=True)
        print(mode, voice, [l for l in log if l.startswith("REFUSED")], "| lint exit", lint.returncode, "errors", errs, rules, "| validate:", (val.stdout + val.stderr).strip().splitlines()[-1:] )
