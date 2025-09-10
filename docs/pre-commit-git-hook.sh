#!/bin/sh
# pre-commit git hook: run tests and lint check before allowing commit to pelican-events
# by Ian Kluft
# created 2025-09-09

# function to print and error and exit
croak()
{
    echo "$*" >&2
    exit 1
}

# verify pdm is installed
which pdm 2>/dev/null >&2 \
    || croak "error: pdm (Python Dependency Manager) is not installed - can't perform pre-commit checks"

# perform lint check the same way Github would, to make sure the build won't break
pdm run invoke lint --concise 2>/dev/null >&2 \
    || croak "error: pdm lint check failed. Run 'pdm run invoke lint --diff' to see changes."

# run unit tests, to make sure the build won't break
pdm run invoke tests 2>/dev/null >&2 \
    || croak "error: tests are not passing. Run 'pdm run invoke tests' to see results."

# success if we got here
exit 0
