"""unit tests for pelican_events plugin for Pelican."""

from datetime import datetime
import unittest
from zoneinfo import ZoneInfo

import pelican.plugins.pelican_events

TSTAMP_METADATA = {
    "event-start": "2025-09-18 18:00",
    "event-end": "2025-09-18 21:00",
    "date": "2025-09-05 23:00",
    "tz-none": datetime(2025, 9, 5, 23, 0, 0),
    "tz-utc": datetime(2025, 9, 5, 23, 0, tzinfo=ZoneInfo(key="UTC")),
    "title": "September 2025 Portland Linux Kernel Meetup",
}
TEST_CASES = {
    "strip_html_tags": (
        {"in": "no HTML here", "out": "no HTML here"},
        {"in": "<i>italic</i>", "out": "_italic_"},
        {"in": "<b>bold</b>", "out": "**bold**"},
    ),
    "parse_tstamp": (
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
            "out": datetime(2025, 9, 5, 23, 0, tzinfo=ZoneInfo(key="UTC")),
        },
        {
            "name": "none",
            "in_metadata": TSTAMP_METADATA,
            "in_field_name": "tz-none",
            "in_tz": None,
            "out": datetime(2025, 9, 5, 23, 0, 0),
        },
    ),
}


class TestCaseSet(unittest.TestCase):
    """Base class for test case sets."""

    @classmethod
    def case_set(cls):
        """Return name of test case set - abstract function to be redefined in subclasses."""
        raise NotImplementedError("define and use case_set() in subclasses")


class TestStripHtmlTags(TestCaseSet):
    """Tests for strip_html_tags()."""

    @classmethod
    def case_set(cls):
        """Return name of test case set."""
        return "strip_html_tags"

    def test_strip_html_tags(self):
        """Subtests for strip_html_tags()."""
        for test_num, test_case in enumerate(TEST_CASES[self.__class__.case_set()]):
            with self.subTest(
                type=self.__class__.case_set(), number=test_num, text=test_case["in"]
            ):
                self.assertEqual(
                    pelican.plugins.pelican_events.strip_html_tags(test_case["in"]),
                    test_case["out"],
                )


class TestParseTstamp(TestCaseSet):
    """Tests for parse_tstamp()."""

    @classmethod
    def case_set(cls):
        """Return name of test case set."""
        return "parse_tstamp"

    def test_strip_html_tags(self):
        """Subtests for strip_html_tags()."""
        for test_num, test_case in enumerate(TEST_CASES[self.__class__.case_set()]):
            with self.subTest(
                type=self.__class__.case_set(), number=test_num, name=test_case["name"]
            ):
                self.assertEqual(
                    pelican.plugins.pelican_events.parse_tstamp(
                        test_case["in_metadata"],
                        test_case["in_field_name"],
                        test_case["in_tz"],
                    ),
                    test_case["out"],
                )


if __name__ == "__main__":
    unittest.main()
