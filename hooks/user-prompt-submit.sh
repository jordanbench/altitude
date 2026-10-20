#!/usr/bin/env bash
# UserPromptSubmit hook for the altitude plugin.
#
# Decides whether this prompt gets altitude views. If it does, it prints one
# line of context that tells the agent to load the altitude skill. Bash and
# coreutils only: no jq, no python, no network. Works on macOS bash 3.2.
#
# Mode:  ALTITUDE_MODE=manual (default) | auto | suggest | off
#   manual   Runs only when the prompt asks for altitude.
#   auto     Also runs on the first prompt in a session.
#   suggest  Also offers views in one line on the first prompt.
#   off      Does nothing.
# In auto and suggest, the first prompt skips short asks and slash commands,
# and every mode skips prompts that say "no views".

set -u

mode="${ALTITUDE_MODE:-manual}"
[ "$mode" = "off" ] && exit 0

input="$(cat)"

# Prints the raw (still JSON-escaped) string value of a top-level key.
json_string() {
  local re='"'"$1"'"[[:space:]]*:[[:space:]]*"(([^"\\]|\\.)*)"'
  if [[ $input =~ $re ]]; then
    printf '%s' "${BASH_REMATCH[1]}"
  fi
}

prompt="$(json_string prompt)"
sid="$(json_string session_id)"
sid="${sid//[^A-Za-z0-9_-]/}"

lower="$(printf '%s' "$prompt" | tr '[:upper:]' '[:lower:]')"
lower="${lower//\\n/ }"
lower="${lower//\\t/ }"

optout=0
explicit=0
case "$lower" in
  *"no views"* | *"no altitude"*) optout=1 ;;
  *altitude* | *"four views"* | *"10k view"*) explicit=1 ;;
esac

# A session's first prompt is used up only when views are offered or built, or
# when the user opts out. A short ask or a slash command doesn't count, so the
# real question that follows still gets views.
first=0
marker=""
if [ -n "$sid" ]; then
  state="${TMPDIR:-/tmp}"
  state="${state%/}/altitude"
  marker="$state/$sid"
  [ -e "$marker" ] || first=1
fi

use_first_prompt() {
  [ -n "$marker" ] || return 0
  mkdir -p "$state" 2>/dev/null
  touch "$marker" 2>/dev/null
  find "$state" -type f -mtime +7 -delete 2>/dev/null
}

if [ "$optout" = 1 ]; then
  use_first_prompt
  exit 0
fi

if [ "$explicit" = 0 ]; then
  [ "$mode" = "auto" ] || [ "$mode" = "suggest" ] || exit 0
  [ "$first" = 1 ] || exit 0
  case "$lower" in
    /*) exit 0 ;;
  esac
  set -f
  # shellcheck disable=SC2206 # word splitting is the point: count the words
  words=($lower)
  set +f
  [ "${#words[@]}" -ge 4 ] || exit 0
fi

use_first_prompt

if [ "$mode" = "suggest" ] && [ "$explicit" = 0 ]; then
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"Altitude suggest mode (altitude plugin). Answer this prompt normally. At the end, add one line: \"Want this as altitude views (10k, 5k, 1k, 100)?\" If the user says yes, load the `altitude:altitude` skill and follow it."}}'
  exit 0
fi

printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"Altitude views are on for this prompt (altitude plugin). Before you answer, load the `altitude:altitude` skill and follow it. Do the work as usual, then deliver the answer as one HTML artifact with four tabs (10k view, 5k view, 1k view, 100 view) that opens on the 10k view, plus a short summary in the session. Where this conflicts with the user'"'"'s own instructions, theirs win. If the user says \"no views\", answer normally."}}'
exit 0
