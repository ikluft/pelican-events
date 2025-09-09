"""pelican_events plugin for Pelican.

This plugin looks for and parses an "pelican_events" directory and generates
blog posts with a user-defined event date. (typically in the future)
It also generates an ICalendar v2.0 calendar file.
https://en.wikipedia.org/wiki/ICalendar


original 2014 events plugin by Federico Ceratto
updated in 2021 by Makerspace Esslingen
converted in 2025 to Namespace plugin by Ian Kluft for Portland Linux Kernel Meetup
Released under AGPLv3+ license, see LICENSE
"""

from collections import defaultdict
from datetime import datetime, timedelta, tzinfo
import logging
import os.path
from pprint import pformat
from typing import Any
from zoneinfo import ZoneInfo

from dateutil import rrule
import dateutil.parser
import html2text
import icalendar
from icalendar.prop import vGeo
from recurrent.event_parser import RecurringEvent

from pelican import contents, signals
from pelican.settings import Settings

log = logging.getLogger(__name__)

#
# constants
#

# time multiplier abbreviations for recurring event specifications
TIME_MULTIPLIERS = {
    "w": "weeks",
    "d": "days",
    "h": "hours",
    "m": "minutes",
    "s": "seconds",
}

# iCalendar property names with data to allow or disallow their use, for security reasons
# source ref: https://www.iana.org/assignments/icalendar/icalendar.xhtml
ICAL_DISALLOWED = False
ICAL_ALLOWED = True
ICAL_PROPS = {
    "CALSCALE": [ICAL_DISALLOWED, "[RFC5545, Section 3.7.1]"],
    "METHOD": [ICAL_DISALLOWED, "[RFC5545, Section 3.7.2]"],
    "PRODID": [ICAL_DISALLOWED, "[RFC5545, Section 3.7.3]"],
    "VERSION": [ICAL_DISALLOWED, "[RFC5545, Section 3.7.4]"],
    "ATTACH": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.1.1]"],
    "CATEGORIES": [ICAL_ALLOWED, "[RFC5545, Section 3.8.1.2] [RFC7986, Section 5.6]"],
    "CLASS": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.1.3]"],
    "COMMENT": [ICAL_ALLOWED, "[RFC5545, Section 3.8.1.4]"],
    "DESCRIPTION": [ICAL_ALLOWED, "[RFC5545, Section 3.8.1.5] [RFC7986, Section 5.2]"],
    "GEO": [ICAL_ALLOWED, "[RFC5545, Section 3.8.1.6]"],
    "LOCATION": [ICAL_ALLOWED, "[RFC5545, Section 3.8.1.7]"],
    "PERCENT-COMPLETE": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.1.8]"],
    "PRIORITY": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.1.9]"],
    "RESOURCES": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.1.10]"],
    "STATUS": [ICAL_ALLOWED, "[RFC5545, Section 3.8.1.11]"],
    "SUMMARY": [ICAL_ALLOWED, "[RFC5545, Section 3.8.1.12]"],
    "COMPLETED": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.2.1]"],
    "DTEND": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.2.2]"],
    "DUE": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.2.3]"],
    "DTSTART": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.2.4]"],
    "DURATION": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.2.5]"],
    "FREEBUSY": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.2.6]"],
    "TRANSP": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.2.7]"],
    "TZID": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.3.1]"],
    "TZNAME": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.3.2]"],
    "TZOFFSETFROM": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.3.3]"],
    "TZOFFSETTO": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.3.4]"],
    "TZURL": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.3.5]"],
    "ATTENDEE": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.4.1]"],
    "CONTACT": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.4.2]"],
    "ORGANIZER": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.4.3]"],
    "RECURRENCE-ID": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.4.4]"],
    "RELATED-TO": [
        ICAL_DISALLOWED,
        "[RFC5545, Section 3.8.4.5] [RFC9253, Section 9.1]",
    ],
    "URL": [ICAL_ALLOWED, "[RFC5545, Section 3.8.4.6] [RFC7986, Section 5.5]"],
    "UID": [ICAL_ALLOWED, "[RFC5545, Section 3.8.4.7] [RFC7986, Section 5.3]"],
    "EXDATE": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.5.1]"],
    "EXRULE": [ICAL_DISALLOWED, "Deprecated [RFC2445, Section 4.8.5.2]"],
    "RDATE": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.5.2]"],
    "RRULE": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.5.3]"],
    "ACTION": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.6.1]"],
    "REPEAT": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.6.2]"],
    "TRIGGER": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.6.3]"],
    "CREATED": [ICAL_ALLOWED, "[RFC5545, Section 3.8.7.1]"],
    "DTSTAMP": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.7.2]"],
    "LAST-MODIFIED": [
        ICAL_DISALLOWED,
        "[RFC5545, Section 3.8.7.3] [RFC7986, Section 5.4]",
    ],
    "SEQUENCE": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.7.4]"],
    "REQUEST-STATUS": [ICAL_DISALLOWED, "[RFC5545, Section 3.8.8.3]"],
    "XML": [ICAL_DISALLOWED, "[RFC6321, Section 4.2]"],
    "TZUNTIL": [ICAL_DISALLOWED, "[RFC7808, Section 7.1]"],
    "TZID-ALIAS-OF": [ICAL_DISALLOWED, "[RFC7808, Section 7.2]"],
    "BUSYTYPE": [ICAL_DISALLOWED, "[RFC7953, Section 3.2]"],
    "NAME": [ICAL_ALLOWED, "[RFC7986, Section 5.1]"],
    "REFRESH-INTERVAL": [ICAL_DISALLOWED, "[RFC7986, Section 5.7]"],
    "SOURCE": [ICAL_DISALLOWED, "[RFC7986, Section 5.8]"],
    "COLOR": [ICAL_DISALLOWED, "[RFC7986, Section 5.9]"],
    "IMAGE": [ICAL_ALLOWED, "[RFC7986, Section 5.10]"],
    "CONFERENCE": [ICAL_ALLOWED, "[RFC7986, Section 5.11]"],
    "CALENDAR-ADDRESS": [ICAL_DISALLOWED, "[RFC9073, Section 6.4]"],
    "LOCATION-TYPE": [ICAL_DISALLOWED, "[RFC9073, Section 6.1]"],
    "PARTICIPANT-TYPE": [ICAL_DISALLOWED, "[RFC9073, Section 6.2]"],
    "RESOURCE-TYPE": [ICAL_DISALLOWED, "[RFC9073, Section 6.3]"],
    "STRUCTURED-DATA": [ICAL_DISALLOWED, "[RFC9073, Section 6.6]"],
    "STYLED-DESCRIPTION": [ICAL_ALLOWED, "[RFC9073, Section 6.5]"],
    "ACKNOWLEDGED": [ICAL_DISALLOWED, "[RFC9074, Section 6.1]"],
    "PROXIMITY": [ICAL_DISALLOWED, "[RFC9074, Section 8.1]"],
    "CONCEPT": [ICAL_ALLOWED, "[RFC9253, Section 8.1]"],
    "LINK": [ICAL_ALLOWED, "[RFC9253, Section 8.2]"],
    "REFID": [ICAL_ALLOWED, "[RFC9253, Section 8.3]"],
}

