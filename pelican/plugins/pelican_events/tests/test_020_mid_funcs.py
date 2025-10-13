"""test_020_mid_funcs.py - unit tests for mid-level functions in pelican_events plugin for Pelican."""
# by Ian Kluft

from datetime import datetime
from typing import Any, ClassVar
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
            "ics_fname": "calendar.ics",
        },
        "TIMEZONE": MOCK_TZ,
    }
    mock_articles: ClassVar[tuple[Article]] = [
        Article(  # sample event, specified by end time
            LOREM_IPSUM,
            settings=get_settings(**mock_settings),
            metadata={
                "title": "test 1",
                "event-start": "2025-09-18 18:00",
                "event-end": "2025-09-18 21:00",
            },
        ),
        Article(  # same as previous event, specified by duration
            LOREM_IPSUM,
            settings=get_settings(**mock_settings),
            metadata={
                "title": "test 2",
                "event-start": "2025-09-18 18:00",
                "event-duration": "3h",
            },
        ),
        Article(  # event fails to specify end or duration - should be zero duration
            LOREM_IPSUM,
            settings=get_settings(**mock_settings),
            metadata={
                "title": "test 3",
                "event-start": "2025-09-18 18:00",
            },
        ),
        Article(  # event fails to specify start - should be skipped by events plugin
            LOREM_IPSUM,
            settings=get_settings(**mock_settings),
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
                        tzinfo=ZoneInfo(mock_settings["TIMEZONE"]),
                    ),
                    "dtend": datetime(
                        2025,
                        9,
                        18,
                        21,
                        0,
                        tzinfo=ZoneInfo(mock_settings["TIMEZONE"]),
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
                        tzinfo=ZoneInfo(mock_settings["TIMEZONE"]),
                    ),
                    "dtend": datetime(
                        2025,
                        9,
                        18,
                        21,
                        0,
                        tzinfo=ZoneInfo(mock_settings["TIMEZONE"]),
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
                        tzinfo=ZoneInfo(mock_settings["TIMEZONE"]),
                    ),
                    "dtend": datetime(
                        2025,
                        9,
                        18,
                        18,
                        0,
                        tzinfo=ZoneInfo(mock_settings["TIMEZONE"]),
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
    def test_parse_article_epd(
        self, in_article: Article, event_plugin_data: dict[str, Any]
    ) -> None:
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
    def test_parse_article_log(self, in_article: Article, log: str, caplog) -> None:
        """Tests for parse_article() which generate logs."""
        parse_article(in_article)  # modifies in_article
        assert log in caplog.text

    @pytest.mark.parametrize(
        "metadata_field, value, field_name, expect_accept",
        (
            # note: DTSTART, DTEND & DTSTAMP can't be tested for non-existence because they're required
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
            ("event-due", "20250919T010000", "DUE", False),
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
            ("event-url", "https://ikluft.github.io/pdx-lkmu/", "URL", True),
            ("event-uid", "20250902-000000-000A-CAFEF00D@example.com", "UID", True),
            (
                "event-exdate",
                "20250402T010000Z,20250403T010000Z,20250404T010000Z",
                "EXDATE",
                False,
            ),
            ("event-exrule", "deprecatedZ", "EXRULE", False),
            ("event-rdate", "20260714T123000Z", "RDATE", False),
            ("event-rrule", "FREQ=DAILY;INTERVAL=2", "RRULE", False),
            ("event-action", "AUDIO", "ACTION", False),
            ("event-repeat", "3", "REPEAT", False),
            ("event-trigger", "-PT90M", "TRIGGER", False),
            # ("event-created", "20250329T133000Z", "CREATED", True),  # fails due to icalendar.py glitch
            ("event-last-modified", "20250817T133000Z", "LAST-MODIFIED", False),
            ("event-sequence", "2", "SEQUENCE", False),
            ("event-request-status", "2.0;Success", "REQUEST-STATUS", False),
            (
                "event-xml",
                '<kml xmlns="http://www.opengis.net/kml/2.2">\n<Document>\n'
                "<name>KML Sample</name>\n<open>1</open>\n"
                "<description>An incomplete example of a KML document - used as an example!</description>\n"
                "</Document>\n</kml>",
                "XML",
                False,
            ),
            ("event-tzuntil", "20260101T000000Z", "TZUNTIL", False),
            ("event-tzid-alias-of", "America/Los_Angeles", "TZID-ALIAS-OF", False),
            ("event-busytype", "BUSY", "BUSYTYPE", False),
            ("event-name", "Portland Linux Kernel Meetup Calendar", "NAME", False),
            ("event-refresh-interval", "P1W", "REFRESH-INTERVAL", True),
            (
                "event-source",
                "https://ikluft.github.io/pdx-lkmu/calendar.ics",
                "SOURCE",
                True,
            ),
            ("event-color", "steelblue", "COLOR", False),
            (
                "event-image",
                "https://ikluft.github.io/pdx-lkmu/images/luckylab_tux.webp",
                "IMAGE",
                True,
            ),
            (
                "event-conference",
                "xmpp:chat-123@conference.example.com",
                "CONFERENCE",
                True,
            ),
            (
                "event-calendar-address",
                "https://ikluft.github.io/pdx-lkmu/calendar.ic",
                "CALENDAR-ADDRESS",
                False,
            ),
            ("event-location-type", "restaurant", "LOCATION-TYPE", False),
            ("event-participant-type", "SPEAKER", "PARTICIPANT-TYPE", False),
            ("event-resource-type", "ROOM", "RESOURCE-TYPE", False),
            ("event-structured-data", "()", "STRUCTURED-DATA", False),
            (
                "event-styled-description",
                "<i>This is a description of something.</i>",
                "STYLED-DESCRIPTION",
                True,
            ),
            ("event-acknowledged", "20250604T084500Z", "ACKNOWLEDGED", False),
            ("event-proximity", "CONNECT", "PROXIMITY", False),
            (
                "event-concept",
                "https://ikluft.github.io/pdx-lkmu/pages/about.html",
                "CONCEPT",
                True,
            ),
            ("event-link", "https://en.wikipedia.org/wiki/Linux_kernel", "LINK", True),
            ("event-refid", "pdx-lkmu-2025-09-18", "REFID", True),
            (
                "event-x-about",
                "https://ikluft.github.io/pdx-lkmu/pages/about.html",
                "X-ABOUT",
                True,
            ),
        ),
    )
    def test_xfer_metadata_to_event_field(
        self, metadata_field: str, value: str, field_name: str, expect_accept: bool
    ) -> None:
        """Tests for xfer_metadata_to_event() which check a field in the resulting iCalendar."""
        # create an iCalendar event for xfer_metadata_to_event() to copy into
        icalendar_event = icalendar.Event(
            dtstart=icalendar.vDatetime(MOCK_TIMES[0]["dtstart"]),
            dtend=icalendar.vDatetime(MOCK_TIMES[0]["dtend"]),
            dtstamp=icalendar.vDatetime(MOCK_TIMES[0]["dtstamp"]),
        )

        # test run of xfer_metadata_to_event() to check if a field gets copied and what it got
        xfer_metadata_to_event({metadata_field: value}, icalendar_event)

        # if the field is marked rejected, verify it wasn't copied to the iCalendar event
        if expect_accept is False:
            assert field_name.upper() not in icalendar_event
            return

        # otherwise test for various types that the correct value was copied
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
