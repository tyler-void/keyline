#!/usr/bin/env bash
# Golden fixture source: editorial rebuild with its true defects fixed (spec 001 §8): bottom block re-spaced, l3 label color CC3322.
set -e
F="${1:-editorial-fixed.pptx}"
rm -f "$F"
officecli create "$F" >/dev/null
officecli open "$F" >/dev/null
officecli add "$F" / --type slide --prop layout=blank --prop background=F2F2F0 >/dev/null

# Grid: margin 2.2cm. Content width 29.47cm. Three columns, 0.9cm gutters.
# col_w = (29.47 - 2*0.9)/3 = 9.223  -> x: 2.2, 12.323, 22.446
cat <<'EOF' | officecli batch "$F"
[
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"mark","text":"Slide.Bench","x":"2.2cm","y":"1.25cm","width":"10cm","height":"0.9cm","font":"Arial","size":"15","bold":"true","color":"111111","spacing":"-0.3"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"markdot","preset":"rect","fill":"E8422E","line":"none","x":"5.52cm","y":"1.93cm","width":"0.17cm","height":"0.17cm"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"meta","text":"AUDITING    officecli-pptx v1.0.152","x":"16cm","y":"1.32cm","width":"15.67cm","height":"0.8cm","font":"Arial","size":"10","color":"6E6E68","align":"right","spacing":"1.4","allCaps":"true"}},

 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"rule1","preset":"rect","fill":"111111","line":"none","x":"2.2cm","y":"2.62cm","width":"29.47cm","height":"0.045cm"}},

 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"lead","text":"What a text-only gate cannot see","x":"2.2cm","y":"3.35cm","width":"22cm","height":"1.7cm","font":"Arial","size":"32","bold":"true","color":"111111","spacing":"-0.8"}},

 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"rule2","preset":"rect","fill":"C9C9C2","line":"none","x":"2.2cm","y":"5.85cm","width":"29.47cm","height":"0.025cm"}},

 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"l1","text":"Impeccable","x":"2.2cm","y":"6.35cm","width":"9.22cm","height":"0.8cm","font":"Arial","size":"9.5","color":"6E6E68","spacing":"1.6","allCaps":"true"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"n1","text":"61","x":"2.2cm","y":"7.05cm","width":"9.22cm","height":"3.6cm","font":"Arial","size":"76","bold":"true","color":"111111","spacing":"-2.5"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"d1","text":"deterministic rules, none of them aimed at a slide","x":"2.2cm","y":"10.35cm","width":"8.6cm","height":"2.2cm","font":"Arial","size":"12.5","color":"3A3A36","lineSpacing":"1.25x"}},

 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"v1","preset":"rect","fill":"C9C9C2","line":"none","x":"11.72cm","y":"6.35cm","width":"0.025cm","height":"6.2cm"}},

 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"l2","text":"For .pptx","x":"12.32cm","y":"6.35cm","width":"9.22cm","height":"0.8cm","font":"Arial","size":"9.5","color":"6E6E68","spacing":"1.6","allCaps":"true"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"n2","text":"0","x":"12.32cm","y":"7.05cm","width":"9.22cm","height":"3.6cm","font":"Arial","size":"76","bold":"true","color":"111111","spacing":"-2.5"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"d2","text":"every design rule in both deck skills is prose an agent may ignore","x":"12.32cm","y":"10.35cm","width":"8.6cm","height":"2.2cm","font":"Arial","size":"12.5","color":"3A3A36","lineSpacing":"1.25x"}},

 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"v2","preset":"rect","fill":"C9C9C2","line":"none","x":"21.84cm","y":"6.35cm","width":"0.025cm","height":"6.2cm"}},

 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"l3","text":"Then it stops","x":"22.45cm","y":"6.35cm","width":"9.22cm","height":"0.8cm","font":"Arial","size":"9.5","color":"CC3322","spacing":"1.6","allCaps":"true"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"n3","text":"3","x":"22.45cm","y":"7.05cm","width":"9.22cm","height":"3.6cm","font":"Arial","size":"76","bold":"true","color":"E8422E","spacing":"-2.5"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"d3","text":"fix cycles, then the gate gives up and hands the deck back","x":"22.45cm","y":"10.35cm","width":"8.6cm","height":"2.2cm","font":"Arial","size":"12.5","color":"3A3A36","lineSpacing":"1.25x"}},

 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"rule3","preset":"rect","fill":"111111","line":"none","x":"2.2cm","y":"12.85cm","width":"29.47cm","height":"0.045cm"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"ftlab","text":"Missed on this very deck","x":"2.2cm","y":"13.15cm","width":"12cm","height":"0.8cm","font":"Arial","size":"9.5","color":"6E6E68","spacing":"1.6","allCaps":"true"}},

 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"r1a","text":"slide 2","x":"2.2cm","y":"14.00cm","width":"4cm","height":"0.85cm","font":"Arial","size":"12","color":"6E6E68"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"r1b","text":"dead-band","x":"6cm","y":"14.00cm","width":"8cm","height":"0.85cm","font":"Arial","size":"12","bold":"true","color":"111111"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"r1c","text":"37% of slide height empty","x":"19cm","y":"14.00cm","width":"12.67cm","height":"0.85cm","font":"Arial","size":"12","color":"3A3A36","align":"right"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"hr1","preset":"rect","fill":"DEDED7","line":"none","x":"2.2cm","y":"14.80cm","width":"29.47cm","height":"0.02cm"}},

 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"r2a","text":"slide 4","x":"2.2cm","y":"15.00cm","width":"4cm","height":"0.85cm","font":"Arial","size":"12","color":"6E6E68"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"r2b","text":"dead-band","x":"6cm","y":"15.00cm","width":"8cm","height":"0.85cm","font":"Arial","size":"12","bold":"true","color":"111111"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"r2c","text":"42% of slide height empty","x":"19cm","y":"15.00cm","width":"12.67cm","height":"0.85cm","font":"Arial","size":"12","color":"3A3A36","align":"right"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"hr2","preset":"rect","fill":"DEDED7","line":"none","x":"2.2cm","y":"15.80cm","width":"29.47cm","height":"0.02cm"}},

 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"r3a","text":"slides 2-4","x":"2.2cm","y":"16.00cm","width":"4cm","height":"0.85cm","font":"Arial","size":"12","color":"6E6E68"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"r3b","text":"edge-margin","x":"6cm","y":"16.00cm","width":"8cm","height":"0.85cm","font":"Arial","size":"12","bold":"true","color":"111111"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"r3c","text":"1.20cm against a 1.27cm floor","x":"19cm","y":"16.00cm","width":"12.67cm","height":"0.85cm","font":"Arial","size":"12","color":"3A3A36","align":"right"}},

 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"verdict","preset":"rect","fill":"E8422E","line":"none","x":"2.2cm","y":"16.99cm","width":"0.2cm","height":"0.42cm"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"verdicttx","text":"officecli validate: pass    ·    view issues: 0 found    ·    deck-lint: 6 findings","x":"2.75cm","y":"16.90cm","width":"28.9cm","height":"0.85cm","font":"Arial","size":"11","color":"3A3A36"}},
 {"command":"add","parent":"/slide[1]","type":"notes","props":{"text":"Same three numbers, no cards. Rules and type carry the structure."}}
]
EOF
officecli save "$F" >/dev/null
officecli validate "$F"
officecli view "$F" issues
officecli view "$F" screenshot --page 1 -o "${F%.pptx}.png"