#
# global-scoped variables
#
events = []
localized_events = defaultdict(list)

#
# Exception classes
#


class FieldParseError(ValueError):
    """Exception class for value error in field name."""

    def __init__(self, field_name: str, title: str, error: str) -> None:  # noqa: D107
        super().__init__(
            f"Unable to parse the '{field_name}' field in the event named '{title}': {error}"
        )


class UnknownTimeMultiplier(KeyError):
    """Exception class for unrecognized time multiplier in event duration."""

    def __init__(self, multiplier: str, title: str) -> None:  # noqa: D107
        super().__init__(
            f"Unknown time multiplier '{multiplier}' value in the 'event-duration' field \
                         in the '{title}' event. Supported multipliers are:"
            + " ".join(TIME_MULTIPLIERS)
        )


class DurationParseError(ValueError):
    """Exception class for unrecognized event duration parameter."""

    def __init__(self, param: str, title: str) -> None:  # noqa: D107
        super().__init__(
            f"Unable to parse '{param}' value in the 'event-duration' field in the '{title}' event."
        )


#
# utility functions
#


def strip_html_tags(html):
    """Remove HTML tags for use in iCalendar summary & description."""
    text_maker = html2text.HTML2Text()
    text_maker.escape_snob = True
    text_maker.ignore_links = True
    text_maker.re_space = True
    text_maker.single_line_break = True
    text_maker.images_to_alt = True
    text_maker.ignore_tables = True
    return text_maker.handle(html).rstrip()


