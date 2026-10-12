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
- Treat framework-defined callback and command method names as protocol-style
  overrides when their spelling is dictated by the framework rather than by the
  project coding standard.
- Add Textual method names/patterns to the centrally maintained naming exemption
  rules, including at minimum:
  - `action_*` command handlers used by Textual key bindings/actions;
  - `on_*` event/message handlers such as `on_button_pressed`, `on_click`,
    `on_input_changed`, and `on_action_needed_navigate`.
- Do not require Textual `action_*` or `on_*` framework hooks to be renamed to
  action-only/domainAction camelCase names, because changing them would break
  Textual dispatch semantics.
- Keep these exemptions framework-scoped and documented rather than weakening
  naming enforcement for arbitrary snake_case project methods.
- Document the framework/protocol exemption policy and the supported Textual
  patterns in the coding-standard/linter guidance distributed by OMP.

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
8. Textual `action_*` methods such as `action_policy_positive`,
   `action_sender_edit`, and `action_choose_filter` produce no naming violation.
9. Textual `on_*` event/message handlers such as `on_button_pressed`,
   `on_click`, and `on_input_changed` produce no naming violation.
10. Arbitrary snake_case methods that are not recognised framework hooks remain
    subject to the normal OMP method naming rules.
11. The OMP coding-standard/linter documentation explains that framework- or
    protocol-mandated names are exempt only where the external API requires the
    spelling, with Textual `action_*` and `on_*` documented as supported cases.
12. Regression tests include representative Textual stubs/classes so future
    linter changes do not reintroduce these false positives.

## Verification

- `pytest tests/test_guiNamingLinter.py`
- `pytest`
- `runLinter`
- `git diff --check`

## Change history

- 2026-09-12: created for the OMP 0.8 backlog after organiseMyVideo linting
  exposed false positives for proper names/acronyms and digit-containing
  domainAction names.
- 2026-10-12: extended after `runLinter` on mailAgent reported Textual
  `action_*` and `on_*` methods as invalid names; require documented,
  centrally maintained framework-hook exemptions and regression tests.
