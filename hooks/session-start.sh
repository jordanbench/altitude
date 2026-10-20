#!/usr/bin/env bash
# SessionStart shim for the altitude plugin: shows the user a one-line tip so
# /altitude is easy to find. No stdin read, no files, no network.
# ALTITUDE_MODE=off hides it.

[ "${ALTITUDE_MODE:-manual}" = "off" ] && exit 0
printf '%s\n' '{"systemMessage":"altitude: type /altitude to see the last answer as 10k, 5k, 1k, and 100 views."}'
exit 0
