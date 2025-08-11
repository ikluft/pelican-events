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
from html.parser import HTMLParser
from io import StringIO
import logging
import os.path
from pprint import pformat
from typing import Any
from zoneinfo import ZoneInfo

from dateutil import rrule
import dateutil.parser
import icalendar
from recurrent.event_parser import RecurringEvent

from pelican import contents, signals
from pelican.settings import Settings

log = logging.getLogger(__name__)

TIME_MULTIPLIERS = {
    'w': 'weeks',
    'd': 'days',
    'h': 'hours',
    'm': 'minutes',
    's': 'seconds'
}

events = []
localized_events = defaultdict(list)


class MLStripper(HTMLParser):
    """HTMLParser wrapper to strip HTML tags and pull out plain text."""

    def __init__(self):
        """Initialize MLStripper object as an HTMLParser instance."""
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, d):
        self.text.write(d)

    def get_data(self):
        return self.text.getvalue()


def strip_html_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def get_tz(settings: Settings) -> None:
    """Get site time zone from PLUGIN_EVENTS.timezone. If found, override the default UTC."""
    return ZoneInfo(settings['PLUGIN_EVENTS'].get('timezone', 'UTC'))


def parse_tstamp(metadata: dict[str, Any] | None, field_name: str, tz: tzinfo) -> datetime:
    """Parse a timestamp string in format YYYY-MM-DD HH:MM."""
    if isinstance(metadata[field_name], datetime):
        return datetime.fromisoformat(metadata[field_name].isoformat()).replace(tzinfo=tz)
    try:
        # return datetime.strptime(metadata[field_name], '%Y-%m-%d %H:%M').replace(tzinfo=tz)
        return dateutil.parser.parse(metadata[field_name]).replace(tzinfo=tz)
    except Exception as e:
        title = metadata['title']
        raise ValueError(f"Unable to parse the '{field_name}' field in the event named '{title}': {e}") from e


def parse_timedelta(metadata) -> timedelta:
    """Parse a timedelta string in format [<num><multiplier> ]* e.g. 2h 30m."""
    chunks = metadata['event-duration'].split()
    tdargs = {}
    for c in chunks:
        try:
            m = TIME_MULTIPLIERS[c[-1]]
            val = float(c[:-1])
            tdargs[m] = val
        except KeyError as e:
            log.exception("""Unknown time multiplier '%s' value in the \
'event-duration' field in the '%s' event. Supported multipliers \
are: '%s'.""", c, metadata['title'], ' '.join(TIME_MULTIPLIERS))
            raise RuntimeError(f"Unknown time multiplier '{c}'") from e
        except ValueError as e:
            log.exception("""Unable to parse '%s' value in the 'event-duration' \
field in the '%s' event.""", c, metadata['title'])
            raise ValueError(f"Unable to parse '{c}'") from e
    return timedelta(**tdargs)


def parse_article(content) -> None:
    """Collect articles metadata to be used for building the event calendar."""
    if not isinstance(content, contents.Article):
        return

    if 'event-start' not in content.metadata:
        return

    site_tz = get_tz(content.settings)
    dtstart = parse_tstamp(content.metadata, 'event-start', site_tz)
    dtend = dtstart  # placeholder defaults to zero duration until overridden

    if 'event-end' in content.metadata:
        dtend = parse_tstamp(content.metadata, 'event-end', site_tz)

    elif 'event-duration' in content.metadata:
        dtdelta = parse_timedelta(content.metadata)
        dtend = dtstart + dtdelta

    else:
        log.error("Either 'event-end' or 'event-duration' must be specified in the event named '%s'",
                  content.metadata['title'])

    content.event_plugin_data = {"dtstart": dtstart, "dtend": dtend}

    if 'status' not in content.metadata or content.metadata['status'] != 'draft':
        events.append(content)


def insert_recurring_events(generator):
    global events

    class AttributeDict(dict):
        __getattr__ = dict.__getitem__
        __setattr__ = dict.__setitem__
        __delattr__ = dict.__delitem__

    if 'recurring_events' not in generator.settings['PLUGIN_EVENTS']:
        return

    site_tz = get_tz(generator.settings)
    for event in generator.settings['PLUGIN_EVENTS']['recurring_events']:
        recurring_rule = event['recurring_rule']
        r = RecurringEvent(now_date=datetime.now(tz=site_tz))
        r.parse(recurring_rule)
        rr = rrule.rrulestr(r.get_RFC_rrule())
        next_occurrence = rr.after(datetime.now(tz=site_tz))

        event_duration = parse_timedelta(event)

        gen_event = AttributeDict({
            'url': f"pages/{event['page_url']}",
            'location': event['location'],
            'metadata': {
                'title': event['title'],
                'summary': event['summary'],
                'date': next_occurrence,
                'event-location': event['location']
            },
            'event_plugin_data': {
                'dtstart': next_occurrence.astimezone(site_tz),
                'dtend': next_occurrence.astimezone(site_tz) + event_duration,
            }
        })
        events.append(gen_event)


