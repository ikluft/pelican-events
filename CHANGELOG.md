# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.4] - 2025-10-15
### Fixed
- fix generated version.py with newline and double-quotes to silence lint warning
- add PDM pre_publish hook to block on unreleased entries in changelog or untracked/uncommitted files in git ws

## [0.1.2] - 2025-10-15
### Fixed
- dynamic version numbering based on contents of CHANGELOG.md in Keep a Changelog format

## [0.1.1] - 2025-10-13
### Fixed
- updated README example to use TIMEZONE instead of old location in PLUGIN_EVENTS.timezone

## [0.1.0] - 2025-10-13
### Added
- initial version of revived Pelican Events plugin