def get_tz(settings: Settings) -> None:
    """Get site time zone from PLUGIN_EVENTS.timezone. If found, override the default UTC."""
    return ZoneInfo(settings["PLUGIN_EVENTS"].get("timezone", "UTC"))


def parse_tstamp(
    metadata: dict[str, Any] | None, field_name: str, tz: tzinfo
) -> datetime:
    """Parse a timestamp string in format YYYY-MM-DD HH:MM."""
    if isinstance(metadata[field_name], datetime):
        return datetime.fromisoformat(metadata[field_name].isoformat()).replace(
            tzinfo=tz
        )
    try:
        # return datetime.strptime(metadata[field_name], '%Y-%m-%d %H:%M').replace(tzinfo=tz)
        return dateutil.parser.parse(metadata[field_name]).replace(tzinfo=tz)
    except Exception as e:
        raise FieldParseError(
            field_name=field_name, title=metadata["title"], error=str(e)
        ) from e


def parse_timedelta(metadata) -> timedelta:
    """Parse a timedelta string in format [<num><multiplier> ]* e.g. 2h 30m."""
    chunks = metadata["event-duration"].split()
    tdargs = {}
    for c in chunks:
        try:
            m = TIME_MULTIPLIERS[c[-1]]
            val = float(c[:-1])
            tdargs[m] = val
        except KeyError as e:
            raise UnknownTimeMultiplier(multiplier=c, title=metadata["title"]) from e
        except ValueError as e:
            raise DurationParseError(param=c, title=metadata["title"]) from e
    return timedelta(**tdargs)


def parse_article(content) -> None:
    """Collect articles metadata to be used for building the event calendar."""
    if not isinstance(content, contents.Article):
        return

    if "event-start" not in content.metadata:
        return

    site_tz = get_tz(content.settings)
    dtstart = parse_tstamp(content.metadata, "event-start", site_tz)
    dtend = dtstart  # placeholder defaults to zero duration until overridden

    if "event-end" in content.metadata:
        dtend = parse_tstamp(content.metadata, "event-end", site_tz)

    elif "event-duration" in content.metadata:
        dtdelta = parse_timedelta(content.metadata)
        dtend = dtstart + dtdelta

    else:
        log.error(
            "Either 'event-end' or 'event-duration' must be specified in the event named '%s'",
            content.metadata["title"],
        )

    content.event_plugin_data = {"dtstart": dtstart, "dtend": dtend}

    if "status" not in content.metadata or content.metadata["status"] != "draft":
        events.append(content)


def insert_recurring_events(generator) -> None:
    """Process recurring_events data from PLUGIN_EVENTS configuration."""

    class _AttributeDict(dict):
        __getattr__ = dict.__getitem__
        __setattr__ = dict.__setitem__
        __delattr__ = dict.__delitem__

    if "recurring_events" not in generator.settings["PLUGIN_EVENTS"]:
        return

    site_tz = get_tz(generator.settings)
    for event in generator.settings["PLUGIN_EVENTS"]["recurring_events"]:
        recurring_rule = event["recurring_rule"]
        r = RecurringEvent(now_date=datetime.now(tz=site_tz))
        r.parse(recurring_rule)
        rr = rrule.rrulestr(r.get_RFC_rrule())
        next_occurrence = rr.after(datetime.now(tz=site_tz))

        event_duration = parse_timedelta(event)

        gen_event = _AttributeDict(
            {
                "url": f"pages/{event['page_url']}",
                "location": event["location"],
                "metadata": {
                    "title": event["title"],
                    "summary": event["summary"],
                    "date": next_occurrence,
                    "event-location": event["location"],
                },
                "event_plugin_data": {
                    "dtstart": next_occurrence.astimezone(site_tz),
                    "dtend": next_occurrence.astimezone(site_tz) + event_duration,
                },
            }
        )
        events.append(gen_event)


