#!/usr/bin/env bash
# Golden fixture source: KPI-card recipe copied from officecli-pptx. Expected to FAIL keyline lint (see specs/001-lint-core/spec.md).
set -e
FILE="${1:-kpi-recipe.pptx}"
rm -f "$FILE"
officecli create "$FILE"
officecli open "$FILE"

# ---------- Slide 1: cover (Midnight Executive) ----------
officecli add "$FILE" / --type slide --prop layout=blank --prop background=1E2761
cat <<'EOF' | officecli batch "$FILE"
[
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"CoverRule","preset":"rect","fill":"CADCFC","line":"none","x":"2cm","y":"6.2cm","width":"3cm","height":"0.18cm"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"CoverTitle","text":"Deck Quality Gate","x":"2cm","y":"7cm","width":"24cm","height":"3cm","font":"Georgia","size":"44","bold":"true","color":"FFFFFF"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"CoverSub","text":"A deterministic linter for AI-generated slides","x":"2cm","y":"10.4cm","width":"24cm","height":"1.4cm","font":"Calibri","size":"20","color":"CADCFC"}},
 {"command":"add","parent":"/slide[1]","type":"shape","props":{"name":"CoverMeta","text":"Tyler · September 2026","x":"2cm","y":"16cm","width":"24cm","height":"1cm","font":"Calibri","size":"14","color":"8899BB"}}
]
EOF

# ---------- Slide 2: KPI cards ----------
officecli add "$FILE" / --type slide --prop layout=blank --prop background=FFFFFF
cat <<'EOF' | officecli batch "$FILE"
[
 {"command":"add","parent":"/slide[2]","type":"shape","props":{"name":"T2","text":"What a text-only gate cannot see","x":"1.5cm","y":"1.2cm","width":"30cm","height":"2cm","font":"Georgia","size":"36","bold":"true","color":"1E2761"}},
 {"command":"add","parent":"/slide[2]","type":"shape","props":{"preset":"roundRect","fill":"1E2761","line":"none","x":"1.5cm","y":"5cm","width":"9.78cm","height":"7cm"}},
 {"command":"add","parent":"/slide[2]","type":"shape","props":{"text":"61","x":"1.5cm","y":"5.8cm","width":"9.78cm","height":"2.8cm","font":"Georgia","size":"60","bold":"true","color":"FFFFFF","align":"center"}},
 {"command":"add","parent":"/slide[2]","type":"shape","props":{"text":"impeccable rules","x":"1.5cm","y":"9cm","width":"9.78cm","height":"0.9cm","font":"Calibri","size":"14","color":"CADCFC","align":"center"}},
 {"command":"add","parent":"/slide[2]","type":"shape","props":{"preset":"roundRect","fill":"1E2761","line":"none","x":"12.04cm","y":"5cm","width":"9.78cm","height":"7cm"}},
 {"command":"add","parent":"/slide[2]","type":"shape","props":{"text":"0","x":"12.04cm","y":"5.8cm","width":"9.78cm","height":"2.8cm","font":"Georgia","size":"60","bold":"true","color":"FFFFFF","align":"center"}},
 {"command":"add","parent":"/slide[2]","type":"shape","props":{"text":"for .pptx today","x":"12.04cm","y":"9cm","width":"9.78cm","height":"0.9cm","font":"Calibri","size":"14","color":"CADCFC","align":"center"}},
 {"command":"add","parent":"/slide[2]","type":"shape","props":{"preset":"roundRect","fill":"B85042","line":"none","x":"22.58cm","y":"5cm","width":"9.78cm","height":"7cm"}},
 {"command":"add","parent":"/slide[2]","type":"shape","props":{"text":"3","x":"22.58cm","y":"5.8cm","width":"9.78cm","height":"2.8cm","font":"Georgia","size":"60","bold":"true","color":"FFFFFF","align":"center"}},
 {"command":"add","parent":"/slide[2]","type":"shape","props":{"text":"fix cycles, then give up","x":"22.58cm","y":"9cm","width":"9.78cm","height":"0.9cm","font":"Calibri","size":"14","color":"FFFFFF","align":"center"}},
 {"command":"add","parent":"/slide[2]","type":"notes","props":{"text":"Screenshot QA is the only visual gate today, and it caps at three rounds."}}
]
EOF

