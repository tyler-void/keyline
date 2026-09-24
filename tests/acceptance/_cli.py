import subprocess
import sys


def keyline(*args, env=None):
    return subprocess.run(
        [sys.executable, "-m", "keyline", *map(str, args)],
        capture_output=True,
        env=env,
    )
