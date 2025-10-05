"""test_500_integ.py - high-level integration tests of test_500_integ.py."""
# by Ian Kluft

from filecmp import cmp
from pathlib import Path
import re
import subprocess

import pytest  # noqa: F401


def get_test_path() -> str:
    """Get the path of the directory containing test subdirectories."""
    prog_path = Path(__file__)
    prog_dir = prog_path.parent
    re_result = re.search("[0-9]+", prog_path.name)
    if not re_result:
        raise OSError("No number in test script name: " + prog_path)
    test_num = int(re_result[0])
    test_top_dir = Path(prog_dir / f"t{test_num:03d}")
    if not test_top_dir.exists() or not test_top_dir.is_dir():
        raise OSError("Test top directory does not exist: " + test_top_dir)
    return test_top_dir


def pytest_generate_tests(metafunc):
    """Generate tests from class.params dict."""
    # called once per each test function
    test_func_dir = get_test_path() / metafunc.function.__name__
    if test_func_dir.exists() and test_func_dir.is_dir():
        metafunc.parametrize(["test_subdir"], [[name] for name in sorted(test_func_dir.glob("[0-9]*"))])


class TestPelicanRun:
    """Run Pelican integration tests via its CLI."""

    def test_run(self, tmp_path, test_subdir: Path) -> None:
        """Test Pelican integration tests via its CLI - these are expected to run and generate output."""
        output_dir = tmp_path / "output"
        output_dir.mkdir(mode=0o775)
        subprocess.run(
            [
                "pelican",
                "--settings",
                "publishconf.py",
                "--output",
                str(output_dir),
            ],
            cwd=test_subdir,
            check=True,
        )
        assert cmp(test_subdir / "expected_calendar.ics", output_dir / "calendar.ics")
