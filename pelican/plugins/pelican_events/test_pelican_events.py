"""unit tests for pelican_events plugin for Pelican."""

import abc
from abc import ABCMeta
from datetime import datetime, timedelta
import unittest
from zoneinfo import ZoneInfo

import pelican.plugins.pelican_events

TSTAMP_METADATA = {
    "event-start": "2025-09-18 18:00",
    "event-end": "2025-09-18 21:00",
    "date": "2025-09-05 23:00",
    "date-err-hour": "2025-09-05 25:00",
    "date-err-day": "2025-09-31 23:00",
    "date-err-month": "2025-13-05 23:00",
    "tz-none": datetime(2025, 9, 6, 6, 0, 0),
    "tz-utc": datetime(2025, 9, 6, 6, 0, tzinfo=ZoneInfo(key="UTC")),
    "title": "September 2025 Portland Linux Kernel Meetup",
}
TEST_CASES = {
    "TestStripHtmlTags": (
        {"in": "no HTML here", "out": "no HTML here"},
        {"in": "<i>italic</i>", "out": "_italic_"},
        {"in": "<b>bold</b>", "out": "**bold**"},
    ),
    "TestParseTstamp": (
        {
            "name": "start",
            "in_metadata": TSTAMP_METADATA,
            "in_field_name": "event-start",
            "in_tz": ZoneInfo(key="US/Pacific"),
            "out": datetime(2025, 9, 18, 18, 0, tzinfo=ZoneInfo(key="US/Pacific")),
        },
        {
            "name": "end",
            "in_metadata": TSTAMP_METADATA,
            "in_field_name": "event-end",
            "in_tz": ZoneInfo(key="US/Pacific"),
            "out": datetime(2025, 9, 18, 21, 0, tzinfo=ZoneInfo(key="US/Pacific")),
        },
        {
            "name": "date",
            "in_metadata": TSTAMP_METADATA,
            "in_field_name": "date",
            "in_tz": ZoneInfo(key="US/Pacific"),
            "out": datetime(2025, 9, 5, 23, 0, tzinfo=ZoneInfo(key="US/Pacific")),
        },
        {
            "name": "utc",
            "in_metadata": TSTAMP_METADATA,
            "in_field_name": "tz-utc",
            "in_tz": ZoneInfo(key="UTC"),
            "out": datetime(2025, 9, 6, 6, 0, tzinfo=ZoneInfo(key="UTC")),
        },
        {
            "name": "none",
            "in_metadata": TSTAMP_METADATA,
            "in_field_name": "tz-none",
            "in_tz": None,
            "out": datetime(2025, 9, 6, 6, 0, 0),
        },
    ),
    "ExceptParseTstamp": (
        {
            "name": "field parse error",
            "in_metadata": TSTAMP_METADATA,
            "in_field_name": "date-err-hour",
            "in_tz": None,
            "exception": pelican.plugins.pelican_events.FieldParseError,
        },
        {
            "name": "field parse error",
            "in_metadata": TSTAMP_METADATA,
            "in_field_name": "date-err-day",
            "in_tz": None,
            "exception": pelican.plugins.pelican_events.FieldParseError,
        },
        {
            "name": "field parse error",
            "in_metadata": TSTAMP_METADATA,
            "in_field_name": "date-err-month",
            "in_tz": None,
            "exception": pelican.plugins.pelican_events.FieldParseError,
        },
    ),
    "TestParseTimedelta": (
        {
            "in_duration": "1h",
            "out": timedelta(seconds=3600),  # seconds
        },
        {
            "in_duration": "2h 30m",
            "out": timedelta(seconds=9000),  # seconds
        },
        {
            "in_duration": "4m 8s",
            "out": timedelta(seconds=248),  # seconds
        },
    ),
    "ExceptParseTimedelta": (
        {
            "in_duration": "1b",
            "exception": pelican.plugins.pelican_events.UnknownTimeMultiplier,
        },
        {
            "in_duration": "hah",
            "exception": pelican.plugins.pelican_events.DurationParseError,
        },
        {
            "in_duration": "m",
            "exception": pelican.plugins.pelican_events.DurationParseError,
        },
    ),
}


