#!/usr/bin/env python3
"""PDM pre_publish hook script runs before publish operation."""
# by Ian Kluft

import subprocess
import sys

from changelogmanager.change_types import (
    UNRELEASED_ENTRY,
)
from changelogmanager.changelog import Changelog
from changelogmanager.changelog_reader import ChangelogReader

# constants
CHANGELOG = "CHANGELOG.md"


def in_git_ws() -> bool:
    """Check if the current directory is within a git workspace."""
    try:
        output = subprocess.check_output(['git', 'rev-parse', '--is-inside-work-tree'], stderr=subprocess.STDOUT)
        return output.strip() == b'true'
    except subprocess.CalledProcessError:
        return False


def is_ws_clean() -> str | None:
    """Check if git workspace is clean of untracked or uncommitted files."""
    try:
        output = subprocess.check_output(['git', 'status', '--porcelain'], stderr=subprocess.STDOUT)
        if len(output.strip()) > 0:
            return "git workspace is not clean - untracked or uncommitted files found"
    except subprocess.CalledProcessError as e:
        return f"git error: {e}"
    return None


def main() -> int | str | None:
    """Mainline for pre_publish hook script."""
    # in order to publish, there must be no unreleased entries in the changelog
    changelog_dict = ChangelogReader(file_path=CHANGELOG).read()
    changelog = Changelog(file_path=CHANGELOG, changelog=changelog_dict)
    if UNRELEASED_ENTRY in changelog.get():
        return f"pre_publish: there are unreleased entries in {CHANGELOG}"

    # in order to publish, we must be in a git workspace
    if not in_git_ws():
        return "pre_publish: publishing must be in a git workspace"

    # in order to publish, there must be no untracked/uncommitted files in the git workspace
    ws_status = is_ws_clean()
    if ws_status is not None:
        return ws_status

    # conditions met: publish approved
    return None


if __name__ == "__main__":
    sys.exit(main())
