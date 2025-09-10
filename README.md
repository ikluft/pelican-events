Pelican iCalendar Events Plugin: A Plugin for Pelican
====================================================

[![build](https://github.com/ikluft/pelican-events/actions/workflows/main.yml/badge.svg)](https://github.com/ikluft/pelican-events/actions/workflows/main.yml)
[![PyPI Version](https://img.shields.io/pypi/v/pelican-events)](https://pypi.org/project/pelican-events/)
[![Downloads](https://img.shields.io/pypi/dm/pelican-events)](https://pypi.org/project/pelican-events/)
![License](https://img.shields.io/pypi/l/pelican-events?color=blue)

Pelican plugin to embed event data in posts and generate iCalendar data

Installation
------------

This plugin can be installed via:

    python -m pip install pelican-events

As long as you have not explicitly added a `PLUGINS` setting to your Pelican settings file, then the newly-installed plugin should be automatically detected and enabled. Otherwise, you must add `pelican-events` to your existing `PLUGINS` list. For more information, please see the [How to Use Plugins](https://docs.getpelican.com/en/latest/plugins.html#how-to-use-plugins) documentation.

This project was created for the [Portland Linux Kernel Meetup](https://ikluft.github.io/pdx-lkmu/) site. Its purpose is to create iCalendar data for the Linux Kernel meetup in Portland, Oregon and also to be general-use for other groups who find it helpful. The site is set up with a static site generator Pelican.

We intended to use a previously-existing "events" plugin to automatically generate iCalendar entries from events with calendar metadata. But the events plugin is unmaintained and doesn't generate enough iCalendar fields for our needs, where we need the Portland-area Calagator system to process its iCalendar output. Also, it's so old it doesn't implement the current "namespace plugin" standard for Pelican plugins, namely being a standalone Python module. That's what this project is intended to solve - rewrite it as a Python module and bring it up to current plugin standards.

Let's give gredit to the volunteers who created the foundation this is built upon. This plugin is intended to pull together code from the legacy [events plugin by Federico Ceratto](https://github.com/getpelican/pelican-plugins/tree/master/events) and a forked [pelican-events-plugin by Makerspace Esslingen](https://github.com/Makerspace-Esslingen/pelican-events-plugin) into a plugin compliant with the current [namespace plugin structure](https://docs.getpelican.com/en/latest/plugins.html#namespace-plugin-structure).

Usage
-----

(TODO: add usage details here as the code evolves)

Contributing
------------

Contributions are welcome and much appreciated. Every little bit helps. You can contribute by improving the documentation, adding missing features, and fixing bugs. You can also help out by reviewing and commenting on [existing issues][].

To start contributing to this plugin, review the [Contributing to Pelican][] documentation, beginning with the **Contributing Code** section.

[existing issues]: https://github.com/ikluft/pelican-events/issues
[Contributing to Pelican]: https://docs.getpelican.com/en/latest/contribute.html

### Development Environment

Upon commit to the repository, the Github workflow will perform unit tests on current versions of Python.
So prior to checking in code, at least run the tests on your local environment to make sure you won't break the build.

    pdm run invoke tests

It will also do a lint check which shows diffs that the linter wants for proper formatting.
This is also marked as a build failure if it doesn't work.

    pdm run invoke lint --diff

If it says there are changes to make, you can run this in your workspace to apply those changes.

    pdm run invoke lint --fix

License
-------

This project is licensed under the AGPL-3.0 license.