class TestCaseSet(unittest.TestCase, metaclass=ABCMeta):
    """Base class for test case sets."""

    def iterate_tests(self):
        """Iterate through test cases for the class."""
        for test_num, test_case in enumerate(TEST_CASES[self.__class__.__name__]):
            with self.subTest(
                type=self.__class__.__name__, name=self.case_name(test_num, test_case)
            ):
                self.do_test(test_num, test_case)

    @abc.abstractmethod
    def case_name(self, test_num: int, test_case: dict) -> str:
        """Return a name of the test case to make it easier to find in error reporting."""
        raise NotImplementedError

    @abc.abstractmethod
    def do_test(self, test_num: int, test_case: dict) -> None:
        """Perform a single test case."""
        raise NotImplementedError


class TestStripHtmlTags(TestCaseSet):
    """Tests for strip_html_tags()."""

    def case_name(self, test_num: int, test_case: dict) -> str:
        """Return a name of the test case to make it easier to find in error reporting."""
        return f"[{test_num}] {test_case['in']}"

    def do_test(self, test_num: int, test_case: dict) -> None:
        """Perform a single test case."""
        self.assertEqual(
            pelican.plugins.pelican_events.strip_html_tags(test_case["in"]),
            test_case["out"],
        )

    def test_strip_html_tags(self):
        """Subtests for strip_html_tags(). The test_ prefix gets discovered and run by unittest."""
        self.iterate_tests()


class TestParseTstamp(TestCaseSet):
    """Tests for parse_tstamp()."""

    def case_name(self, test_num: int, test_case: dict) -> str:
        """Return a name of the test case to make it easier to find in error reporting."""
        return f"[{test_num}] {test_case['name']}"

    def do_test(self, test_num: int, test_case: dict) -> None:
        """Perform a single test case."""
        self.assertEqual(
            pelican.plugins.pelican_events.parse_tstamp(
                test_case["in_metadata"],
                test_case["in_field_name"],
                test_case["in_tz"],
            ),
            test_case["out"],
        )

    def test_strip_html_tags(self):
        """Subtests for parse_tstamp(). The test_ prefix gets discovered and run by unittest."""
        self.iterate_tests()


class ExceptParseTstamp(TestCaseSet):
    """Tests for parse_tstamp() which raise exceptions."""

    def case_name(self, test_num: int, test_case: dict) -> str:
        """Return a name of the test case to make it easier to find in error reporting."""
        return f"[{test_num}] {test_case['name']}"

    def do_test(self, test_num: int, test_case: dict) -> None:
        """Perform a single test case."""
        with self.assertRaises(
            test_case["exception"], msg=self.case_name(test_num, test_case)
        ):
            pelican.plugins.pelican_events.parse_tstamp(
                test_case["in_metadata"],
                test_case["in_field_name"],
                test_case["in_tz"],
            )

    def test_exc_strip_html_tags(self):
        """Subtests for parse_tstamp(). The test_ prefix gets discovered and run by unittest."""
        self.iterate_tests()


class TestParseTimedelta(TestCaseSet):
    """Tests for parse_timedelta()."""

    def case_name(self, test_num: int, test_case: dict) -> str:
        """Return a name of the test case to make it easier to find in error reporting."""
        return f"[{test_num}] {test_case['in_duration']}"

    def do_test(self, test_num: int, test_case: dict) -> None:
        """Perform a single test case."""
        self.assertEqual(
            pelican.plugins.pelican_events.parse_timedelta(
                {
                    "event-duration": test_case["in_duration"],
                    "title": test_case["in_duration"],
                },
            ),
            test_case["out"],
        )

    def test_strip_html_tags(self):
        """Subtests for parse_timedelta(). The test_ prefix gets discovered and run by unittest."""
        self.iterate_tests()


class ExceptParseTimedelta(TestCaseSet):
    """Tests for parse_timedelta() which raise exceptions."""

    def case_name(self, test_num: int, test_case: dict) -> str:
        """Return a name of the test case to make it easier to find in error reporting."""
        return f"[{test_num}] {test_case['in_duration']}"

    def do_test(self, test_num: int, test_case: dict) -> None:
        """Perform a single test case."""
        with self.assertRaises(
            test_case["exception"], msg=self.case_name(test_num, test_case)
        ):
            pelican.plugins.pelican_events.parse_timedelta(
                {
                    "event-duration": test_case["in_duration"],
                    "title": test_case["in_duration"],
                },
            )

    def test_strip_html_tags(self):
        """Subtests for parse_timedelta(). The test_ prefix gets discovered and run by unittest."""
        self.iterate_tests()


if __name__ == "__main__":
    unittest.main()
