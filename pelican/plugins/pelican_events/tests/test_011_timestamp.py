"""test_011_timestamp.py - unit tests for low-level utility functions using timestamp fixtures."""
# by Ian Kluft

from datetime import datetime
from typing import Any, ClassVar
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


class TestTimestampData:
    """Test class and fixture data for low-level utility functions using timestamp fixtures."""

    # for tests in this file, the setting "test_timestamp" forces a test value in place of the current time

    # test fixtures by function name providing batches of arguments for each test
    params: ClassVar[dict[str, dict[str, Any]]] = {
        "test_timestamp_now": (
            {
                "in_settings": {
                    "PLUGIN_EVENTS": {
                        "timezone": "US/Pacific",
                        "test_timestamp": "2025-10-03 18:00:00",
                    },
                },
                "out": datetime(
                    2025, 10, 3, 18, 0, 0, tzinfo=ZoneInfo(key="US/Pacific")
                ),
            },
            {
                "in_settings": {
                    "PLUGIN_EVENTS": {
                        "timezone": "UTC",
                        "test_timestamp": "2025-10-04 01:00:00",
                    },
                },
                "out": datetime(2025, 10, 4, 1, 0, 0, tzinfo=ZoneInfo(key="UTC")),
            },
        ),
        "test_except_timestamp_now": (
            {
                "in_settings": {
                    "PLUGIN_EVENTS": {
                        "timezone": "UTC",
                        "test_timestamp": "2025-10-04 25:00:00",
                    },
                },
                "exception": ValueError,
            },
        ),
    }

    def test_timestamp_now(self, in_settings: dict[str, Any], out: datetime) -> None:
        """Tests for timestamp_now()."""
        dt = pelican.plugins.pelican_events.timestamp_now(in_settings)
        assert dt == out

    def test_except_timestamp_now(
        self, exception: Exception, in_settings: dict[str, Any]
    ) -> None:
        """Tests for timestamp_now() which raise exceptions."""
        with pytest.raises(exception):
            pelican.plugins.pelican_events.timestamp_now(in_settings)
