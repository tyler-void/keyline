"""Spec 002 §8.1 (task T-33; audit 07 §4.5): `skill/keyline/scripts/kl.py` finds the skill
through its own location, puts `<skill>/lib` first on the import path when that folder
exists (the packaged skill), and otherwise uses the installed keyline. `kl.py <args>`
is the keyline CLI, exit code included; `kl.py run SCRIPT.py [ARGS]` runs a build script
as `__main__` with `sys.argv` set."""

import json
import re
import shutil
import subprocess
import sys

import pytest

from tests.conftest import FIXTURES, ROOT

KL = ROOT / "skill" / "keyline" / "scripts" / "kl.py"


def kl(*args, script=KL, cwd=None):
    return subprocess.run(
        [sys.executable, str(script), *map(str, args)], capture_output=True, text=True, cwd=cwd
    )


def test_it_is_the_keyline_cli():
    proc = kl("rules", "--json")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert len(data["rules"] if isinstance(data, dict) else data) == 35


def test_exit_codes_pass_through(tmp_path):
    assert kl("lint", tmp_path / "missing.pptx").returncode == 1  # could not scan
    assert kl("lint", FIXTURES / "golden" / "kpi-recipe.pptx").returncode == 2  # findings
    assert kl("doctor").returncode == 0
    none = kl()
    assert none.returncode == 1 and "usage" in none.stderr.lower()


def test_run_executes_a_script_as_main(tmp_path):
    script = tmp_path / "build.py"
    script.write_text(
        "import sys\n"
        "import helper\n"
        "import keyline\n"
        "print(__name__, sys.argv[1:], helper.VALUE, keyline.__name__)\n"
        "if __name__ == '__main__':\n"
        "    sys.exit(3)\n",
        encoding="utf-8",
    )
    (tmp_path / "helper.py").write_text("VALUE = 'beside the script'\n", encoding="utf-8")
    proc = kl("run", script, "out.pptx", "--flag", cwd=tmp_path.parent)
    assert proc.returncode == 3, proc.stderr
    assert proc.stdout.strip() == "__main__ ['out.pptx', '--flag'] beside the script keyline"


def test_run_builds_a_deck_with_the_pen(tmp_path):
    pytest.importorskip("pptx")
    script = tmp_path / "build.py"
    script.write_text(
        "import sys\n"
        "from keyline.pen import Deck\n"
        "d = Deck(pack='swiss', mode='presented', voice='neutral')\n"
        "d.add('cover', 'A deck from kl.py run')\n"
        "d.save(sys.argv[1], author='Tyler')\n",
        encoding="utf-8",
    )
    proc = kl("run", script, tmp_path / "deck.pptx")
    assert proc.returncode == 0, proc.stderr
    assert (tmp_path / "deck.pptx").stat().st_size > 10_000


def test_run_prints_a_refusal_as_one_line(tmp_path):
    """When the pen refuses, `run` prints the script's line and the refusal, and exits 1;
    an error of the script's own keeps its traceback."""
    pytest.importorskip("pptx")
    script = tmp_path / "build.py"
    script.write_text(
        "from keyline.pen import Deck\n"
        "d = Deck(pack='swiss', mode='presented', voice='neutral')\n"
        "s = d.add('evidence', 'A headline')\n"
        "s.text('word ' * 400)\n",
        encoding="utf-8",
    )
    proc = kl("run", script)
    assert proc.returncode == 1
    (line,) = proc.stderr.splitlines()
    assert re.fullmatch(
        r"kl\.py: build\.py:4: DoesNotFit: text needs \d+ lines, region holds \d+.*", line
    )
    script.write_text("raise ValueError('the script itself is wrong')\n", encoding="utf-8")
    proc = kl("run", script)
    assert proc.returncode == 1 and "Traceback" in proc.stderr
    assert proc.stderr.rstrip().endswith("ValueError: the script itself is wrong")


def test_run_needs_a_script(tmp_path):
    for args in (("run",), ("run", tmp_path / "missing.py")):
        proc = kl(*args)
        assert proc.returncode == 1 and proc.stderr.startswith("kl.py: ")


def test_lib_takes_precedence_over_the_installed_package(tmp_path):
    """The packaged skill: a `lib/` beside `scripts/` wins, for the CLI and for `run`."""
    skill = tmp_path / "keyline"
    (skill / "scripts").mkdir(parents=True)
    shutil.copy(KL, skill / "scripts" / "kl.py")
    stub = skill / "lib" / "keyline"
    stub.mkdir(parents=True)
    (stub / "__init__.py").write_text("WHERE = 'lib'\n", encoding="utf-8")
    (stub / "cli.py").write_text(
        "def main(argv):\n    print('stub', argv)\n    return 7\n", encoding="utf-8"
    )
    proc = kl("doctor", "--json", script=skill / "scripts" / "kl.py")
    assert (proc.returncode, proc.stdout.strip()) == (7, "stub ['doctor', '--json']")
    script = tmp_path / "where.py"
    script.write_text("import keyline\nprint(keyline.WHERE, keyline.__file__)\n", encoding="utf-8")
    proc = kl("run", script, script=skill / "scripts" / "kl.py")
    assert proc.returncode == 0, proc.stderr
    where, file = proc.stdout.split()
    assert where == "lib" and file.startswith(str(stub))
