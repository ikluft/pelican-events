Pelican Events: iCalendar Plugin for Pelican
============================================

[![build](https://github.com/ikluft/pelican-events/actions/workflows/main.yml/badge.svg)](https://github.com/ikluft/pelican-events/actions/workflows/main.yml)
[![PyPI Version](https://img.shields.io/pypi/v/pelican-events)](https://pypi.org/project/pelican-events/)
![License](https://img.shields.io/pypi/l/pelican-events?color=blue)

Pelican plugin to embed event data in posts and generate iCalendar data

This project was created for the [Portland Linux Kernel Meetup (PDX-LKMU)](https://ikluft.github.io/pdx-lkmu/) site. This is a refresh of the 2015 events plugin and includes improvements from Makerspace Esslingen.

This plugin/module was made to generate iCalendar data for the Linux Kernel Meetup in Portland, Oregon and also to be general-use for other groups who find it helpful. The PDX-LKMU site uses the static site generator Pelican.

We intended to use the previously-existing "events" plugin from 2015 to automatically generate iCalendar entries from events with calendar metadata. But the events plugin was unmaintained. It also didn't support enough iCalendar properties for our needs, where we need the Portland-area Calagator tech events calendar site to process our iCalendar output. Also, the original events plugin was so old it didn't implement the current "namespace plugin" standard for Pelican plugins, being a standalone Python module. That's what this project was intended to solve - rewrite it as a Python module and bring it up to current plugin standards. As part of the process, time zones are now handled correctly too.

Contents
--------

* <a href="#installation">Installation</a>
  * <a href="#dependencies">Dependencies</a>
  * <a href="#building_from_source">Building from source</a>
  * <a href="#settings">Settings</a>
* <a href="#usage">Usage</a>
  * <a href="#icalendar_property_support">iCalendar property support</a>
  * <a href="#example_usage">Example usage</a>
* <a href="#contributing">Contributing</a>
  * <a href="#development_environment">Development Environment</a>
* <a href="#license">License</a>
* <a href="#credits">Credits</a>

<a name="installation">Installation</a>
------------

This plugin is available as ['pelican-events' on PyPI](https://pypi.org/project/pelican-events/) and can be installed via:

    python -m pip install pelican-events

### <a name="dependencies">Dependencies</a>

Whether installing from PyPI with pip, or building from source, you may install dependencies from OS packages if you prefer. But you will have to do that first.

The pelican-events plugin depends on the following Python packages:

  * pelican
  * icalendar
  * recurrent
  * html2text
  * and others

Some dependencies are available for installation via OS-native packages.

  * on RPM-based systems (Fedora, RHEL, Rocky, Alma, etc):

    dnf install python3-pelican python3-icalendar python3-html2text

  * on DEB-based systems (Debian, Ubuntu, etc):

    apt install pelican python3-icalendar python3-html2text

### <a name="building_from_source">Building from source</a>

Pelican uses PDM (Python Dependency Manager) for builds and Ruff as its linter. So the Pelican-Events plugin does too. PDM determines the project's dependencies with the command

    pdm lock

Dependencies which aren't available as OS-native packages may be installed via PDM:

    pdm install

### <a name="settings">Settings</a>

As long as you have not explicitly added a `PLUGINS` setting to your Pelican settings file, then the newly-installed plugin should be detected as a Python module with a "pelican.plugins" prefix, and then automatically enabled. Otherwise, you must add `pelican-events` to your existing `PLUGINS` list. For more information, please see the [How to Use Plugins](https://docs.getpelican.com/en/latest/plugins.html#how-to-use-plugins) documentation.

Define settings in pelicanconf.py with the PLUGIN_EVENTS variable:

    PLUGIN_EVENTS = {
        'ics_fname': 'calendar.ics',
        'metadata_field_for_summary': 'title',
    },
    'TIMEZONE': 'US/Pacific',  # use your local time zone

Settings available in the PLUGIN_EVENTS dictionary variable:

  * ics_fname: where the iCal file is written - disables plugin if not set
  * metadata_field_for_summary: which field to use for the event summary, default: summary
  * recurring_events: recurring event rules in [recurrent module](https://github.com/kvh/recurrent) format. If not set, then recurring events will not be generated. This feature was added by Makerspace Esslingen. *(This feature is now minimally tested with some unit tests. But we don't use it on the PDX-LKMU site.)*

Settings used from Pelican's top-level configuration:
  * TIMEZONE: time zone to use for events in icalendar output, default: UTC. If set, this must be an official time zone name from the [IANA Time Zone Database](https://www.iana.org/time-zones).

<a name="usage">Usage</a>
-----

See Pelican's [How to Use Plugins](https://docs.getpelican.com/en/latest/plugins.html#how-to-use-plugins) documentation to get a Pelican site started.

You can use the following metadata (headers above the article text) in articles in your Pelican content, which are from the original 2015 events plugin:

  * event-start: When the event will start in "YYYY-MM-DD hh:mm"
  * event-end: When the event will stop in "YYYY-MM-DD hh:mm"
  * event-duration: The duration of the event [note 1]
  * event-location: Where the event takes place [[RFC5545, Section 3.8.1.7](https://www.rfc-editor.org/rfc/rfc5545#section-3.8.1.7)]

Note 1: To specify the event duration, use a number followed by a time unit, for example "2h 30m"

  * w: weeks
  * d: days
  * h: hours
  * m: minutes
  * s: seconds

### <a name="icalendar_property_support">iCalendar property support</a>

Support for more iCalendar properties, prefixed with "event-" in the post metadata, were added in the update for the Portland Linux Kernel Meetup.

  * event-categories: comma-separated list of arbitrary categories [[RFC5545, Section 3.8.1.2](https://www.rfc-editor.org/rfc/rfc5545#section-3.8.1.2), [RFC7986, Section 5.6](https://www.rfc-editor.org/rfc/rfc7986#section-5.6)]
  * event-comment: comment to the calendar user [[RFC5545, Section 3.8.1.4](https://www.rfc-editor.org/rfc/rfc5545#section-3.8.1.4)]
  * event-description: textual description of the activity [[RFC5545, Section 3.8.1.5](https://www.rfc-editor.org/rfc/rfc5545#section-3.8.1.5), [RFC7986, Section 5.2](https://www.rfc-editor.org/rfc/rfc7986#section-5.2)]
  * event-geo: latitude and longitude as floating point numbers separated by semicolon [[RFC5545, Section 3.8.1.6](https://www.rfc-editor.org/rfc/rfc5545#section-3.8.1.6)]
  * event-status: status of the event as "tentative", "confirmed", or "cancelled" [[RFC5545, Section 3.8.1.11](https://www.rfc-editor.org/rfc/rfc5545#section-3.8.1.11)]
  * event-summary: short one-line summary about the activity [[RFC5545, Section 3.8.1.12](https://www.rfc-editor.org/rfc/rfc5545#section-3.8.1.12)]
  * event-url: URL online location of a more dynamic rendition of the calendar information [[RFC5545, Section 3.8.4.6](https://www.rfc-editor.org/rfc/rfc5545#section-3.8.4.6), [RFC7986, Section 5.5](https://www.rfc-editor.org/rfc/rfc7986#section-5.5)]
  * event-uid: globally unique identifier [[RFC5545, Section 3.8.4.7](https://www.rfc-editor.org/rfc/rfc5545#section-3.8.4.7), [RFC7986, Section 5.5](https://www.rfc-editor.org/rfc/rfc7986#section-5.3)]
  * event-created: date and time that the calendar information was created [[RFC5545, Section 3.8.7.1](https://www.rfc-editor.org/rfc/rfc5545#section-3.8.7.1)]
  * event-name: name for presenting the calendar data to a user [[RFC7986, Section 5.1](https://www.rfc-editor.org/rfc/rfc7986#section-5.1)]
  * event-image: image for the event via a URI or inline data [[RFC7986, Section 5.10](https://www.rfc-editor.org/rfc/rfc7986#section-5.10)]
  * event-conference: information for accessing a conferencing system for attendees [[RFC7986, Section 5.11](https://www.rfc-editor.org/rfc/rfc7986#section-5.11)]
  * event-styled-description: rich-text description of the activity [[RFC9073, Section 6.5](https://www.rfc-editor.org/rfc/rfc9073#name-styled-description)]
  * event-concept: formal categories or classifications of the event [[RFC9253, Section 8.1](https://www.rfc-editor.org/rfc/rfc9253#section-8.1)]
  * event-link: additional information related to the component [[RFC9253, Section 8.2](https://www.rfc-editor.org/rfc/rfc9253#section-8.2)]
  * event-refid: free-form text that creates an identifier for associated components [[RFC9253, Section 8.3](https://www.rfc-editor.org/rfc/rfc9253#section-8.3)]
  * event-x-\*: non-standard experimental properties [[RFC5545, Section 3.8.8.2](https://www.rfc-editor.org/rfc/rfc5545#section-3.8.8.2)]

However, not all iCalendar properties make sense in the context of a public post. Those intended for private emails were excluded in a security review to prevent misconfiguration and mischief. A few were disallowed because they are redundant with metadata settings that generate those properties in the original events plugin. If you think you need a property which was excluded, [submit an issue to the project](https://github.com/ikluft/pelican-events/issues) stating which property is requested and explaining why it should be allowed in a public setting.

The disallowed iCalendar properties are: *acknowledged action attach attendee busytype calendar-address calscale class color completed contact dtend dtstamp dtstart due duration exdate exrule freebusy last-modified location-type method organizer participant-type percent-complete priority prodid proximity rdate recurrence-id refresh-interval related-to repeat request-status resources resource-type rrule sequence source structured-data transp trigger tzid tzid-alias-of tzname tzoffsetfrom tzoffsetto tzuntil tzurl version xml*

### <a name="example_usage">Example usage</a>

The pelican-events plugin was made for and is used by the [Portland Linux Kernel Meetup](https://ikluft.github.io/pdx-lkmu/) in Portland, Oregon, USA.

<a name="contributing">Contributing</a>
------------

Contributions are welcome and much appreciated. Every little bit helps. You can contribute by improving the documentation, adding missing features, and fixing bugs. You can also help out by reviewing and commenting on [existing issues][].

To start contributing to this plugin, review the [Contributing to Pelican][] documentation, beginning with the **Contributing Code** section.

[existing issues]: https://github.com/ikluft/pelican-events/issues
[Contributing to Pelican]: https://docs.getpelican.com/en/latest/contribute.html

### <a name="development_environment">Development Environment</a>

Upon commit to the repository, the Github workflow will perform unit tests on current versions of Python.
So prior to checking in code, at least run the tests on your local environment to make sure you won't break the build.

    pdm run invoke tests

It will also do a lint check which shows diffs that the linter wants for proper formatting.
This is also marked as a build failure if it doesn't work.

    pdm run invoke lint --diff

If it says there are changes to make, you can run this in your workspace to apply those changes.

    pdm run invoke lint --fix

To make a local git hook to perform these checks before each commit, make a symbolic link as follows:

    ln -s "../../docs/pre-commit-git-hook.sh" .git/hooks/pre-commit

### <a name="changelog-based-versioning">Changelog-based versioning</a>

The [CHANGELOG.md](CHANGELOG.md) file uses the [Keep a Changelog](https://keepachangelog.com/) format to select the next version number.
Version numbers follow [Semantic Versioning](https://semver.org/).
The version numbers are strings containing 3 integer numbers indicating major, minor and patch versions, such as "1.0.2".

When adding an entry to CHANGELOG.md, you can carefully edit the file making sure to follow the Keep A Changelog format. Or use the "changelogmanager" command, from the Python package [keepachangelog-manager](https://pypi.org/project/keepachangelog-manager/). Use "changelogmanager add --help" for usage. Here's an example:

    changelogmanager add --change-type added --message "description of new feature that was added"

If the changelog didn't already have an "unreleased" section, this will create it to file the new change under it. Upon the next release, the unreleased section will be renamed with the new version number.

Keep in mind that the type of change affects how the version number will be increased.

* The major number is incremented by changes of type "removed"
* The minor number is incremented by changes of type "added" or "security"
* The patch number is incremented by changes of type "changed", "deprecated" or "fixed"

A changelog update for release is done with the command:

    changelogmanager release

It is possible to override the new version number in a release with this command (fill in the relevant numbers for major, minor and patch):

    changelogmanager release --override-version "major.minor.patch"

Use "pdm release" to publish the new version with updated changelog to PyPI.

Use of changelogmanager's "github-release" feature is awaiting a fix that allows the changelog release update to happen before running it. We have to do the PyPI release first.

<a name="license">License</a>
-------

This project is licensed under the AGPL-3.0 license in order to be compatible with Pelican.

<a name="credits">Credits</a>
-------
Let's give credit to the volunteers who created the foundation this is built upon. This plugin pulls together code from the legacy [events plugin by Federico Ceratto](https://github.com/getpelican/pelican-plugins/tree/master/events) and the forked [pelican-events-plugin by Makerspace Esslingen](https://github.com/Makerspace-Esslingen/pelican-events-plugin) into a plugin compliant with the current [namespace plugin structure](https://docs.getpelican.com/en/latest/plugins.html#namespace-plugin-structure). We also added support for more iCalendar properties, as many as make sense in a public setting. A security review excluded some properties which are intended for private email use, and could cause misconfiguration or be used for mischief. Those details are documented above.
