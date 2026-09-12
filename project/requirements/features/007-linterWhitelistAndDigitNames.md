# 007: Linter whitelist and digit-aware naming

## Status

ToDo — planned for OMP 0.8.

## Outcome

Reduce false-positive GUI naming linter findings while preserving the existing
logging and domainAction conventions.

## Scope

- Add an explicit whitelist for approved proper names and acronyms used in log
  messages so valid casing is not rejected by the logging rules.
- Seed the whitelist with the currently observed project terms:
  `DJI`, `Firefox`, `GoPro`, `Grok`, `MCM`, `SQLite`, `TVDB`, and `X.ai`.
- Keep the whitelist exact and reviewable rather than weakening case checks for
  arbitrary mixed-case words.
- Apply logging-case checks after accounting for whitelisted tokens, so a
  lowercase `info`/`warning` message may still contain approved proper names and
  an `error` message may remain sentence case while preserving approved names.
- Update the domainAction rule so digits are allowed within otherwise valid
  domain/action names, including private helpers such as `_mp4BoxIterate` and
  `_mp4MvhdCreationRead`.
- Preserve the current rule that nested/local helpers do not require
  domainAction naming.
- Preserve the current rule that only `logger.info` and `logger.value` accept
  separate interpolation variables unless a later requirement deliberately
  changes that logging API policy.

## Acceptance criteria

1. A logging message containing only permitted casing plus a whitelisted token,
   such as `TVDB`, `MCM`, `Firefox`, or `Grok`, produces no casing violation.
2. A mixed-case token that is not whitelisted still produces the existing
   casing violation.
3. The whitelist is defined centrally and can be extended without changing the
   case-check algorithm.
4. Valid domainAction names containing digits, including `_mp4BoxIterate` and
   `_mp4MvhdCreationRead`, produce no function-name violation.
5. Invalid module-level function names continue to be rejected.
6. Existing tests for action-only class methods, private constants, nested
   helpers, logging interpolation rules, and test-file exceptions continue to
   pass.
7. New focused tests cover approved log tokens, rejected unapproved mixed-case
   tokens, and digit-containing domainAction names.

## Verification

- `pytest tests/test_guiNamingLinter.py`
- `pytest`
- `git diff --check`

## Change history

- 2026-09-12: created for the OMP 0.8 backlog after organiseMyVideo linting
  exposed false positives for proper names/acronyms and digit-containing
  domainAction names.
