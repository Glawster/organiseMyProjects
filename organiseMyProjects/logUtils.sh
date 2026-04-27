#!/usr/bin/env bash
# logUtils.sh — standard logging helper for bash scripts.
#
# Part of organiseMyProjects — the canonical shared tooling library.
#
# SOURCE this file; do not execute it directly:
#   source "$(python3 -c 'import organiseMyProjects, os; print(os.path.dirname(organiseMyProjects.__file__))')/logUtils.sh"
#
# Then initialise logging once per script:
#   setApplication "myScript"          # → ~/.local/state/myScript/myScript-<date>.log
#   setApplication "myScript" /tmp/logs # → /tmp/logs/myScript-<date>.log
#
# Compatibility wrapper:
#   log_init "myScript"                # calls setApplication "myScript"
#
# Semantic log functions (mirror Python logUtils conventions):
#   log_doing "scanning files"           →  scanning files...
#   log_done  "scan complete"            →  ...scan complete
#   log_info  "found 5 items"            →  ...found 5 items
#   log_value "source dir" "/home/andy"  →  ...source dir: /home/andy
#   log_action "moving file: a → b"      →  ...[] moving file: a → b  (when dryRun is set)
#                                        →  ...moving file: a → b     (when dryRun is unset)
#   log_warn  "file not found"           →  WARNING: file not found
#   log_error "fatal problem"            →  ERROR: fatal problem  (stderr)
#   log_box   "Backup complete"          →  draws a box around the message
#
# Logging guidelines (matching Python logUtils):
#   all messages in lowercase
#   "doing something..." - major action being taken
#   "...something done"  - above action completed
#   "...message"         - general update
#   "...message: value"  - display some information
#   ERROR messages should be in Sentence Case.

# Guard against double-sourcing
[[ -n "${_LOG_UTILS_LOADED:-}" ]] && return 0
_LOG_UTILS_LOADED=1

# Application context is set by setApplication.
thisApplication="${thisApplication:-}"
applicationLogDir="${applicationLogDir:-}"
logFile="${logFile:-/dev/null}"
logDir="${logDir:-}"

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_require_application() {
  if [[ -z "${thisApplication:-}" ]]; then
    echo "Application logging context has not been set. Call setApplication first." >&2
    return 1
  fi
}

_current_date() {
  date +%Y-%m-%d
}

# Write a timestamped line to logFile only (no console output)
_log_to_file() {
  [[ "$logFile" == "/dev/null" ]] && return 0
  echo "[$(date +"%Y-%m-%d %H:%M:%S")] $*" >> "$logFile"
}

# Write a timestamped line to both console and logFile
_log() {
  _require_application || return 1
  local msg="[$(date +"%Y-%m-%d %H:%M:%S")] $*"
  echo "$msg"
  [[ "$logFile" != "/dev/null" ]] && echo "$msg" >> "$logFile"
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# setApplication <applicationName> [logBaseDir]
#   Sets the active application context and creates the log directory.
#   If logBaseDir is empty or not provided, defaults to ~/.local/state/<applicationName>
setApplication() {
  local appName="${1:-}"
  local baseDir="${2:-}"

  if [[ -z "$appName" ]]; then
    echo "Application name must not be empty." >&2
    return 1
  fi

  [[ -z "$baseDir" ]] && baseDir="$HOME/.local/state/$appName"

  thisApplication="$appName"
  applicationLogDir="$baseDir"
  logDir="$applicationLogDir"
  mkdir -p "$logDir"

  logFile="$logDir/${thisApplication}-$(_current_date).log"
  _log "logging to: $logFile"
}

# getApplication
#   Prints the active application name, or fails if unset.
getApplication() {
  _require_application || return 1
  echo "$thisApplication"
}

# getApplicationLogDir
#   Prints the active application log directory, or fails if unset.
getApplicationLogDir() {
  _require_application || return 1
  if [[ -z "${applicationLogDir:-}" ]]; then
    echo "Application log directory has not been initialised." >&2
    return 1
  fi
  echo "$applicationLogDir"
}

# log_init <scriptName> [logBaseDir]
#   Backwards-compatible wrapper around setApplication.
log_init() {
  setApplication "$@"
}

# log_doing <message>  →  message...
log_doing() {
  _log "$1..."
}

# log_done <message>  →  ...message
log_done() {
  _log "...$1"
}

# log_info <message>  →  ...message
log_info() {
  _log "...$1"
}

# log_value <key> <value>  →  ...key: value
log_value() {
  _log "...$1: $2"
}

# log_action <message>
#   If the caller's $dryRun variable is non-empty, prefixes with "[] " (dry-run marker).
#   Use for operations that are skipped in dry-run mode.
log_action() {
  if [[ -n "${dryRun:-}" ]]; then
    _log "...[] $1"
  else
    _log "...$1"
  fi
}

# log_warn <message>  →  WARNING: message
log_warn() {
  _log "WARNING: $1"
}

# log_error <message>  →  ERROR: message  (also to stderr)
log_error() {
  _require_application || return 1
  local msg="[$(date +"%Y-%m-%d %H:%M:%S")] ERROR: $1"
  echo "$msg" | tee -a "$logFile" >&2
}

# log_box <message>
#   Draws an ASCII box around the message. Multi-line messages supported
#   (separate lines with \n or actual newlines).
#   Output goes to both console and logFile.
log_box() {
  _require_application || return 1
  local message="$1"
  local pad=2
  local maxLen=0
  local line

  # Calculate max line length
  while IFS= read -r line; do
    (( ${#line} > maxLen )) && maxLen=${#line}
  done <<< "$(printf '%b' "$message")"

  local innerWidth=$(( maxLen + pad * 2 ))
  local border
  border=$(printf '+'; printf -- '─%.0s' $(seq 1 $innerWidth); printf '+')

  local output
  output="$border"$'\n'
  while IFS= read -r line; do
    local padRight=$(( innerWidth - ${#line} - pad ))
    output+=$(printf "│%${pad}s%s%${padRight}s│" "" "$line" "")$'\n'
  done <<< "$(printf '%b' "$message")"
  output+="$border"

  echo "$output"
  [[ "$logFile" != "/dev/null" ]] && echo "$output" >> "$logFile"
}
