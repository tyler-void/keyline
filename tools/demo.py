"""Set up and record the BonsaiHub demo (spec 002 §10; task T-46; plan Q-58 as ruled;
audit 07 §4.7).

The two demo decks are built by a fresh Claude Code session, in a directory outside the
keyline checkout, with the skill installed from `dist/keyline.zip`. This tool does the
parts around that session:

    python tools/demo.py setup DIR       # before: make DIR ready for the fresh session
    python tools/demo.py record DIR      # after: print what audit 07 asks to record
    python tools/demo.py collect DIR     # after G-2a: copy the outputs into examples/bonsaihub/

`setup` refuses a DIR inside the checkout or one that is not empty. It unpacks the skill
into DIR/.claude/skills/keyline, copies `product.toml` to DIR/examples/bonsaihub/ (the
prompts P-1 and P-2 name that path), and makes DIR/.venv with lxml, Pillow and
python-pptx (pinned by constraints.txt) and pypdfium2 for the preview, without keyline.
It writes DIR/SETUP.json: the zip's SHA-256 and the files it put there.

`record` prints the working directory, the skill path, the zip's SHA-256, where keyline
imports from in DIR's venv, and the SHA-256 of every file the session wrote (everything
under DIR that `setup` did not put there, without .venv and the skill).

`collect` copies the demo's outputs, and nothing else, into examples/bonsaihub/.
Dev only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import venv
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "dist" / "keyline.zip"
PRODUCT = ROOT / "examples" / "bonsaihub" / "product.toml"
DEMO = Path("examples") / "bonsaihub"
SKILL = Path(".claude") / "skills" / "keyline"
SETUP = "SETUP.json"
PACKAGES = ("lxml", "Pillow", "python-pptx", "pypdfium2")
DECKS = ("pitch", "preread")
SKIPPED = (".venv", ".claude")  # not the session's own files


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _files(folder: Path) -> list[Path]:
    return sorted(p for p in folder.rglob("*") if p.is_file())


def _python(folder: Path) -> Path:
    return folder / ".venv" / ("Scripts" if os.name == "nt" else "bin") / "python"


def setup(folder: Path, with_venv: bool = True) -> dict:
    folder = folder.resolve()
    if folder == ROOT or ROOT in folder.parents:
        raise SystemExit("demo: the folder must be outside the keyline checkout (audit 07 §4.7)")
    if folder.exists() and any(folder.iterdir()):
        raise SystemExit(f"demo: {folder} is not empty")
    if not ZIP.is_file():
        raise SystemExit("demo: dist/keyline.zip is missing: run tools/build_skill.py first")
    (folder / SKILL.parent).mkdir(parents=True)
    with zipfile.ZipFile(ZIP) as z:
        z.extractall(folder / SKILL.parent)
    (folder / DEMO).mkdir(parents=True)
    shutil.copy(PRODUCT, folder / DEMO / PRODUCT.name)
    if with_venv:
        venv.EnvBuilder(with_pip=True).create(folder / ".venv")
        subprocess.run(
            [str(_python(folder)), "-m", "pip", "install", "--quiet",
             "--disable-pip-version-check", "-c", str(ROOT / "constraints.txt"), *PACKAGES],
            check=True,
        )  # fmt: skip
    placed = [p.relative_to(folder).as_posix() for p in _files(folder) if ".venv" not in p.parts]
    data = {"zip_sha256": sha256(ZIP), "placed": placed}
    (folder / SETUP).write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    return data


def written(folder: Path) -> list[Path]:
    """Every file under `folder` that the fresh session wrote."""
    placed = set(json.loads((folder / SETUP).read_text(encoding="utf-8"))["placed"])
    return [
        p
        for p in _files(folder)
        if not set(SKIPPED) & set(p.relative_to(folder).parts)
        and p.relative_to(folder).as_posix() not in placed
        and p.name != SETUP
    ]


def record(folder: Path) -> str:
    folder = folder.resolve()
    data = json.loads((folder / SETUP).read_text(encoding="utf-8"))
    where = "not checked (no .venv)"
    if _python(folder).is_file():
        probe = folder / ".where.py"
        probe.write_text("import keyline\nprint(keyline.__file__)\n", encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME")}
        proc = subprocess.run(
            [str(_python(folder)), str(folder / SKILL / "scripts" / "kl.py"), "run", str(probe)],
            capture_output=True, text=True, cwd=folder, env=env,
        )  # fmt: skip
        probe.unlink()
        where = proc.stdout.strip() or proc.stderr.strip()
    lines = [
        f"- working directory: `{folder}`",
        f"- skill: `{folder / SKILL}`",
        f"- `dist/keyline.zip` SHA-256: `{data['zip_sha256']}`",
        f"- `keyline` imports from: `{where}`",
        "- files the session wrote:",
    ]
    lines += [f"  - `{p.relative_to(folder).as_posix()}` `{sha256(p)}`" for p in written(folder)]
    return "\n".join(lines) + "\n"


def outputs(folder: Path) -> list[Path]:
    """The demo's outputs under DIR/examples/bonsaihub: per deck its brief, build script,
    deck and render, and any evidence file the session added. Never product.toml."""
    demo = folder / DEMO
    found = []
    for deck in DECKS:
        found += [demo / f"{deck}.brief.toml", demo / f"build_{deck}.py", demo / f"{deck}.pptx"]
        found += [demo / f"{deck}.evidence.toml"]
        found += _files(demo / "render" / deck) if (demo / "render" / deck).is_dir() else []
    return [p for p in found if p.is_file()]


def collect(folder: Path, target: Path = ROOT / DEMO) -> list[Path]:
    folder = folder.resolve()
    copied = []
    for path in outputs(folder):
        dest = target / path.relative_to(folder / DEMO)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        copied.append(dest)
    return copied


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="set up and record the BonsaiHub demo")
    parser.add_argument("command", choices=("setup", "record", "collect"))
    parser.add_argument("folder", type=Path)
    parser.add_argument("--no-venv", action="store_true", help="setup: do not make DIR/.venv")
    args = parser.parse_args(argv)
    if args.command == "setup":
        data = setup(args.folder, with_venv=not args.no_venv)
        print(f"ready: {args.folder.resolve()} (zip {data['zip_sha256'][:12]}…)")
    elif args.command == "record":
        print(record(args.folder), end="")
    else:
        for path in collect(args.folder):
            print(path.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
