#!/bin/bash
# Adapted from audit 02's stress-corpus/src/lo_autofit.sh: output paths, test photo and the Tyler author only (see _stress.py).
# D18: build the overflowing deck with python-pptx, then let LibreOffice write it.
# Usage: bash lo_autofit.sh [OUT.pptx]   (needs soffice on PATH and python-pptx)
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-$HERE/../d18_lo_autofit.pptx}"
PY="${PYTHON:-python3}"
WORK="$(mktemp -d)"
"$PY" "$HERE/lo_autofit.py" "$WORK/autofit_in.pptx"
(cd "$WORK" && timeout 180 soffice --headless --convert-to pptx --outdir conv autofit_in.pptx)
cp "$WORK/conv/autofit_in.pptx" "$OUT"
"$PY" "$HERE/_stress.py" retag "$OUT"   # LibreOffice writes its own docProps
rm -rf "$WORK"
