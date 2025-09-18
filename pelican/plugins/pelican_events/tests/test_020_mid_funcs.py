"""test_020_mid_funcs.py - unit tests for mid-level functions in pelican_events plugin for Pelican."""
# by Ian Kluft

from datetime import datetime
from typing import ClassVar
from zoneinfo import ZoneInfo

import pytest

from pelican.contents import Article
from pelican.plugins.pelican_events import parse_article
from pelican.tests.support import get_settings


class TestMidFuncsData:
    """Test class with fixture data for mid-level functions in pelican_events plugin."""

    in_settings: ClassVar[dict[str, str]] = {
        "PLUGIN_EVENTS": {
            "timezone": "US/Pacific",
            "ics_fname": "calendar.ics",
        },
    }
    in_articles: ClassVar[list[Article]] = [
        Article(  # sample event, specified by end time
            "",
            settings=get_settings(PLUGIN_EVENTS=in_settings["PLUGIN_EVENTS"]),
            metadata={
                "title": "test 1",
                "event-start": "2025-09-18 18:00",
                "event-end": "2025-09-18 21:00",
            },
        ),
        Article(  # same as previous event, specified by duration
            "",
            settings=get_settings(PLUGIN_EVENTS=in_settings["PLUGIN_EVENTS"]),
            metadata={
                "title": "test 2",
                "event-start": "2025-09-18 18:00",
                "event-duration": "3h",
            },
        ),
        Article(  # event fails to specify end or duration - should be zero duration
            "",
            settings=get_settings(PLUGIN_EVENTS=in_settings["PLUGIN_EVENTS"]),
            metadata={
                "title": "test 3",
                "event-start": "2025-09-18 18:00",
            },
        ),
        Article(  # event fails to specify start - should be skipped by events plugin
            "",
            settings=get_settings(PLUGIN_EVENTS=in_settings["PLUGIN_EVENTS"]),
            metadata={
                "title": "test 4",
            },
        ),
        "this is a string",  # test for non-Article - should be skipped by events plugin
    ]

    @pytest.mark.parametrize(
        "in_article, event_plugin_data",
        [
            (
                in_articles[0],
                {
                    "dtstart": datetime(
                        2025,
                        9,
                        18,
                        18,
                        0,
                        tzinfo=ZoneInfo(in_settings["PLUGIN_EVENTS"]["timezone"]),
                    ),
                    "dtend": datetime(
                        2025,
                        9,
                        18,
                        21,
                        0,
                        tzinfo=ZoneInfo(in_settings["PLUGIN_EVENTS"]["timezone"]),
                    ),
                },
            ),
            (
                in_articles[1],
                {
                    "dtstart": datetime(
                        2025,
                        9,
                        18,
                        18,
                        0,
                        tzinfo=ZoneInfo(in_settings["PLUGIN_EVENTS"]["timezone"]),
                    ),
                    "dtend": datetime(
                        2025,
                        9,
                        18,
                        21,
                        0,
                        tzinfo=ZoneInfo(in_settings["PLUGIN_EVENTS"]["timezone"]),
                    ),
                },
            ),
            (
                in_articles[2],
                {
                    "dtstart": datetime(
                        2025,
                        9,
                        18,
                        18,
                        0,
                        tzinfo=ZoneInfo(in_settings["PLUGIN_EVENTS"]["timezone"]),
                    ),
                    "dtend": datetime(
                        2025,
                        9,
                        18,
                        18,
                        0,
                        tzinfo=ZoneInfo(in_settings["PLUGIN_EVENTS"]["timezone"]),
                    ),
                },
            ),
            (
                in_articles[3],
                None,
            ),
            (
                in_articles[4],
                None,
            ),
        ],
    )
    def test_parse_article_epd(self, in_article, event_plugin_data) -> None:
        """Tests for parse_article() checing event_plugin_data."""
        parse_article(in_article)  # modifies in_article
        if hasattr(in_article, "event_plugin_data"):
            assert in_article.event_plugin_data == event_plugin_data
        else:
            assert event_plugin_data is None  # test for non-existence using None

    @pytest.mark.parametrize(
        "in_article, log",
        [
            (
                in_articles[0],
                "",
            ),
            (
                in_articles[1],
                "",
            ),
            (
                in_articles[2],
                "Either 'event-end' or 'event-duration' must be specified in the event named 'test 3'",
            ),
            (
                in_articles[3],
                "",
            ),
            (
                in_articles[4],
                "",
            ),
        ],
    )
    def test_parse_article_log(self, in_article, log, caplog) -> None:
        """Tests for parse_article() which generate logs."""
        parse_article(in_article)  # modifies in_article
        assert log in caplog.text
