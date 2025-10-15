"""Pelican Events version number getter for PDM - call configured from pyproject.toml."""

from changelogmanager.change_types import (
    UNRELEASED_ENTRY,
)
from changelogmanager.changelog import Changelog
from changelogmanager.changelog_reader import ChangelogReader


def get_version() -> str:
    """Get version number from changelog file."""
    changelog_dict = ChangelogReader(file_path="CHANGELOG.md").read()
    changelog = Changelog(file_path="CHANGELOG.md", changelog=changelog_dict)
    if UNRELEASED_ENTRY in changelog.get():
        return str(changelog.suggest_future_version())
    return str(changelog.version())