def field_name_check(fname: str) -> str | None:
    """Validate field name for iCalendar property from content. Returns None if OK, otherwise error string."""
    # allow X- experimental properties
    if fname.upper().startswith("X-"):
        return None

    # otherwise disallow unrecognized properties
    if fname.upper() not in ICAL_PROPS:
        return f"unrecognized iCalendar property '{fname}'"

    # return property status from lookup
    prop_status = ICAL_PROPS[fname.upper()]
    if prop_status[0] == ICAL_ALLOWED:
        return None
    return f"property '{fname}' disallowed, ref: " + prop_status[1]


def xfer_metadata_to_event(
    metadata: dict[str, Any] | None, event: icalendar.cal.Event
) -> None:
    """Copy event-related metadata into the iCalendar event. Filter for relevant headers."""
    if not metadata:
        return

    # process all metadata prefixed with event- and add them to the iCalendar event
    # this allows some flexibility in fields from RFC5545 and related standards
    errors = []
    comment = []
    for field in iter(metadata):
        if field.lower().startswith("event-"):
            fname = field[6:].lower()
            log.debug("processing field %s", fname)

            # save comment property for later, append errors at end if any
            if fname == "comment":
                comment.append(metadata[field])
                log.debug("field saved as comment")
                continue

            # skip start, end and duration because they are generated internally
            if fname in ["start", "end", "duration"]:
                log.debug("field %s skipped because it is processed separately", fname)
                continue

            # skip disallowed properties, add note to errors list for report in comment property
            status = field_name_check(fname)
            if status is not None:
                errors.append(status)
                log.debug("field %s skipped because of error %s", fname, status)
                continue

            # special handling for "GEO" geographic coordinates
            if fname == "geo":
                geo_text = metadata[field]
                event.add("geo", vGeo.from_ical(geo_text))
                log.debug("field %s processed as coordinates %s", fname, geo_text)
                continue

            # special handling for lists (CATEGORIES, RESOURCES)
            if fname in ["categories", "resources"]:
                event.categories = metadata[field].split(",")
                continue

            event.add(fname, metadata[field])

    # process comment property combining user text with any errors that may have occurred
    if len(errors) > 0:
        comment.append("*** errors occurred in processing event ***")
        comment += errors
    if len(comment) > 0:
        event.add("comment", "\n".join(comment))


#
# Pelican plugin API signal handlers
#


