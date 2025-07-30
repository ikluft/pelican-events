#!python
"""
pelican_events plugin for Pelican
=========================

This plugin looks for and parses an "pelican_events" directory and generates
blog posts with a user-defined event date. (typically in the future)
It also generates an ICalendar v2.0 calendar file.
https://en.wikipedia.org/wiki/ICalendar


original 2014 events plugin by Federico Ceratto
updated in 2021 by Makerspace Esslingen
converted in 2025 to Namespace plugin by Ian Kluft for Portland Linux Kernel Meetup
Released under AGPLv3+ license, see LICENSE
"""
from io import StringIO
import logging
import os.path
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from dateutil import rrule
import icalendar
from recurrent.event_parser import RecurringEvent
import pytz
import re
from pelican import signals, utils, contents
from collections import namedtuple, defaultdict

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
    def __init__(self):
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


def parse_tstamp(metadata, field_name):
    """Parse a timestamp string in format "YYYY-MM-DD HH:MM"

    :returns: datetime
    """
    try:
        # assume local system timezone when parsing datetime
        return datetime.strptime(metadata[field_name], '%Y-%m-%d %H:%M').astimezone()
    except Exception as e:
        log.error("Unable to parse the '%s' field in the event named '%s': %s" \
                  % (field_name, metadata['title'], e))
        raise


def parse_timedelta(metadata):
    """Parse a timedelta string in format [<num><multiplier> ]*
    e.g. 2h 30m

    :returns: timedelta
    """

    chunks = metadata['event-duration'].split()
    tdargs = {}
    for c in chunks:
        try:
            m = TIME_MULTIPLIERS[c[-1]]
            val = float(c[:-1])
            tdargs[m] = val
        except KeyError:
            log.error("""Unknown time multiplier '%s' value in the \
'event-duration' field in the '%s' event. Supported multipliers \
are: '%s'.""" % (c, metadata['title'], ' '.join(TIME_MULTIPLIERS)))
            raise RuntimeError("Unknown time multiplier '%s'" % c)
        except ValueError:
            log.error("""Unable to parse '%s' value in the 'event-duration' \
field in the '%s' event.""" % (c, metadata['title']))
            raise ValueError("Unable to parse '%s'" % c)
    return timedelta(**tdargs)


def basic_utc_isoformat(datetime_value):
    utc_datetime = datetime_value.astimezone(timezone.utc)
    pure_datetime = utc_datetime.replace(tzinfo=None)
    iso_timestamp = pure_datetime.isoformat(timespec='seconds')
    stripped_iso_timestamp = iso_timestamp.replace('-', '').replace(':', '')

    return stripped_iso_timestamp + 'Z'


def parse_article(content):
    """Collect articles metadata to be used for building the event calendar

    :returns: None
    """
    if not isinstance(content, contents.Article):
        return

    if 'event-start' not in content.metadata:
        return

    dtstart = parse_tstamp(content.metadata, 'event-start')

    if 'event-end' in content.metadata:
        dtend = parse_tstamp(content.metadata, 'event-end')

    elif 'event-duration' in content.metadata:
        dtdelta = parse_timedelta(content.metadata)
        dtend = dtstart + dtdelta

    else:
        msg = "Either 'event-end' or 'event-duration' must be" + \
            " speciefied in the event named '%s'" % content.metadata['title']
        log.error(msg)
        raise ValueError(msg)

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

    for event in generator.settings['PLUGIN_EVENTS']['recurring_events']:
        recurring_rule = event['recurring_rule']
        r = RecurringEvent(now_date=datetime.now())
        r.parse(recurring_rule)
        rr = rrule.rrulestr(r.get_RFC_rrule())
        next_occurrence = rr.after(datetime.now())

        event_duration = parse_timedelta(event)

        event = AttributeDict({
            'url': f"pages/{event['page_url']}",
            'location': event['location'],
            'metadata': dict({
                'title': event['title'],
                'summary': event['summary'],
                'date': next_occurrence,
                'event-location': event['location']
            }),
            'event_plugin_data': dict({
                'dtstart': next_occurrence.astimezone(),
                'dtend': next_occurrence.astimezone() + event_duration,
            })
        })
        events.append(event)


def generate_ical_file(generator):
    """Generate an iCalendar file
    """
    global events
    ics_fname = generator.settings['PLUGIN_EVENTS']['ics_fname']
    if not ics_fname:
        return

    if 'metadata_field_for_summary' in generator.settings['PLUGIN_EVENTS']:
        metadata_field_for_event_summary = generator.settings['PLUGIN_EVENTS']['metadata_field_for_summary']

    if not metadata_field_for_event_summary:
        metadata_field_for_event_summary = 'summary'

    ics_fname = os.path.join(generator.settings['OUTPUT_PATH'], ics_fname)
    log.debug("Generating calendar at %s with %d events" % (ics_fname, len(events)))

    ical = icalendar.Calendar()
    ical.add('prodid', '-//My calendar product//mxm.dk//')
    ical.add('version', '2.0')

    DEFAULT_LANG = generator.settings['DEFAULT_LANG']
    curr_events = events if not localized_events else localized_events[DEFAULT_LANG]

    filtered_list = filter(lambda x: x.event_plugin_data["dtstart"] >= datetime.now().astimezone(), curr_events)

    for e in filtered_list:
        icalendar_event = icalendar.Event(
            summary=strip_html_tags(e.metadata[metadata_field_for_event_summary]),
            dtstart=basic_utc_isoformat(e.event_plugin_data["dtstart"]),
            dtend=basic_utc_isoformat(e.event_plugin_data["dtend"]),
            dtstamp=basic_utc_isoformat(e.metadata['date']),
            priority=5,
            uid=generator.settings['SITEURL'] + e.url,
        )
        if 'event-location' in e.metadata:
            icalendar_event.add('location', e.metadata['event-location'])

        ical.add_component(icalendar_event)

    with open(ics_fname, 'wb') as f:
        f.write(ical.to_ical())


def generate_localized_events(generator):
    """ Generates localized events dict if i18n_subsites plugin is active """

    if "i18n_subsites" in generator.settings["PLUGINS"]:
        if not os.path.exists(generator.settings['OUTPUT_PATH']):
            os.makedirs(generator.settings['OUTPUT_PATH'])

        for e in events:
            if "lang" in e.metadata:
                localized_events[e.metadata["lang"]].append(e)
            else:
                log.debug("event %s contains no lang attribute" % (e.metadata["title"],))


def populate_context_variables(generator):
    """
    Populate the event_list and upcoming_events_list variables to be used in jinja templates
    """

    filter_future = lambda ev: ev.event_plugin_data["dtend"].date() >= datetime.now().date()

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
    """
    Clears the events list before generating articles to properly support plugins with
    multiple generation passes like i18n_subsites
    """

    del events[:]
    localized_events.clear()
    insert_recurring_events(article_generator)

def register():
    signals.article_generator_init.connect(initialize_events)
    signals.content_object_init.connect(parse_article)
    signals.article_generator_finalized.connect(generate_localized_events)
    signals.article_generator_finalized.connect(generate_ical_file)
    signals.article_generator_finalized.connect(populate_context_variables)
