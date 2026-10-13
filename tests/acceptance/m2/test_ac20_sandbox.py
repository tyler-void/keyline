"""Spec 002 AC-20 (task T-44; Q-55 as ruled; audit 07 §4.5): the sandbox smoke. In a fresh
venv with only lxml, Pillow and python-pptx (pinned to 1.0.2 through constraints.txt;
keyline itself not installed), with `dist/keyline.zip` unpacked to a temp dir outside the
repository:
- `kl.py doctor` exits 0 and prints the python-pptx version;
- `kl.py run` builds the specimens from the `fixtures/packs/` layout, with keyline
  imported from the skill's `lib/`;
- `kl.py check` on each specimen with its brief exits 0.
This stands in for the claude.ai sandbox. The test scrubs PYTHONPATH and runs from a
working directory outside the repository. Without network it skips locally and fails in
CI."""

import importlib.util
import os
import shutil
import subprocess
import sys
import venv
import zipfile

import pytest

from tests.conftest import FIXTURES, ROOT

STEMS = (
    "swiss-specimen-presented-neutral",
    "swiss-specimen-presented-night",
    "swiss-specimen-read-field",
)
PACKAGES = ("lxml", "Pillow", "python-pptx")


def _run(args, cwd, env):
    return subprocess.run([str(a) for a in args], cwd=cwd, env=env, capture_output=True, text=True)


@pytest.fixture(scope="module")
def sandbox(tmp_path_factory):
    """(python of the venv, the unpacked skill folder, a working folder, the environment)."""
    spec = importlib.util.spec_from_file_location("build_skill", ROOT / "tools/build_skill.py")
    build_skill = importlib.util.module_from_spec(spec)
    sys.modules["build_skill"] = build_skill
    spec.loader.exec_module(build_skill)

    base = tmp_path_factory.mktemp("sandbox")
    assert ROOT not in base.parents and base != ROOT
    package = build_skill.build(base / "keyline.zip")
    with zipfile.ZipFile(package) as z:
        z.extractall(base / "skills")
    skill = base / "skills" / "keyline"

    venv.EnvBuilder(with_pip=True, system_site_packages=False).create(base / "venv")
    python = base / "venv" / ("Scripts" if os.name == "nt" else "bin") / "python"
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME")}
    env["PYTHONNOUSERSITE"] = "1"
    install = _run(
        [python, "-m", "pip", "install", "--quiet", "--disable-pip-version-check",
         "-c", ROOT / "constraints.txt", *PACKAGES],
        base, env,
    )  # fmt: skip
    if install.returncode != 0:
        why = f"pip could not install {', '.join(PACKAGES)}: {install.stderr.strip()[-300:]}"
        if os.environ.get("CI"):
            pytest.fail(why)  # Q-55: skip without network locally, fail in CI
        pytest.skip(why)

    work = base / "work"
    (work / "packs" / "src").mkdir(parents=True)
    shutil.copy(FIXTURES / "packs" / "src" / "build_specimens.py", work / "packs" / "src")
    for path in (FIXTURES / "packs").glob("*.toml"):  # build_specimens.py reads parents[1]
        shutil.copy(path, work / "packs")
    return python, skill, work, env


def test_only_the_three_packages_are_installed(sandbox):
    python, _skill, work, env = sandbox
    code = (
        "import importlib.metadata as m, importlib.util as u\n"
        "print(m.version('python-pptx'), m.version('lxml'), m.version('Pillow'))\n"
        "print(u.find_spec('keyline'))\n"
    )
    proc = _run([python, "-c", code], work, env)
    assert proc.returncode == 0, proc.stderr
    versions, keyline = proc.stdout.strip().splitlines()
    assert versions.split()[0] == "1.0.2"  # the constraint
    assert keyline == "None"  # keyline is not installed: only the skill's lib has it
    print(f"AC-20 sandbox: python-pptx, lxml, Pillow = {versions}")  # -rP shows it in CI


def test_doctor_exits_zero_and_prints_the_python_pptx_version(sandbox):
    python, skill, work, env = sandbox
    proc = _run([python, skill / "scripts" / "kl.py", "doctor"], work, env)
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout + proc.stderr
    assert "PPTX_OK" in out and "python-pptx 1.0.2" in out
    assert "PYTHON_OK" in out and "LXML_OK" in out and "PILLOW_OK" in out


def test_keyline_is_imported_from_the_skills_lib(sandbox):
    python, skill, work, env = sandbox
    script = work / "where.py"
    script.write_text(
        "import sys\nimport keyline\nprint(keyline.__file__)\nprint(sys.argv)\nprint(__name__)\n",
        encoding="utf-8",
    )
    proc = _run([python, skill / "scripts" / "kl.py", "run", script, "one", "two"], work, env)
    assert proc.returncode == 0, proc.stderr
    where, argv, name = proc.stdout.strip().splitlines()
    assert where.startswith(str(skill / "lib" / "keyline"))
    assert argv == str([str(script), "one", "two"]) and name == "__main__"


def test_the_specimens_build_and_pass_check(sandbox):
    python, skill, work, env = sandbox
    kl = skill / "scripts" / "kl.py"
    out = work / "out"
    built = _run([python, kl, "run", work / "packs" / "src" / "build_specimens.py", out], work, env)
    assert built.returncode == 0, built.stderr
    for stem in STEMS:
        deck = out / f"{stem}.pptx"
        assert deck.stat().st_size > 20_000, stem
        check = _run(
            [python, kl, "check", deck, "--brief", work / "packs" / f"{stem}.brief.toml",
             "-o", work / "render" / stem],
            work, env,
        )  # fmt: skip
        assert check.returncode == 0, f"{stem}: {check.stderr[-600:]}"
