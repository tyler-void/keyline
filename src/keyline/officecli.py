"""Running OfficeCLI safely (spec 002 amendment B-14, lesson L-016).

`officecli validate` and `officecli view … screenshot` start a resident process that keeps
the document in memory for about 60 s, and a second call on the same path reads that
memory, not the file. So keyline never passes the user's deck to OfficeCLI: every call
works on a private copy with a unique name, `officecli close` releases the copy in a
`finally`, and the copy is deleted.
"""

from __future__ import annotations

import contextlib
import shutil
import subprocess
import tempfile
import uuid
from collections.abc import Iterator
from pathlib import Path

CLOSE_TIMEOUT_S = 30


@contextlib.contextmanager
def private_copy(deck: str | Path) -> Iterator[Path]:
    """A copy of `deck` under a fresh temp directory, released and deleted on exit."""
    tmp = Path(tempfile.mkdtemp(prefix="keyline-oc-"))
    copy = tmp / f"deck-{uuid.uuid4().hex}{Path(deck).suffix or '.pptx'}"
    try:
        shutil.copyfile(deck, copy)
        yield copy
    finally:
        exe = shutil.which("officecli")
        if exe is not None:
            with contextlib.suppress(OSError, subprocess.TimeoutExpired):
                subprocess.run(
                    [exe, "close", str(copy)], capture_output=True, timeout=CLOSE_TIMEOUT_S
                )
        shutil.rmtree(tmp, ignore_errors=True)
