"""test_200_recurrence.py - unit tests for MakerSpace Esslingen's recurring events feature."""
# recurring events feature by MakerSpace Esslingen, these tests by Ian Kluft

# from typing import ClassVar

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from pelican.plugins.pelican_events import (
    UnknownTimeMultiplier,
    clear_events,
    insert_recurring_events,
    snapshot_events,
)


class TestRecurrence:
    """Test class with parmeterization for recurring events feature."""

    #
    # tests for insert_recurring_events()
    #

    @pytest.mark.filterwarnings(
        "ignore:.*Flag style will be deprecated in parsedatetime 2.*:"
    )
    @pytest.mark.parametrize(
        "in_settings, expected_event",
        [
            (
                {
                    "PLUGIN_EVENTS": {
                        "test_timestamp": "2025-10-04 11:00:00",
                        "timezone": "US/Pacific",
                        "metadata_field_for_summary": "summary",
                        "ics_fname": "calendar.ics",
                        "recurring_events": [
                            {
                                "title": "Monthly event",
                                "summary": "Something that happens monthly",
                                "page_url": "recurring_event_info.html",
                                "location": "a local meeting spot",
                                "recurring_rule": "Every third Thursday at 6pm starting from September 18 2025",
                                "event-duration": "2h",
                            }
                        ],
                    }
                },
                [
                    {
                        "event_plugin_data": {
                            "dtend": datetime(
                                2026, 10, 8, 20, 0, tzinfo=ZoneInfo(key="US/Pacific")
                            ),
                            "dtstart": datetime(
                                2026, 10, 8, 18, 0, tzinfo=ZoneInfo(key="US/Pacific")
                            ),
                        },
                        "location": "a local meeting spot",
                        "metadata": {
                            "date": datetime(
                                2026, 10, 8, 18, 0, tzinfo=ZoneInfo(key="US/Pacific")
                            ),
                            "event-location": "a local meeting spot",
                            "summary": "Something that happens monthly",
                            "title": "Monthly event",
                        },
                        "url": "pages/recurring_event_info.html",
                    },
                ],
            )
        ],
    )
    def test_insert_recurring_events(
        self, in_settings: dict, expected_event: dict
    ) -> None:
        """Tests for insert_recurring_events() checking expected_event contents."""
        clear_events()
        insert_recurring_events(in_settings)
        events = snapshot_events()
        assert events == expected_event

    @pytest.mark.filterwarnings(
        "ignore:.*Flag style will be deprecated in parsedatetime 2.*:"
    )
    @pytest.mark.parametrize(
        "exception, in_settings",
        [
            (
                UnknownTimeMultiplier,
                {
                    "PLUGIN_EVENTS": {
                        "test_timestamp": "2025-10-04 11:00:00",
                        "timezone": "US/Pacific",
                        "metadata_field_for_summary": "summary",
                        "ics_fname": "calendar.ics",
                        "recurring_events": [
                            {
                                "title": "Monthly event",
                                "summary": "Something that happens monthly",
                                "page_url": "recurring_event_info.html",
                                "location": "a local meeting spot",
                                "recurring_rule": "Every third Thursday at 6pm starting from September 18 2025",
                                "event-duration": "2z",
                            }
                        ],
                    }
                },
            ),
        ],
    )
    def test_except_insert_recurring_events(
        self, exception: Exception, in_settings: dict
    ) -> None:
        """Tests for insert_recurring_events() checking expected_event contents."""
        clear_events()
        with pytest.raises(exception):
            insert_recurring_events(in_settings)
