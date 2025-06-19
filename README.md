# pelican-events
Pelican plugin to embed event data in posts

This project is just getting started. It is for the [Portland Linux Kernel Meetup](https://ikluft.github.io/pdx-lkmu/) site. The site is set up with a static site generator Pelican. We intended to use the "events" plugin to automatically generate iCalendar entries from events with calendar metadata. But the events plugin is unmaintained and doesn't generate enough iCalendar fields for our needs. Also, it's so old it doesn't implement the current standard for Pelican plugins, namely being a standalone Python module. That's what this project is intended to solve - rewrite it as a Python module.