def xfer_metadata_to_event(metadata: dict[str, Any] | None, event: icalendar.cal.Event) -> None:
    """Copy event-related metadata into the event structure."""
    if not metadata:
        return
    # process all metadata prefixed with event- and add them to the iCalendar event
    # this allows some flexibility in fields from RFC5545 and related standards
    for field in iter(metadata):
        if field.lower().startswith("event-"):
            fname = field[6:].lower()
            if fname not in ["start", "end", "duration"]:
                event.add(fname.lower(), metadata[field])


def generate_ical_file(generator):
    """Generate an iCalendar file."""
    global events
    ics_fname = generator.settings['PLUGIN_EVENTS']['ics_fname']
    if not ics_fname:
        return

    if 'metadata_field_for_summary' in generator.settings['PLUGIN_EVENTS']:
        metadata_field_for_event_summary = generator.settings['PLUGIN_EVENTS']['metadata_field_for_summary']

    if not metadata_field_for_event_summary:
        metadata_field_for_event_summary = 'summary'

    ics_fname = os.path.join(generator.settings['OUTPUT_PATH'], ics_fname)
    log.debug("Generating calendar at %s with %d events", ics_fname, len(events))

    ical = icalendar.Calendar()
    ical.add('prodid', '-//My calendar product//mxm.dk//')
    ical.add('version', '2.0')

    default_lang = generator.settings['DEFAULT_LANG']
    curr_events = events if not localized_events else localized_events[default_lang]

    site_tz = get_tz(generator.settings)
    filtered_list = filter(lambda x: x.event_plugin_data["dtstart"] >= datetime.now(tz=site_tz), curr_events)

    for e in filtered_list:
        if 'date' in e.metadata:
            dtstamp = parse_tstamp(e.metadata, 'date', site_tz)
        else:
            dtstamp = datetime.now(tzinfo=site_tz)
        icalendar_event = icalendar.Event(
            summary=strip_html_tags(e.metadata[metadata_field_for_event_summary]),
            dtstart=e.event_plugin_data["dtstart"],
            dtend=e.event_plugin_data["dtend"],
            dtstamp=dtstamp,
            priority=5,
            uid=generator.settings['SITEURL'] + e.url,
        )
        # copy event- prefixed fields to icalendar object
        xfer_metadata_to_event(e.metadata, icalendar_event)
        log.debug("Added icalendar event: %s", pformat(icalendar_event))

        ical.add_component(icalendar_event)

    with open(ics_fname, 'wb') as f:
        f.write(ical.to_ical())


def generate_localized_events(generator):
    """Generates localized events dict if i18n_subsites plugin is active."""
    if "i18n_subsites" in generator.settings["PLUGINS"]:
        if not os.path.exists(generator.settings['OUTPUT_PATH']):
            os.makedirs(generator.settings['OUTPUT_PATH'])

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
        generator.context['events_list'] = sorted(events, reverse=True,
                                                  key=lambda ev: (ev.event_plugin_data["dtstart"],
                                                                  ev.event_plugin_data["dtend"]))
        generator.context['upcoming_events_list'] = sorted(filter(filter_future, events),
                                                           key=lambda ev: (ev.event_plugin_data["dtstart"],
                                                                           ev.event_plugin_data["dtend"]))
    else:
        generator.context['events_list'] = {k: sorted(v, reverse=True,
                                                      key=lambda ev: (ev.event_plugin_data["dtstart"],
                                                                      ev.event_plugin_data["dtend"]))
                                            for k, v in localized_events.items()}

        generator.context['upcoming_events_list'] = {k: sorted(filter(filter_future, v),
                                                     key=lambda ev: (ev.event_plugin_data["dtstart"],
                                                                     ev.event_plugin_data["dtend"]))
                                                     for k, v in localized_events.items()}


def initialize_events(article_generator):
    """Clear events list to support plugins with multiple generation passes like i18n_subsites."""
    del events[:]
    localized_events.clear()
    insert_recurring_events(article_generator)


def register():
    signals.article_generator_init.connect(initialize_events)
    signals.content_object_init.connect(parse_article)
    signals.article_generator_finalized.connect(generate_localized_events)
    signals.article_generator_finalized.connect(generate_ical_file)
    signals.article_generator_finalized.connect(populate_context_variables)