# ---------- Slide 3: chart + commentary ----------
officecli add "$FILE" / --type slide --prop layout=blank --prop background=FFFFFF
officecli add "$FILE" "/slide[3]" --type shape --prop name=T3 --prop text="Where the rules actually live" \
  --prop x=1.5cm --prop y=1.2cm --prop width=30cm --prop height=2cm \
  --prop font=Georgia --prop size=36 --prop bold=true --prop color=1E2761
officecli add "$FILE" "/slide[3]" --type chart --prop chartType=column \
  --prop series1.name="Prose rules" --prop series1.values="38,41,0" --prop series1.color=CADCFC \
  --prop series2.name="Machine-checked" --prop series2.values="0,0,61" --prop series2.color=1E2761 \
  --prop categories="Anthropic pptx,officecli-pptx,impeccable" \
  --prop x=1.5cm --prop y=4.5cm --prop width=20cm --prop height=12.5cm --prop title="Rule count by enforcement"
cat <<'EOF' | officecli batch "$FILE"
[
 {"command":"add","parent":"/slide[3]","type":"shape","props":{"preset":"roundRect","fill":"F5F7FA","line":"none","x":"22.5cm","y":"4.5cm","width":"9.87cm","height":"12.5cm"}},
 {"command":"add","parent":"/slide[3]","type":"shape","props":{"text":"Key insight","x":"23cm","y":"5.2cm","width":"8.9cm","height":"1.2cm","font":"Georgia","size":"20","bold":"true","color":"1E2761"}},
 {"command":"add","parent":"/slide[3]","type":"shape","props":{"text":"Both deck skills carry rich design guidance and zero enforcement. Impeccable has the enforcement and none of it targets slides.","x":"23cm","y":"6.8cm","width":"8.9cm","height":"9cm","font":"Calibri","size":"18","color":"333333"}},
 {"command":"add","parent":"/slide[3]","type":"notes","props":{"text":"The gap is the product."}}
]
EOF

# ---------- Slide 4: flow ----------
officecli add "$FILE" / --type slide --prop layout=blank --prop background=FFFFFF
cat <<'EOF' | officecli batch "$FILE"
[
 {"command":"add","parent":"/slide[4]","type":"shape","props":{"name":"T4","text":"The loop","x":"1.5cm","y":"1.2cm","width":"30cm","height":"2cm","font":"Georgia","size":"36","bold":"true","color":"1E2761"}},
 {"command":"add","parent":"/slide[4]","type":"shape","props":{"name":"S1","preset":"roundRect","fill":"1E2761","line":"none","x":"1.5cm","y":"8cm","width":"6cm","height":"3cm","text":"officecli edit","font":"Calibri","size":"18","bold":"true","color":"FFFFFF","align":"center","valign":"middle"}},
 {"command":"add","parent":"/slide[4]","type":"shape","props":{"name":"S2","preset":"roundRect","fill":"CADCFC","line":"none","x":"9.79cm","y":"8cm","width":"6cm","height":"3cm","text":"dump to JSON","font":"Calibri","size":"18","bold":"true","color":"1E2761","align":"center","valign":"middle"}},
 {"command":"add","parent":"/slide[4]","type":"shape","props":{"name":"S3","preset":"roundRect","fill":"1E2761","line":"none","x":"18.08cm","y":"8cm","width":"6cm","height":"3cm","text":"deck-lint","font":"Calibri","size":"18","bold":"true","color":"FFFFFF","align":"center","valign":"middle"}},
 {"command":"add","parent":"/slide[4]","type":"shape","props":{"name":"S4","preset":"roundRect","fill":"B85042","line":"none","x":"26.37cm","y":"8cm","width":"6cm","height":"3cm","text":"hook feeds agent","font":"Calibri","size":"18","bold":"true","color":"FFFFFF","align":"center","valign":"middle"}},
 {"command":"add","parent":"/slide[4]","type":"notes","props":{"text":"Deterministic findings return to the model before the deck is declared done."}}
]
EOF
for pair in "S1 S2" "S2 S3" "S3 S4"; do
  A=${pair% *}; B=${pair#* }
  officecli add "$FILE" "/slide[4]" --type connector \
    --prop "from=/slide[4]/shape[@name=$A]" --prop "to=/slide[4]/shape[@name=$B]" \
    --prop shape=elbow --prop color=333333 --prop tailEnd=triangle
done

officecli save "$FILE"
echo "=== validate ==="
officecli validate "$FILE" || true
echo "=== issues ==="
officecli view "$FILE" issues || true
