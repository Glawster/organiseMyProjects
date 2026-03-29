#!/usr/bin/env bash
# =============================================================================
# logUtils.sh — shared Bash logging helper for organiseMyProjects
# =============================================================================
#
# PURPOSE:
#   Provides standardised, timestamped logging for shell scripts, mirroring
#   the conventions and semantic function names of logUtils.py.
#
# USAGE:
#   Set SCRIPT_NAME before sourcing, then call setup_logging:
#
#     SCRIPT_NAME="organiseHome"
#     source ~/Source/organiseMyProjects/organiseMyProjects/logUtils.sh
#     setup_logging
#
#   Optionally override the log directory by setting LOG_DIR before calling
#   setup_logging:
#
#     LOG_DIR="/tmp/mylogs"
#     setup_logging
#
# LOG FILE LOCATION:
#   ~/.local/state/<SCRIPT_NAME>/<SCRIPT_NAME>-<YYYY-MM-DD>.log
#
# DRY-RUN SUPPORT:
#   Set DRY_RUN=true (or DRY_RUN=1) before sourcing / before calling any
#   log function.  log_action will then prefix messages with "[] ".
#
# AVAILABLE FUNCTIONS:
#   setup_logging              — initialise LOG_FILE and create log directory
#   log_doing  <message>       — "message..."   (major action starting)
#   log_done   <message>       — "...message"   (action completed)
#   log_info   <message>       — "...message"   (general info)
#   log_value  <name> <value>  — "...name: value"
#   log_action <message>       — "...[] message" when DRY_RUN set, else "...message"
#   log_warn   <message>       — "WARNING: message" (stdout + stderr + file)
#   log_error  <message>       — "ERROR: message"   (stdout + stderr + file)
#   log_box    <message>       — ASCII +---+ box around message
#   log_raw    <message>       — timestamped line written verbatim to log file
#
# IDEMPOTENCY:
#   Safe to source multiple times; setup_logging may be called multiple times
#   (each call refreshes LOG_FILE for the current date).
#
# logging guidelines:
# all messages in lowercase
# "doing something..." - major action being taken
# "...something done" - above action completed
# "...message" - general update
# "...message: value" - display name/value pair
# ERROR messages should be in Sentence Case.
# =============================================================================

# Guard against being sourced more than once in the same shell session.
# Remove the guard variable to allow re-initialisation if needed.
if [[ -n "${_LOGUTILS_SH_LOADED:-}" ]]; then
    return 0
fi
_LOGUTILS_SH_LOADED=1

# ---------------------------------------------------------------------------
# Internal helper: write a timestamped line to LOG_FILE (if set) AND stdout.
# Usage: _log_write <line>
# ---------------------------------------------------------------------------
_log_write() {
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    local line="${timestamp} - ${1}"

    # Write to log file when available
    if [[ -n "${LOG_FILE:-}" ]]; then
        printf '%s\n' "${line}" >> "${LOG_FILE}"
    fi

    # Always echo to stdout
    printf '%s\n' "${line}"
}

# ---------------------------------------------------------------------------
# Internal helper: write to stderr (and log file).
# ---------------------------------------------------------------------------
_log_write_err() {
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    local line="${timestamp} - ${1}"

    if [[ -n "${LOG_FILE:-}" ]]; then
        printf '%s\n' "${line}" >> "${LOG_FILE}"
    fi

    printf '%s\n' "${line}"
    printf '%s\n' "${line}" >&2
}

# ---------------------------------------------------------------------------
# setup_logging
#   Creates the log directory and sets LOG_FILE.
#   Respects optional LOG_DIR override; uses ~/.local/state/<SCRIPT_NAME>
#   by default.  Writes a separator line to mark a new session.
# ---------------------------------------------------------------------------
setup_logging() {
    local script_name="${SCRIPT_NAME:-unknown}"
    local log_dir="${LOG_DIR:-${HOME}/.local/state/${script_name}}"
    local date_str
    date_str="$(date '+%Y-%m-%d')"

    mkdir -p "${log_dir}"
    LOG_FILE="${log_dir}/${script_name}-${date_str}.log"

    # Write a session separator so multiple runs on the same day are distinct
    printf '%s\n' "$(date '+%Y-%m-%d %H:%M:%S') - ----------------------------------------" >> "${LOG_FILE}"
}

