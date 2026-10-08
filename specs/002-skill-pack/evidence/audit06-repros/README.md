# Audit 06 repros (adversarial pass on the A2 fixes, re-run by the auditor)

Run from the root of a keyline checkout, with its venv:

    mkdir -p /tmp/keyline-audit06 && cp *.py /tmp/keyline-audit06/
    .venv/bin/python /tmp/keyline-audit06/t_top.py      # FX-25: tall Vietnamese capitals, top edge (also t_top2.py, t_tabletop.py)
    .venv/bin/python /tmp/keyline-audit06/t_kern.py     # FX-26: positive kerning (kern.py lists the pairs)
    .venv/bin/python /tmp/keyline-audit06/t_break.py    # FX-27: no break after opening punctuation + space (also t_misc.py)
    .venv/bin/python /tmp/keyline-audit06/t_table.py    # FX-28: CJK in table cells (24.2)
    .venv/bin/python /tmp/keyline-audit06/t_ctl.py      # FX-29: Hebrew in the CTL font slot
    .venv/bin/python /tmp/keyline-audit06/t_chart.py    # FX-30: chart series checked late
    .venv/bin/python /tmp/keyline-audit06/t_misc.py     # box drawing (outside the measured set), invisible-only text

hx.py builds test-only voices, converts with soffice under a private profile and measures
ink against a control slide at 1280 px. The auditor ran these on LibreOffice 24.2.7.2.
t_txn.py and t_sink.py are what held (transactions, lint and validate on kitchen-sink decks).
Also here: this checkout's measure_lo.py and fit_stress.py outputs on 24.2.7.2.
