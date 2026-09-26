import subprocess
import sys

from keyline import __version__


def test_version_flag():
    out = subprocess.run(
        [sys.executable, "-m", "keyline", "--version"], capture_output=True, text=True, check=True
    )
    assert out.stdout.strip() == __version__ == "0.1.0"
