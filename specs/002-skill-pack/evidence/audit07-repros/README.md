# Audit 07 repros (in-set adversarial pass, re-run by the auditor on LibreOffice 24.2.7.2)

Run from the root of a keyline checkout, with its venv:

    mkdir -p /tmp/keyline-audit07 && cp *.py /tmp/keyline-audit07/
    .venv/bin/python /tmp/keyline-audit07/f1_right.py      # FX-32: ink right of the last glyph's advance (numeral, side region)
    .venv/bin/python /tmp/keyline-audit07/f2_backslash.py  # FX-33: no break before "\" (f2_detail.py shows the lines; probe_b.py <family> probes characters)
    .venv/bin/python /tmp/keyline-audit07/f3_ignorable.py  # FX-34: kerning across ZWNJ/ZWJ (f3_width.py measures one line)

What held: b26_boundary.py (600 renders at the numeral-set boundary), b26_bypass.py (74/74
refusals, NFC and NFD), sweep.py (198 descender and punctuation texts at the limit).
Also: this checkout's measure_lo.py and fit_stress.py outputs on 24.2.7.2, and the one
pytest failure here (FX-35: the Thai fallback font here is Loma, hhea 1.589 em > 1.52).
