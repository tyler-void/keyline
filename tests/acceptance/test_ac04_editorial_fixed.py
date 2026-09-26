"""AC-4: editorial-fixed.pptx exits 0 in read mode, and the fix adds no warning."""

from keyline.lint import lint_path
from tests.acceptance._cli import keyline
from tests.conftest import GOLDEN

FAILING = ("warning", "error")


def test_exits_zero_in_read_mode():
    proc = keyline("lint", GOLDEN / "editorial-fixed.pptx", "--mode", "read")
    assert proc.returncode == 0, proc.stderr.decode()


def test_no_new_warning_in_read_mode():
    def warned(name):
        found = lint_path(GOLDEN / name, "read").findings
        return {(f.rule, f.shape_name) for f in found if f.severity in FAILING}

    assert warned("editorial-fixed.pptx") - warned("editorial.pptx") == set()


def test_true_defects_are_gone():
    found = lint_path(GOLDEN / "editorial-fixed.pptx", "read").findings
    assert not [f for f in found if f.shape_name in ("verdict", "verdicttx", "l3")]
