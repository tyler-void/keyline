"""Evidence series values the loader accepts (TOML nan, inf, an empty series, a huge int):
does chart_bar refuse them at the verb (PenError), and do save(), lint and officecli
validate stay clean?"""
import subprocess, sys, json
from pathlib import Path
from keyline.pen import Deck, PenError
W = Path("/tmp/keyline-audit06")
ev = W / "ev-chart.toml"
ev.write_text('''schema = 1
[product]
name = "Chart attack"
fictional = false

[[evidence]]
id = "nan"
label = "nan series"
source = "test"
series = [["a", 1], ["b", nan], ["c", 3]]

[[evidence]]
id = "inf"
label = "inf series"
source = "test"
series = [["a", 1], ["b", inf], ["c", -inf]]

[[evidence]]
id = "empty"
label = "empty series"
source = "test"
series = []

[[evidence]]
id = "huge"
label = "huge series"
source = "test"
series = [["a", 1], ["b", 1_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000]]
''')
for eid in ("nan", "inf", "empty", "huge"):
    for mode in ("presented",):
        try:
            d = Deck("swiss", mode, "neutral", evidence=str(ev))
        except PenError as e:
            print(eid, "Deck refused:", e); break
        try:
            d.add("evidence", "Chart").chart_bar(eid).source()
        except PenError as e:
            print(f"{eid}: chart_bar refused (PenError): {e}"); continue
        except Exception as e:
            print(f"{eid}: chart_bar raised {type(e).__name__} (not PenError): {e}"); continue
        out = W / f"chart-{eid}.pptx"
        try:
            d.save(str(out))
        except PenError as e:
            print(f"{eid}: accepted by chart_bar, save() failed: {e}"); continue
        lint = subprocess.run([".venv/bin/keyline", "lint", str(out), "--pack", "swiss", "--voice", "neutral", "--mode", mode, "--format", "json"], capture_output=True, text=True)
        try:
            fs = json.loads(lint.stdout)["findings"]
            errs = [f for f in fs if f["severity"] == "error"]
        except Exception:
            errs = lint.stdout[-300:] + lint.stderr[-300:]
        val = subprocess.run(["officecli", "validate", str(out), "--json"], capture_output=True, text=True)
        print(f"{eid}: accepted and saved; lint exit {lint.returncode} errors={errs}; validate: {val.stdout.strip()[:300]}")
