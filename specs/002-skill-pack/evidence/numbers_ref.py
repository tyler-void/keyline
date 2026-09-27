"""Auditor's reference implementation of spec 002 §4.4 numeric tokens (2026-09-27).

An oracle for tests, not production code. It returns (token, significant) pairs.
"""
import re
import unicodedata
CORE = re.compile(r"\d+(?:[.,]\d+)*")
CUR = "$€£¥₫"; SIGNS = "-−+"
def tokens(text):
    t = unicodedata.normalize("NFC", text); out = []; pos = 0
    for m in CORE.finditer(t):
        s, e = m.span()
        # skip cores that are glued to a previous core via [.,] (maximal match already handles)
        pre = ""; i = s
        if i > 0 and t[i-1] in CUR:
            pre = t[i-1]; i -= 1
        if i > 0 and t[i-1] in SIGNS and (i-1 == 0 or not t[i-2].isalnum()):
            pre = ("-" if t[i-1] == "−" else t[i-1]) + pre
        suf = ""; j = e
        if j < len(t) and t[j] in "%×": suf = t[j]
        elif j + 1 < len(t) and t[j] == " " and t[j+1] in "%×": suf = t[j+1]
        else:
            for sx in ("bn", "k", "K", "M", "B", "x"):
                if t.startswith(sx, j) and not (j + len(sx) < len(t) and t[j+len(sx)].isalpha()):
                    suf = sx; break
        core = m.group()
        digits = sum(c.isdigit() for c in core)
        year = (not pre and not suf and len(core) == 4 and core.isdigit() and 1900 <= int(core) <= 2099)
        sig = (bool(pre) or bool(suf) or digits >= 2) and not year
        out.append((pre + core + suf, sig))
    return out
