"""Test configuration for pelican-events plugin of Pelican site generator."""

PLUGIN_EVENTS = {
    "metadata_field_for_summary": "title",
    "ics_fname": "calendar.ics",
    "test_timestamp": "2025-09-04 11:00:00",  # fixed time for this test only, before event time in content/
}
AUTHOR = "Pelican Events Plugin Developers"
SITENAME = "Pelican Events Plugin Test Case"
SITEURL = ""
TIMEZONE = "US/Pacific"

PATH = "content"
DEFAULT_LANG = "en"

# feed generation is not needed for iCalendar event testing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
