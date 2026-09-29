# Audit 05 repros (adversarial pass on the pen, re-run by the auditor)

Run from the root of a keyline checkout, with its venv:

    mkdir -p /tmp/keyline-audit05 && cp *.py /tmp/keyline-audit05/
    .venv/bin/python /tmp/keyline-audit05/mkvoices.py      # test-only voices (Times, Calibri, Cambria, Courier)
    .venv/bin/python /tmp/keyline-audit05/attack_fit1.py   # FX-16: whitespace and line breaks
    .venv/bin/python /tmp/keyline-audit05/attack_uax14.py presented neutral evidence keyline:evidence "/"   # FX-17
    .venv/bin/python /tmp/keyline-audit05/attack_table2.py # FX-18: table-cell pitch
    .venv/bin/python /tmp/keyline-audit05/attack_fit2.py   # FX-19: missing glyphs, monospace twin
    .venv/bin/python /tmp/keyline-audit05/attack_ctrl.py   # FX-20: control characters
    .venv/bin/python /tmp/keyline-audit05/attack_label.py  # FX-21: label word cap
    .venv/bin/python /tmp/keyline-audit05/attack_state.py  # FX-22, FX-23

Also attack_crlf.py, attack_dblspace.py, attack_nbsp.py (FX-16), attack_img.py (FX-20) and
attack_next.py (FX-23). h.py converts with soffice under a private profile and reads word
boxes with `pdftotext -bbox` (poppler-utils). The auditor ran them on LibreOffice 24.2.7.2.
They are evidence, not tests: turn each finding into a test in the repo's own style.
