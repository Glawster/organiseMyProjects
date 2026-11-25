# 036: Check-aligned setup reminders

## Status

ToDo

## Outcome

As a maintainer running update, I need setup-command reminder logs to align
with check outcomes so that update only asks for documentation changes when
check would report the corresponding deficiency.

## Context

The OMPR 0.10 alignment review found update continued logging setup/test
command reminders after the repository already documented those commands in
README and additional instructions.

## Scope

- Align update reminder emission with check's `DOC-003` logic.
- Avoid reminder noise when command documentation already satisfies check.
- Keep reminder behaviour deterministic across repeated update runs.

## Out of scope

- Introducing new documentation policy categories beyond the current check rules.
- Replacing current check codes or diagnostics taxonomy.

## Acceptance criteria

1. Given command documentation already satisfies check expectations, when
   update runs, then setup-command reminders are not emitted.
2. Given command documentation is missing and check would report `DOC-003`,
   when update runs, then reminder messaging is emitted.
3. Given update/check run repeatedly with no documentation changes, when
   reminder logic evaluates, then output remains stable and predictable.

## Dependencies and decisions

- Depends on existing `DOC-003` check semantics as the single source of truth
  for command-documentation deficiency.

## Verification

- Add tests that assert reminder presence/absence matches `DOC-003` outcomes.
- Validate update/check messaging consistency in representative fixtures.

## Change history

- 2026-11-25: created from OMPR 0.10 alignment review findings recorded in
  `organiseMyConda/project/reviews/2026-11-25-ompr010Alignment.md`.
