# 013: runLinter pytest-style reporting

## Status

ToDo

## Outcome

As a developer or CI pipeline running `runLinter`, I need findings reported in
a familiar pytest-style format with unambiguous locations, a summary and a
meaningful exit status so that lint results can be read at a glance, navigated
from the terminal or editor, and enforced automatically.

## Context

`runLinter` currently prints one line per file using only the basename, for
example `__init__.py: OK`, so files with the same name in different packages
cannot be distinguished. Findings use a single template,
`Line N: '<name>' should follow naming rule for <rule>.`, which reads poorly for
rules that are not naming rules, such as the `LOG-SEC-*` log-section checks.
There is no closing summary, and the process exits `0` even when findings are
reported, so CI, pre-commit and the release checklist cannot rely on the exit
status.

Developers already read pytest output daily. Adopting its conventions keeps the
linter output consistent with the rest of the OMPR validation workflow.

## Scope

- Report each finding on one line as
  `<relativePath>:<line>: <ruleId> <message>`, with the path relative to the
  directory `runLinter` was invoked from, so terminals and editors can open the
  location directly.
- Give every rule a stable rule identifier and a rule-specific message instead
  of the generic "should follow naming rule" template.
- Print a pytest-style header identifying the OMPR version, root directory and
  lint targets.
- Print a progress section listing linted files, marking each as passed or
  failed, without printing basenames that are ambiguous.
- Print a final summary line in pytest style, for example
  `==== 4 findings in 2 files, 23 files passed in 0.41s ====`, or
  `==== 25 files passed in 0.39s ====` when clean.
- Exit with a status code following pytest conventions:
  - `0` — every linted file passed;
  - `1` — one or more findings were reported;
  - `2` — invalid invocation, or a supplied target is missing, unreadable or
    not lintable;
  - `5` — no Python files were found to lint.
- Provide `-q`/`--quiet` (findings and summary only) and `-v`/`--verbose` (also
  list each passed file), with the default output between the two.
- Keep reporting logic separate from rule evaluation so findings can be
  collected and tested as data without parsing printed text.
- Update `documentation/linter.md` and the release checklist in
  `documentation/howToRelease.md` to describe the format and exit codes.

## Out of scope

- Changing which rules exist or what they accept or reject.
- Changing `runLinter --markup` output, which is produced by markdownlint.
- Machine-readable output formats such as JSON, SARIF or JUnit XML.
- Colour output beyond what can be disabled safely for non-terminal output.
- Running the linter as a pytest plugin.

## Acceptance criteria

1. Given a project with findings in two files that share a basename, when
   `runLinter` runs, then each finding is reported as
   `<relativePath>:<line>: <ruleId> <message>` and the two files are
   distinguishable.
2. Given any reported finding, when it is printed, then its message is specific
   to the rule and does not use the generic "should follow naming rule"
   template for non-naming rules.
3. Given a lint run, when it completes, then a pytest-style summary line reports
   the number of findings, the number of affected files, the number of passed
   files and the elapsed time.
4. Given a project with no findings, when `runLinter` runs, then it exits `0`.
5. Given a project with at least one finding, when `runLinter` runs, then it
   exits `1`.
6. Given a supplied target that does not exist, is unreadable or is not a
   Python file or directory, when `runLinter` runs, then the problem is
   reported and the exit status is `2`.
7. Given targets that contain no Python files, when `runLinter` runs, then the
   summary says nothing was linted and the exit status is `5`.
8. Given `-q`, when `runLinter` runs, then only findings and the summary are
   printed; given `-v`, then every passed file is also listed.
9. Given `runLinter --markup`, when it runs, then its existing behaviour and
   exit status are unchanged.
10. Given the OMPR repository itself, when the release checklist runs
    `runLinter .`, then it exits `0`, with any existing findings either fixed or
    explicitly allowed by an existing rule.
11. Automated tests cover the finding format, relative paths, summary counts,
    each exit status and the quiet and verbose modes, using collected findings
    rather than only captured output.
12. `documentation/linter.md` and `documentation/howToRelease.md` describe the
    output format and exit codes.

## Dependencies and decisions

- Builds on requirement 005 (source directory discovery), 009 (log-section
  linting) and 010 (centralised linter implementation).
- The internal refactor that removes the import-time patches from
  `organiseMyProjects/__init__.py`, including `runLinterPatchesInstall`, should
  land first so reporting is implemented in `runLinter.py` rather than an
  overlay.
- Changing the exit status from always `0` to `1` on findings may fail
  downstream pre-commit hooks or CI that currently pass despite findings; the
  release notes must call this out.
- No architecture decision is expected.

## Verification

- Focused tests in `tests/test_runLinter.py` for each acceptance criterion.
- Run `runLinter .`, `runLinter -q .` and `runLinter -v .` on this repository
  and on a downstream project, confirming output and exit status.
- Full `pytest`, `runLinter .` and `runLinter --markup` release validation.

## Change history

- 2026-10-18: created — agreed for OMPR 0.9 to make runLinter output
  pytest-style and its exit status enforceable. Format, exit-code and
  quiet/verbose details are proposed and to be confirmed before InProgress.
