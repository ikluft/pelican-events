"""test_300_ical.py - unit tests for generating an ical file."""
# by Ian Kluft

from filecmp import cmp
import importlib
import logging
import os
from pathlib import Path
import re
import sys
from typing import Any

import pytest

from pelican.contents import Article
from pelican.generators import ArticlesGenerator
from pelican.plugins.pelican_events import (
    clear_events,
    generate_ical_file,
    parse_article,
)
from pelican.readers import Readers
from pelican.settings import Settings, read_settings

log = logging.getLogger(__name__)

#
# constants
#

CONTENT_EXTENSIONS = ["static", "rst", "md", "markdown", "mkd", "mdown", "htm", "html"]

#
# pytest setup
#


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
    log.debug(
        "pytest version %s", pytest.__version__
    )  # explicitly using pytest to plug bogus unused-import warning
    test_func_dir = get_test_path() / metafunc.function.__name__
    if test_func_dir.exists() and test_func_dir.is_dir():
        metafunc.parametrize(
            ["test_subdir"], [[name] for name in sorted(test_func_dir.glob("[0-9]*"))]
        )


class TestGenerateIcal:
    """Unit tests for generating an ical file using generate_ical_file()."""

    @staticmethod
    def process_article(
        filepath: Path,
        settings: Settings,
        # source_path: Path,
        context: dict[str, Any] | None,
    ) -> None:
        """Read a file's contents, then run parse_article() to save any event found in it."""
        log.debug("process_article: filepath=%s", repr(filepath))
        log.debug("process_article: settings=%s", repr(settings))
        log.debug("process_article: context=%s", repr(context))

        # parse_article() was tested in test_020_mid_funcs.py, called here to set up for generate_ical_file()
        reader = Readers(settings=settings)
        article = reader.read_file(
            filepath.parent, filepath.name, content_class=Article, context=context
        )
        parse_article(article)

    def test_generate_ical_file(self, tmp_path, test_subdir: Path) -> None:
        """Unit tests generating ical file using generate_ical_file() - tests expected to generate output."""
        # prepare test directory
        os.chdir(test_subdir)  # exceptions for directory existence or access errors

        # clear any previously-loaded settings modules
        # Since they are loaded as modules, each one must be cleared before reloading one of the same name.
        importlib.invalidate_caches()
        if "publishconf" in sys.modules:
            del sys.modules["publishconf"]
        if "pelicanconf" in sys.modules:
            del sys.modules["pelicanconf"]
        log.debug(
            "test_generate_ical_file: keys from globals() %s", repr(globals().keys())
        )

        # load settings
        settings_path = Path(test_subdir / "publishconf.py")
        settings = read_settings(settings_path)

        # prepare output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir(mode=0o775)
        settings["OUTPUT_PATH"] = str(output_dir)

        # create context object from copy of settings, for mocking up a generator like Pelican builds them
        context = settings.copy()
        context["generated_content"] = {}
        context["static_links"] = set()
        context["static_content"] = {}
        context["localsiteurl"] = settings["SITEURL"]

        # load events from files in content directory
        clear_events()
        content_path = test_subdir / "content"
        for file in os.listdir(content_path):
            filepath = content_path / file
            if str(filepath.suffix).removeprefix(".") in CONTENT_EXTENSIONS:
                log.debug(
                    "test_generate_ical_file: processing article %s", str(filepath)
                )
                TestGenerateIcal.process_article(content_path / file, settings, context)
            else:
                log.debug("test_generate_ical_file: skipped article %s", str(filepath))

        # create mock generator object and generate ical file
        generator = ArticlesGenerator(
            context, settings, test_subdir, settings["THEME"], output_dir
        )
        generate_ical_file(generator)

        expect_path = test_subdir / "expected_calendar.ics"
        result_path = output_dir / settings["PLUGIN_EVENTS"]["ics_fname"]
        assert cmp(expect_path, result_path)
