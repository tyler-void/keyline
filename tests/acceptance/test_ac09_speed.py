"""AC-9: linting kpi-recipe.pptx takes under 1 s wall time, interpreter start included.
Judged on the minimum of 3 whole-process runs; all three are printed (A-19)."""

import subprocess
import sys
import time

from tests.conftest import GOLDEN

BUDGET_S = 1.0


def test_kpi_lint_under_one_second():
    cmd = [sys.executable, "-m", "keyline", "lint", str(GOLDEN / "kpi-recipe.pptx"), "--json"]
    subprocess.run(cmd, capture_output=True)  # warm the filesystem cache once
    timings = []
    for _ in range(3):
        start = time.perf_counter()
        proc = subprocess.run(cmd, capture_output=True)
        timings.append(time.perf_counter() - start)
        assert proc.returncode == 2
    print(f"kpi-recipe lint wall times: {', '.join(f'{t:.3f}s' for t in timings)}")
    assert min(timings) < BUDGET_S, timings  # A-19
