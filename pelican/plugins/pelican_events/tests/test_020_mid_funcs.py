"""test_020_mid_funcs.py - unit tests for mid-level functions in pelican_events plugin for Pelican."""
# by Ian Kluft

from datetime import datetime
from typing import ClassVar
from zoneinfo import ZoneInfo

import icalendar
import pytest

from pelican.contents import Article
from pelican.plugins.pelican_events import (
    parse_article,
    xfer_metadata_to_event,
)
from pelican.tests.support import get_settings

# constants
LOREM_IPSUM = "Lorem ipsum dolor sit amet, ad nauseam..."  # more or less standard placeholder text
MOCK_TZ = "US/Pacific"
MOCK_TIMES: tuple[dict[str, datetime]] = (
    {
        "dtstamp": datetime(2025, 9, 2, 0, 0, tzinfo=ZoneInfo("UTC")),
        "dtstart": datetime(2025, 9, 19, 1, 0, tzinfo=ZoneInfo("UTC")),
        "dtend": datetime(2025, 9, 19, 4, 0, tzinfo=ZoneInfo("UTC")),
    },
)


class TestMidFuncsData:
    """Test class with parameterization for mid-level functions in pelican_events plugin."""

    #
    # data used by text fixtures
    #

    mock_settings: ClassVar[dict[str, any]] = {
        "PLUGIN_EVENTS": {
            "timezone": MOCK_TZ,
            "ics_fname": "calendar.ics",
        },
    }
    mock_articles: ClassVar[tuple[Article]] = [
        Article(  # sample event, specified by end time
            LOREM_IPSUM,
            settings=get_settings(PLUGIN_EVENTS=mock_settings["PLUGIN_EVENTS"]),
            metadata={
                "title": "test 1",
                "event-start": "2025-09-18 18:00",
                "event-end": "2025-09-18 21:00",
            },
        ),
        Article(  # same as previous event, specified by duration
            LOREM_IPSUM,
            settings=get_settings(PLUGIN_EVENTS=mock_settings["PLUGIN_EVENTS"]),
            metadata={
                "title": "test 2",
                "event-start": "2025-09-18 18:00",
                "event-duration": "3h",
            },
        ),
        Article(  # event fails to specify end or duration - should be zero duration
            LOREM_IPSUM,
            settings=get_settings(PLUGIN_EVENTS=mock_settings["PLUGIN_EVENTS"]),
            metadata={
                "title": "test 3",
                "event-start": "2025-09-18 18:00",
            },
        ),
        Article(  # event fails to specify start - should be skipped by events plugin
            LOREM_IPSUM,
            settings=get_settings(PLUGIN_EVENTS=mock_settings["PLUGIN_EVENTS"]),
            metadata={
                "title": "test 4",
            },
        ),
        "this is a string",  # test for non-Article - should be skipped by events plugin
    ]
    mock_metadata: ClassVar[tuple[dict[str, any]]] = ()

    #
    # tests which check contents of event_plugin_data()
    #

    @pytest.mark.parametrize(
        "in_article, event_plugin_data",
        (
            (
                mock_articles[0],
                {
                    "dtstart": datetime(
                        2025,
                        9,
                        18,
                        18,
                        0,
                        tzinfo=ZoneInfo(mock_settings["PLUGIN_EVENTS"]["timezone"]),
                    ),
                    "dtend": datetime(
                        2025,
                        9,
                        18,
                        21,
                        0,
                        tzinfo=ZoneInfo(mock_settings["PLUGIN_EVENTS"]["timezone"]),
                    ),
                },
            ),
            (
                mock_articles[1],
                {
                    "dtstart": datetime(
                        2025,
                        9,
                        18,
                        18,
                        0,
                        tzinfo=ZoneInfo(mock_settings["PLUGIN_EVENTS"]["timezone"]),
                    ),
                    "dtend": datetime(
                        2025,
                        9,
                        18,
                        21,
                        0,
                        tzinfo=ZoneInfo(mock_settings["PLUGIN_EVENTS"]["timezone"]),
                    ),
                },
            ),
            (
                mock_articles[2],
                {
                    "dtstart": datetime(
                        2025,
                        9,
                        18,
                        18,
                        0,
                        tzinfo=ZoneInfo(mock_settings["PLUGIN_EVENTS"]["timezone"]),
                    ),
                    "dtend": datetime(
                        2025,
                        9,
                        18,
                        18,
                        0,
                        tzinfo=ZoneInfo(mock_settings["PLUGIN_EVENTS"]["timezone"]),
                    ),
                },
            ),
            (
                mock_articles[3],
                None,
            ),
            (
                mock_articles[4],
                None,
            ),
        ),
    )
    def test_parse_article_epd(self, in_article, event_plugin_data) -> None:
        """Tests for parse_article() checing event_plugin_data contents."""
        parse_article(in_article)  # modifies in_article
        if hasattr(in_article, "event_plugin_data"):
            assert in_article.event_plugin_data == event_plugin_data
        else:
            assert event_plugin_data is None  # test for non-existence using None

    #
    # tests which check contents of logging
    #

    @pytest.mark.parametrize(
        "in_article, log",
        (
            (
                mock_articles[0],
                "",
            ),
            (
                mock_articles[1],
                "",
            ),
            (
                mock_articles[2],
                "Either 'event-end' or 'event-duration' must be specified in the event named 'test 3'",
            ),
            (
                mock_articles[3],
                "",
            ),
            (
                mock_articles[4],
                "",
            ),
        ),
    )
    def test_parse_article_log(self, in_article, log, caplog) -> None:
        """Tests for parse_article() which generate logs."""
        parse_article(in_article)  # modifies in_article
        assert log in caplog.text

    @pytest.mark.parametrize(
        "metadata_field, value, field_name, expect_accept",
        (
            (
                "event-location",
                "Lucky Labrador Beer Hall: 1945 NW Quimby, Portland OR 97209 US",
                "LOCATION",
                True,
            ),
            ("event-calscale", "MARTIAN", "CALSCALE", False),
            ("event-method", "RejectedMethod", "METHOD", False),
            ("event-prodid", "BSoD Generator v2.1", "PRODID", False),
            ("event-version", "2.5", "VERSION", False),
            ("event-attach", "https://pdx-lkmu.ikluft.github.io/", "ATTACH", False),
            ("event-categories", "MEETING,LINUX,KERNEL,SOCIAL", "CATEGORIES", True),
            ("event-class", "CONFIDENTIAL", "CLASS", False),
            ("event-comment", "/* No comment! */", "COMMENT", True),
            (
                "event-description",
                "This is a description of something.",
                "DESCRIPTION",
                True,
            ),
            ("event-geo", "45.53371;-122.69174", "GEO", True),
            ("event-percent-complete", "99", "PERCENT-COMPLETE", False),
            ("event-priority", "9", "PRIORITY", False),
            ("event-resources", "TABLE,BEER", "RESOURCES", False),
            ("event-status", "CONFIRMED", "STATUS", True),
            ("event-summary", "Social event", "SUMMARY", True),
            ("event-completed", "20250902T000000", "COMPLETED", False),
            ("event-dtend", "20250919T040000", "DTEND", False),
            ("event-due", "20250919T010000", "DUE", False),
            ("event-dtstart", "20250919T010000", "DTSTART", False),
            ("event-duration", "PT3H0M0S", "DURATION", False),
            ("event-freebusy", "20250919T010000Z/PT3H", "FREEBUSY", False),
            ("event-transp", "TRANSPARENT", "TRANSP", False),
            ("event-tzid", "US/Pacific", "TZID", False),
            ("event-tzname", "PDT", "TZNAME", False),
            ("event-tzoffsetfrom", "-0700", "TZOFFSETFROM", False),
            ("event-tzoffsetto", "-0700", "TZOFFSETTO", False),
            (
                "event-tzurl",
                "http://timezones.example.org/tz/US-Pacific.ics",
                "TZURL",
                False,
            ),
            ("event-attendee", "mailto:lucy@example.com", "ATTENDEE", False),
            ("event-contact", "mailto:woodstock@example.com", "CONTACT", False),
            ("event-organizer", "mailto:snoopy@example.com", "ORGANIZER", False),
            ("event-recurrence-id", "20250919T010000Z", "RECURRENCE-ID", False),
            (
                "event-related-to",
                "20250919-010000-000F-DEADBEEF@example.com",
                "RELATED-TO",
                False,
            ),
            ("event-url", "https://ikluft.github.io/pdx-lkmu/", "URL", False),
            ("event-uid", "20250902-000000-000A-CAFEF00D@example.com", "UID", False),
        ),
    )
    def test_xfer_metadata_to_event_field(
        self, metadata_field, value, field_name, expect_accept
    ) -> None:
        """Tests for xfer_metadata_to_event() which check a field in the resulting iCalendar."""
        icalendar_event = icalendar.Event(
            dtstart=icalendar.vDatetime(MOCK_TIMES[0]["dtstart"]),
            dtend=icalendar.vDatetime(MOCK_TIMES[0]["dtend"]),
            dtstamp=icalendar.vDatetime(MOCK_TIMES[0]["dtstamp"]),
        )
        xfer_metadata_to_event({metadata_field: value}, icalendar_event)
        if field_name.upper() in icalendar_event:
            if isinstance(icalendar_event[field_name.upper()], icalendar.prop.TimeBase):
                value_dt = datetime.fromisoformat(value).replace(tzinfo=ZoneInfo("UTC"))
                assert icalendar_event[field_name.upper()].dt == value_dt
            elif isinstance(
                icalendar_event[field_name.upper()],
                icalendar.prop.vCategory | icalendar.prop.vText,
            ):
                assert (
                    icalendar_event[field_name.upper()]
                    .to_ical()
                    .decode("utf-8")
                    .replace("\\", "")
                    == value
                )
            elif isinstance(icalendar_event[field_name.upper()], icalendar.prop.vGeo):
                assert icalendar_event[field_name.upper()].to_ical() == value
            else:
                assert icalendar_event[field_name.upper()] == value
        else:
            assert expect_accept is False  # test for expected rejection of field
