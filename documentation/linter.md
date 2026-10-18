# OMP linter

## Invocation

The installed `organiseMyProjects` package is the single source of truth for
linting. From any managed project, run:

```bash
runLinter
```

Pass a file or directory only when a narrower target is required. Managed
projects do not carry private copies of `runLinter.py` or
`guiNamingLinter.py`; updating the installed OMP package updates linter
behaviour for every project that uses it.

## Output and exit status

`runLinter` reports in the style of pytest. After the version header it prints
the root directory and targets, then one line per linted file marked `PASSED`
or `FAILED`, then each finding on its own line:

```text
organiseMyProjects/manageProject.py:375: LOG-CASE-001 logger.info message should be lowercase: '...'
```

Paths are relative to the directory `runLinter` was run from, so terminals and
editors can open the location directly. Each finding carries a stable rule
identifier, for example `NAM-003` for module function names or `LOG-SEC-002`
for a missing separator after an application header. A closing line
summarises the run:

```text
==================== 4 findings in 2 files, 23 files passed in 0.41s ====================
```

The exit status follows pytest conventions:

| Status | Meaning |
| --- | --- |
| `0` | Every linted file passed. |
| `1` | One or more findings were reported. |
| `2` | Invalid invocation, or a supplied target is missing, unreadable or not a Python file or directory. |
| `5` | No Python files were found to lint. |

A target error takes precedence over findings. A file that cannot be parsed is
reported as a `LINT-001` finding rather than stopping the run.
`runLinter --markup` keeps the markdownlint output and exit status.

## Naming rules

Module-level functions use `domainAction` camelCase. Digits may be part of the
domain before the action boundary, so names such as `_mp4BoxIterate` and
`_mp4MvhdCreationRead` are valid. Class methods may use action-only camelCase.
Nested/local helpers remain exempt from the module-level `domainAction` rule.

External frameworks and protocols may dictate method names. Such names are
exempt only when dispatch depends on their exact spelling. Textual is currently
recognised explicitly: in files importing `textual`, `action_*` action handlers
and `on_*` event/message handlers are accepted. This includes methods such as
`action_policy_positive`, `action_sender_edit`, `on_button_pressed`,
`on_click`, and `on_input_changed`. Arbitrary snake_case project methods remain
invalid.

## Logging case exceptions

`logger.info` and `logger.warning` messages remain lowercase, and
`logger.error` messages remain sentence case. Approved product/proper-name
tokens may retain their spelling without weakening the rest of the message.
The centrally maintained approved set is:

- `DJI`
- `Firefox`
- `GoPro`
- `Grok`
- `MCM`
- `SQLite`
- `TVDB`
- `X.ai`

Mixed-case tokens outside that list are still reported. Additions therefore
require an explicit OMP change and regression test rather than silently
relaxing the casing rule.

## Migration from project-local linters

`manageProject update -y` removes obsolete `tests/runLinter.py` and
`tests/guiNamingLinter.py` only when they are recognised as unmodified
OMP-managed copies. Locally changed or ambiguous files are preserved and
reported for manual review. Re-running update is idempotent and does not
recreate the old copies.
