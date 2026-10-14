"""Run measure_lo.py's own break probe (B-27 item 3) on the 52 characters of the measured
set that no twin has, using fonts that do have them (FreeSerif, DejaVu Sans), plus
controls whose outcome is known. Usage: python probe_unprobed.py <keyline checkout>."""

import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / "tools"))
import measure_lo as m  # noqa: E402

UNPROBED = (
    "2023 2024 2025 2027 2031 2035 2036 2037 2038 203B 203F 2040 2041 2042 2043 2045 2046 "
    "2047 2048 2049 204A 204B 204C 204D 204E 204F 2050 2051 2053 2054 2055 2056 2057 2058 "
    "2059 205A 205B 205C 205D 2061 2062 2063 2064 2066 2067 2068 2069 20B6 20B7 20BB 20BE 20C0"
)
CONTROLS = "()%!" + chr(0x2044) + "[" + chr(0x2019)
CHARS = [chr(int(h, 16)) for h in UNPROBED.split()] + list(CONTROLS)
m.break_chars = lambda: CHARS  # the probe and the report both iterate this

soffice = m.find_soffice()
version = m.libreoffice_version(soffice)
families = ["FreeSerif", "DejaVu Sans"]
decks = {f: m.build_breaks(f) for f in families}
pages = {}
with tempfile.TemporaryDirectory(prefix="kl-unprobed-") as tmp:
    for i, (family, (deck_bytes, probes)) in enumerate(decks.items()):
        got = m.convert(Path(tmp), f"b{i}", deck_bytes, soffice, origins=True)
        assert len(got) == len(probes), (family, len(got), len(probes))
        pages[family] = got
lines, sets = m.break_report(decks, pages, version)
print("\n".join(lines))
