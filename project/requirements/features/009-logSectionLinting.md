# 009: Log section linting

## Status

Completed

## Outcome

runLinter reports missing run markers and section separators in conventional
Python application entry points so existing projects can adopt the shared output
convention.

## Scope

Check runStart before logger headers, line after headers, and line before summary
counts and completion output. Recognise direct and logUtils-qualified calls.
Exclude tests and ordinary helpers. Handle conditional completion branches.

## Out of scope

Bash analysis, arbitrary logger aliases, interprocedural or full control-flow
analysis, automatic source edits, print-only header detection and changes to
linter exit-code behaviour.

## Acceptance criteria

1. Missing or misplaced calls produce LOG-SEC-001, LOG-SEC-002 or LOG-SEC-003.
2. Compliant entry points produce no section findings.
3. Calls in strings, comments or unused nested helpers do not satisfy the rules.
4. Real runLinter output includes the findings with source line numbers.
5. Helper modules, tests and dispatchers with no headers are not flagged.

## Dependencies and decisions

Shared logUtils.runStart and line APIs; no new architecture decision required.

## Verification

`tests/test_loggingSections.py` exercises parser rules and the real linter path.
The full repository suite validates existing behaviour.

## Change history

- 2026-09-14: Created from the request to enforce existing-project logging layout.