def generate_ical_file(generator):
    """Generate an iCalendar file."""
    ics_fname = generator.settings["PLUGIN_EVENTS"]["ics_fname"]
    if not ics_fname:
        return

    if "metadata_field_for_summary" in generator.settings["PLUGIN_EVENTS"]:
        metadata_field_for_event_summary = generator.settings["PLUGIN_EVENTS"][
            "metadata_field_for_summary"
        ]

    if not metadata_field_for_event_summary:
        metadata_field_for_event_summary = "summary"

    ics_fname = os.path.join(generator.settings["OUTPUT_PATH"], ics_fname)
    log.debug("Generating calendar at %s with %d events", ics_fname, len(events))

    ical = icalendar.Calendar()
    ical.add("prodid", "-//My calendar product//mxm.dk//")
    ical.add("version", "2.0")

    # add site timezone info for VTIMEZONE section to beginning of icalendar object's list
    site_tz = get_tz(generator.settings)
    ical.add_component(icalendar.cal.Timezone.from_tzinfo(site_tz))

    default_lang = generator.settings["DEFAULT_LANG"]
    curr_events = events if not localized_events else localized_events[default_lang]

    # get list of blog entries with metadata indicating they are events
    filtered_list = filter(
        lambda x: x.event_plugin_data["dtstart"] >= datetime.now(tz=site_tz),
        curr_events,
    )

    for e in filtered_list:
        if "date" in e.metadata:
            dtstamp = parse_tstamp(e.metadata, "date", site_tz)
        else:
            dtstamp = datetime.now(tz=site_tz)
        icalendar_event = icalendar.Event(
            summary=strip_html_tags(e.metadata[metadata_field_for_event_summary]),
            dtstart=icalendar.vDatetime(e.event_plugin_data["dtstart"]),
            dtend=icalendar.vDatetime(e.event_plugin_data["dtend"]),
            dtstamp=icalendar.vDatetime(dtstamp),
            priority=5,
            uid=generator.settings["SITEURL"] + e.url,
        )

        # copy article text to description field without HTML tags
        content_text = e.content
        icalendar_event.add("description", strip_html_tags(content_text))

        # copy event- prefixed fields to icalendar object
        xfer_metadata_to_event(e.metadata, icalendar_event)
        log.debug("Added icalendar event: %s", pformat(icalendar_event))

        # save the newly-created event structure in the calendar for export
        ical.add_component(icalendar_event)

    # create directory if it doesn't exist
    os.makedirs(os.path.dirname(ics_fname), exist_ok=True)

    # write iCalendar content to file
    with open(ics_fname, "wb") as f:
        f.write(ical.to_ical())


def generate_localized_events(generator):
    """Generate localized events dict if i18n_subsites plugin is active."""
    if "i18n_subsites" in generator.settings["PLUGINS"]:
        if not os.path.exists(generator.settings["OUTPUT_PATH"]):
            os.makedirs(generator.settings["OUTPUT_PATH"])

        for e in events:
            if "lang" in e.metadata:
                localized_events[e.metadata["lang"]].append(e)
            else:
                log.debug("event %s contains no lang attribute", e.metadata["title"])


def populate_context_variables(generator):
    """Populate the event_list and upcoming_events_list variables to be used in jinja templates."""
    site_tz = get_tz(generator.settings)

    def filter_future(ev):
        return ev.event_plugin_data["dtend"].date() >= datetime.now(tz=site_tz).date()

    if not localized_events:
        generator.context["events_list"] = sorted(
            events,
            reverse=True,
            key=lambda ev: (
                ev.event_plugin_data["dtstart"],
                ev.event_plugin_data["dtend"],
            ),
        )
        generator.context["upcoming_events_list"] = sorted(
            filter(filter_future, events),
            key=lambda ev: (
                ev.event_plugin_data["dtstart"],
                ev.event_plugin_data["dtend"],
            ),
        )
    else:
        generator.context["events_list"] = {
            k: sorted(
                v,
                reverse=True,
                key=lambda ev: (
                    ev.event_plugin_data["dtstart"],
                    ev.event_plugin_data["dtend"],
                ),
            )
            for k, v in localized_events.items()
        }

        generator.context["upcoming_events_list"] = {
            k: sorted(
                filter(filter_future, v),
                key=lambda ev: (
                    ev.event_plugin_data["dtstart"],
                    ev.event_plugin_data["dtend"],
                ),
            )
            for k, v in localized_events.items()
        }


def initialize_events(article_generator):
    """Clear events list to support plugins with multiple generation passes like i18n_subsites."""
    del events[:]
    localized_events.clear()
    insert_recurring_events(article_generator)


def register():
    """Register Pelican plugin API signal handler functions.

    See https://docs.getpelican.com/en/latest/plugins.html#list-of-signals for descriptions of signals.
    """
    signals.article_generator_init.connect(initialize_events)
    signals.content_object_init.connect(parse_article)
    signals.article_generator_finalized.connect(generate_localized_events)
    signals.article_generator_finalized.connect(generate_ical_file)
    signals.article_generator_finalized.connect(populate_context_variables)