# ---------------------------------------------------------------------------
# log_doing <message>
#   Logs "<message>..." — announces a major action being taken.
# ---------------------------------------------------------------------------
log_doing() {
    _log_write "${1}..."
}

# ---------------------------------------------------------------------------
# log_done <message>
#   Logs "...<message>" — announces that the previous action completed.
# ---------------------------------------------------------------------------
log_done() {
    _log_write "...${1}"
}

# ---------------------------------------------------------------------------
# log_info <message>
#   Logs "...<message>" — general informational update.
# ---------------------------------------------------------------------------
log_info() {
    _log_write "...${1}"
}

# ---------------------------------------------------------------------------
# log_value <name> <value>
#   Logs "...<name>: <value>" — display a name/value pair.
# ---------------------------------------------------------------------------
log_value() {
    _log_write "...${1}: ${2}"
}

# ---------------------------------------------------------------------------
# log_action <message>
#   Logs "...[[] ]<message>" when DRY_RUN=true/1, otherwise "...<message>".
#   Use this for operations that are skipped during a dry run.
# ---------------------------------------------------------------------------
log_action() {
    local prefix=""
    if [[ "${DRY_RUN:-}" == "true" || "${DRY_RUN:-}" == "1" ]]; then
        prefix="[] "
    fi
    _log_write "...${prefix}${1}"
}

# ---------------------------------------------------------------------------
# log_warn <message>
#   Logs "WARNING: <message>" to stdout, stderr, and the log file.
# ---------------------------------------------------------------------------
log_warn() {
    _log_write_err "WARNING: ${1}"
}

# ---------------------------------------------------------------------------
# log_error <message>
#   Logs "ERROR: <message>" to stdout, stderr, and the log file.
# ---------------------------------------------------------------------------
log_error() {
    _log_write_err "ERROR: ${1}"
}

# ---------------------------------------------------------------------------
# log_box <message>
#   Prints an ASCII +---+ box around a (possibly multi-line) message.
#   Also writes each line to the log file with a timestamp.
# ---------------------------------------------------------------------------
log_box() {
    local message="${1}"
    local padding=2
    local border_char="-"
    local corner_char="+"
    local side_char="|"

    # Split message into lines
    local -a lines
    while IFS= read -r line; do
        lines+=("${line}")
    done <<< "${message}"

    # Calculate the maximum line length
    local max_len=0
    for line in "${lines[@]}"; do
        if (( ${#line} > max_len )); then
            max_len=${#line}
        fi
    done

    local inner_width=$(( max_len + padding * 2 ))
    local border="${corner_char}$(printf '%0.s'"${border_char}" $(seq 1 "${inner_width}"))${corner_char}"

    # Output top border
    _log_write "${border}"

    # Output each content line
    for line in "${lines[@]}"; do
        local pad_right=$(( inner_width - ${#line} - padding ))
        local content_line="${side_char}$(printf '%*s' "${padding}" '')${line}$(printf '%*s' "${pad_right}" '')${side_char}"
        _log_write "${content_line}"
    done

    # Output bottom border
    _log_write "${border}"
}

# ---------------------------------------------------------------------------
# log_raw <message>
#   Writes a timestamped line verbatim to the log file (no semantic prefix).
#   Useful for capturing piped command output into the log.
# ---------------------------------------------------------------------------
log_raw() {
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    local line="${timestamp} - ${1}"

    if [[ -n "${LOG_FILE:-}" ]]; then
        printf '%s\n' "${line}" >> "${LOG_FILE}"
    else
        # Warn only once per session if LOG_FILE is not set
        if [[ -z "${_LOG_RAW_WARNING_SHOWN:-}" ]]; then
            _LOG_RAW_WARNING_SHOWN=1
            printf 'WARNING: log_raw called before setup_logging; writing to stdout only\n' >&2
        fi
        printf '%s\n' "${line}"
    fi
}
