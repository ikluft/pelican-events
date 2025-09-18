"""test_010_util_funcs.py - unit tests for low-level utility functions in pelican_events plugin for Pelican."""
# by Ian Kluft

from datetime import datetime, timedelta
from typing import ClassVar
from zoneinfo import ZoneInfo

import pytest

import pelican.plugins.pelican_events


def pytest_generate_tests(metafunc):
    """Generate tests from class.params dict."""
    # called once per each test function
    funcarglist = metafunc.cls.params[metafunc.function.__name__]
    argnames = sorted(funcarglist[0])
    metafunc.parametrize(
        argnames, [[funcargs[name] for name in argnames] for funcargs in funcarglist]
    )


class TestCaseData:
    """Test class and fixture data for low-level utility functions in pelican_events plugin."""

    tstamp_metadata: ClassVar[dict[str, str | datetime]] = {
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
    params: ClassVar[dict[str, dict[str, any]]] = {
        "test_strip_html_tags": (
            {"text": "no HTML here", "out": "no HTML here"},
            {"text": "<i>italic</i>", "out": "_italic_"},
            {"text": "<b>bold</b>", "out": "**bold**"},
        ),
        "test_parse_tstamp": (
            {
                # "name": "start",
                "in_metadata": tstamp_metadata,
                "in_field_name": "event-start",
                "in_tz": ZoneInfo(key="US/Pacific"),
                "out": datetime(2025, 9, 18, 18, 0, tzinfo=ZoneInfo(key="US/Pacific")),
            },
            {
                # "name": "end",
                "in_metadata": tstamp_metadata,
                "in_field_name": "event-end",
                "in_tz": ZoneInfo(key="US/Pacific"),
                "out": datetime(2025, 9, 18, 21, 0, tzinfo=ZoneInfo(key="US/Pacific")),
            },
            {
                # "name": "date",
                "in_metadata": tstamp_metadata,
                "in_field_name": "date",
                "in_tz": ZoneInfo(key="US/Pacific"),
                "out": datetime(2025, 9, 5, 23, 0, tzinfo=ZoneInfo(key="US/Pacific")),
            },
            {
                # "name": "utc",
                "in_metadata": tstamp_metadata,
                "in_field_name": "tz-utc",
                "in_tz": ZoneInfo(key="UTC"),
                "out": datetime(2025, 9, 6, 6, 0, tzinfo=ZoneInfo(key="UTC")),
            },
            {
                # "name": "none",
                "in_metadata": tstamp_metadata,
                "in_field_name": "tz-none",
                "in_tz": None,
                "out": datetime(2025, 9, 6, 6, 0, 0),
            },
        ),
        "test_except_parse_tstamp": (
            {
                # "name": "hour error",
                "in_metadata": tstamp_metadata,
                "in_field_name": "date-err-hour",
                "in_tz": None,
                "exception": pelican.plugins.pelican_events.FieldParseError,
            },
            {
                # "name": "day error",
                "in_metadata": tstamp_metadata,
                "in_field_name": "date-err-day",
                "in_tz": None,
                "exception": pelican.plugins.pelican_events.FieldParseError,
            },
            {
                # "name": "month error",
                "in_metadata": tstamp_metadata,
                "in_field_name": "date-err-month",
                "in_tz": None,
                "exception": pelican.plugins.pelican_events.FieldParseError,
            },
        ),
        "test_parse_timedelta": (
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
        "test_except_parse_timedelta": (
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
        "test_field_name_check": (
            {
                "in_fname": "location",
                "out": None,
            },
            {
                "in_fname": "LOCATION",
                "out": None,
            },
            {
                "in_fname": "FooBar",
                "out": "unrecognized iCalendar property 'FooBar'",
            },
            {
                "in_fname": "foobar",
                "out": "unrecognized iCalendar property 'foobar'",
            },
            {
                "in_fname": "FOOBAR",
                "out": "unrecognized iCalendar property 'FOOBAR'",
            },
            {
                "in_fname": "X-Experimental",
                "out": None,
            },
            {
                "in_fname": "x-experimental",
                "out": None,
            },
            {
                "in_fname": "X-EXPERIMENTAL",
                "out": None,
            },
            {
                "in_fname": "method",
                "out": "property 'method' disallowed, ref: [RFC5545, Section 3.7.2]",
            },
            {
                "in_fname": "METHOD",
                "out": "property 'METHOD' disallowed, ref: [RFC5545, Section 3.7.2]",
            },
        ),
    }

    def test_strip_html_tags(self, text, out) -> None:
        """Tests for strip_html_tags()."""
        assert pelican.plugins.pelican_events.strip_html_tags(text) == out

    def test_parse_tstamp(self, in_metadata, in_field_name, in_tz, out) -> None:
        """Tests for parse_tstamp()."""
        assert (
            pelican.plugins.pelican_events.parse_tstamp(
                in_metadata,
                in_field_name,
                in_tz,
            )
            == out
        )

    def test_except_parse_tstamp(
        self, exception, in_metadata, in_field_name, in_tz
    ) -> None:
        """Tests for parse_tstamp() which raise exceptions."""
        with pytest.raises(exception):
            pelican.plugins.pelican_events.parse_tstamp(
                in_metadata,
                in_field_name,
                in_tz,
            )

    def test_parse_timedelta(self, in_duration, out) -> None:
        """Tests for parse_timedelta()."""
        assert (
            pelican.plugins.pelican_events.parse_timedelta(
                {
                    "event-duration": in_duration,
                    "title": in_duration,
                },
            )
            == out
        )

    def test_except_parse_timedelta(self, exception, in_duration) -> None:
        """Tests for parse_timedelta() which raise exceptions."""
        with pytest.raises(exception):
            pelican.plugins.pelican_events.parse_timedelta(
                {
                    "event-duration": in_duration,
                    "title": in_duration,
                },
            )

    def test_field_name_check(self, in_fname, out) -> None:
        """Tests for field_name_check()."""
        assert pelican.plugins.pelican_events.field_name_check(in_fname) == out
