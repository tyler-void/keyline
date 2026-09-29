"""Running an engine process: LibreOffice, OfficeCLI, pdftoppm (amendments B-13, B-19).

Every engine call goes through `run()`:
- the child gets a process group of its own, so killing it also kills what it started
  (soffice's soffice.bin, the npm launcher's native officecli);
- a timeout, or any exception while waiting (a SIGINT or SIGTERM turned into
  `Interrupted`), kills the whole group before it propagates;
- output is decoded as UTF-8 with replacement, so an engine's odd bytes never crash
  keyline.

`interruptible()` turns SIGINT and SIGTERM into `Interrupted` for the length of a
command, so the `finally` blocks that close OfficeCLI copies and remove temp directories
run; the CLI then exits 130 or 143.
"""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import threading
from collections.abc import Iterator

TERMINATING = (signal.SIGINT, signal.SIGTERM)


class Interrupted(BaseException):
    """A SIGINT or SIGTERM arrived. A BaseException, so `except Exception` cleanup code
    cannot swallow it."""

    def __init__(self, signum: int) -> None:
        super().__init__(signum)
        self.signum = signum

    @property
    def exit_code(self) -> int:
        return 128 + self.signum


def _kill_group(proc: subprocess.Popen) -> None:
    if os.name == "posix":
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(proc.pid, signal.SIGKILL)
    else:
        proc.kill()


def run(cmd: list[str], timeout: float) -> subprocess.CompletedProcess:
    """Run `cmd` in its own process group; raise TimeoutExpired after `timeout` s. On a
    timeout or an interruption the whole group is killed first."""
    group = (
        {"start_new_session": True}
        if os.name == "posix"
        else {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    )
    with subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
        **group,
    ) as proc:
        try:
            out, err = proc.communicate(timeout=timeout)
        except BaseException:
            _kill_group(proc)
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.communicate(timeout=10)
            raise
    return subprocess.CompletedProcess(cmd, proc.returncode, out, err)


@contextlib.contextmanager
def interruptible() -> Iterator[None]:
    """SIGINT and SIGTERM raise `Interrupted` inside the block. After the first one, both
    are ignored, so a second signal cannot cut the cleanup short."""
    if threading.current_thread() is not threading.main_thread():
        yield
        return

    def handler(signum, frame):
        for sig in TERMINATING:
            signal.signal(sig, signal.SIG_IGN)
        raise Interrupted(signum)

    previous = {sig: signal.getsignal(sig) for sig in TERMINATING}
    for sig in TERMINATING:
        signal.signal(sig, handler)
    try:
        yield
    finally:
        for sig, old in previous.items():
            signal.signal(sig, old)
