# 006: GUI naming method and constant rules

## Status

Completed

## Outcome

As a developer, I need class methods to use action-only names and private
constants to use `_UPPER_CASE` so naming matches the domain already present
in the class or the private-constant convention.

## Context

The linter previously required `domainAction` for every function, including
methods such as `Project.update()`, and rejected `_MAX_RETRIES`.

## Scope

- Class methods, classmethods and staticmethods may be action-only camelCase.
- Module-level functions continue to require `domainAction`.
- Nested or local helper functions may use ordinary descriptive names and
  are not required to use `domainAction`.
- Private constants may use a leading underscore on UPPER_CASE names.

## Out of scope

- Changing widget prefix rules or Qt snake_case widget naming.

## Acceptance criteria

1. Given `class Project: def update(self)`, when the file is linted, then
   `update` is not a naming violation.
2. Given a module-level `def update()`, when the file is linted, then
   `domainAction` is required.
3. Given `_MAX_RETRIES = 3` at module level, when the file is linted, then
   it is accepted as a constant.
4. Given nested helpers such as `fail`, `empty`, `box` or `boom`, when the
   file is linted, then they are not `domainAction` violations.

## Verification

- Unit tests in `tests/test_guiNamingLinter.py`.
- HELP.md and agent-instructions describe the distinction.

## Traceability

- Implementation: `organiseMyProjects/guiNamingLinter.py`
- Tests: `tests/test_guiNamingLinter.py`
- Documentation: `organiseMyProjects/HELP.md`, `.github/agent-instructions.md`

## Change history

- 2026-09-11: completed on `release/0.7`.
- 2026-09-11: nested/local helpers are exempt from `domainAction`.
