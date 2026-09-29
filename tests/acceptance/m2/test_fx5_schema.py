"""Audit 02 FX-5 (amendment B-12 items 1-7, and X-17): schema errors are exit 1 with one
line that names the file and key, never an internal error."""

import shutil
import subprocess
import sys

import pytest

from keyline.brief import BriefError, load
from keyline.packs import PackError, resolve
from keyline.packs.voices import VoiceError
from keyline.packs.voices import load as load_voice
from tests.acceptance._cli import keyline
from tests.conftest import FIXTURES, ROOT

BRIEFS = FIXTURES / "briefs"
VALID = (BRIEFS / "valid.brief.toml").read_text(encoding="utf-8")
EVIDENCE = (BRIEFS / "evidence.toml").read_text(encoding="utf-8")
PACK = resolve("swiss")
DECK = FIXTURES / "briefs/drift/base.pptx"
NEUTRAL = PACK.directory / "voices/neutral.toml"


def _brief(tmp_path, old="", new="", evidence=None):
    """valid.brief.toml with one change, beside copies of its evidence files."""
    for name in ("evidence.toml", "extra-evidence.toml"):
        shutil.copyfile(BRIEFS / name, tmp_path / name)
    if evidence is not None:
        (tmp_path / "evidence.toml").write_text(evidence, encoding="utf-8")
    assert not old or VALID.count(old) == 1, old
    path = tmp_path / "b.brief.toml"
    path.write_text(VALID.replace(old, new) if old else VALID, encoding="utf-8")
    return path


def _error(tmp_path, *change, evidence=None):
    with pytest.raises(BriefError) as err:
        load(_brief(tmp_path, *change, evidence=evidence))
    assert "\n" not in str(err.value)
    return str(err.value)


# item 1: full-string matches
def test_ids_hex_and_names_use_fullmatch(tmp_path):
    bad_id = EVIDENCE.replace('id = "returns_repaired"', 'id = "returns_repaired\\n"')
    assert "evidence[1].id: 'returns_repaired\\n' must match" in _error(tmp_path, evidence=bad_id)
    msg = _error(tmp_path, 'accent = "1F6F5C"', 'accent = "1F6F5C\\n"')
    assert "palette.accent '1F6F5C\\n' is not 6-digit hex" in msg
    with pytest.raises(VoiceError, match="unknown voice 'night\\\\n'"):
        load_voice(PACK, "night\n")
    with pytest.raises(PackError, match="pack not found"):
        resolve("swiss\n")


# item 2: one line per slide
@pytest.mark.parametrize("brk", ["\\n", "\\r", "\\u000b", "\\u2028", "\\u2029"])
def test_line_breaks_in_headlines_and_reads(tmp_path, brk):
    msg = _error(tmp_path, 'headline = "Toolshed Commons"', f'headline = "Toolshed{brk}Commons"')
    assert msg == "slides[1].headline: must be one line (it contains a line break)"
    msg = _error(tmp_path, '"why it matters"', f'"why it{brk}matters"')
    assert msg == "slides[2].reads[2]: must be one line (it contains a line break)"


# item 3: a brief names its voice; only --voice may be a file
@pytest.mark.parametrize("value", ["voices/night.toml", "night.toml", "..\\\\night"])
def test_a_briefs_voice_is_a_name(tmp_path, value):
    text = VALID[: VALID.index("[voice.fonts]")] + VALID[VALID.index("[[slides]]") :]
    text = text.replace('pack = "swiss"\n', f'pack = "swiss"\nvoice = "{value}"\n')
    path = _brief(tmp_path)
    path.write_text(text, encoding="utf-8")
    with pytest.raises(BriefError, match="is a path; a brief names a voice of its pack"):
        load(path)


# item 5: pack.toml
@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ('modes = ["presented", "read"]', "modes = []", "modes: must name at least one mode"),
        ("columns = 12", "columns = 0", "grid.columns: must be at least 1"),
        ("size_pt = 66", "size_pt = nan", "size_pt: must be a finite number"),
        ("[grid]", "grid = 3\n[gridx]", "grid"),
    ],
)
def test_pack_toml_errors(tmp_path, old, new, message):
    text = (PACK.directory / "pack.toml").read_text(encoding="utf-8")
    assert old in text
    (tmp_path / "pack.toml").write_text(text.replace(old, new, 1), encoding="utf-8")
    with pytest.raises(PackError, match=message) as err:
        resolve(tmp_path)
    assert "\n" not in str(err.value)


# item 6: B-4 on the CLI path
def test_pack_and_mode_on_the_command_line():
    one_mode = BRIEFS / "packs/presented-only"
    proc = keyline("lint", DECK, "--pack", one_mode, "--voice", NEUTRAL, "--mode", "read")
    assert proc.returncode == 1 and proc.stdout == b""
    assert proc.stderr.decode() == "keyline: mode: pack swiss has no read mode (presented)\n"


# item 7: paths that are not readable TOML files
def test_unreadable_paths_are_one_line(tmp_path):
    msg = _error(tmp_path, '"evidence.toml", "extra-evidence.toml"', '"evidence.toml", "."')
    assert msg == f"evidence file {tmp_path.name} is a directory, not a file"
    proc = keyline("brief", BRIEFS)
    assert proc.returncode == 1
    assert proc.stderr.decode() == "keyline: briefs: brief is a directory, not a file\n"
    latin = tmp_path / "latin.brief.toml"
    latin.write_bytes(VALID.replace("Toolshed", "Tool\xe9shed").encode("latin-1"))
    with pytest.raises(BriefError, match=r"^brief is not UTF-8$"):
        load(latin)
    deep = tmp_path / "deep.brief.toml"
    deep.write_text("a = " + "[" * 5000 + "]" * 5000 + "\n", encoding="utf-8")
    with pytest.raises(BriefError, match=r"^brief (nests too deeply|is not valid TOML)"):
        load(deep)
    (tmp_path / "packdir" / "pack.toml").mkdir(parents=True)
    with pytest.raises(
        PackError, match=r"^pack file packdir/pack\.toml is a directory, not a file$"
    ):
        resolve(tmp_path / "packdir")
    (tmp_path / "v.toml").mkdir()
    with pytest.raises(VoiceError, match=r"voice file v\.toml is a directory, not a file"):
        load_voice(PACK, tmp_path / "v.toml")


# X-17: a bare name is the bundled pack; a path needs a separator or a leading "."
def test_a_local_directory_cannot_shadow_a_bundled_pack(tmp_path):
    shutil.copytree(BRIEFS / "packs/presented-only", tmp_path / "swiss")
    base = [sys.executable, "-m", "keyline", "lint", str(DECK), "--voice", str(NEUTRAL)]
    bundled = subprocess.run([*base, "--pack", "swiss", "--mode", "read"], cwd=tmp_path)
    local = subprocess.run(
        [*base, "--pack", "./swiss", "--mode", "read"], cwd=tmp_path, capture_output=True
    )
    assert bundled.returncode in (0, 2)  # the bundled pack has read mode
    assert local.returncode == 1 and b"has no read mode" in local.stderr
    assert resolve("./swiss", base=tmp_path).modes == ("presented",)
    assert resolve("swiss", base=tmp_path).directory == ROOT / "src/keyline/packs/swiss"
