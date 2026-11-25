# Requirement 036 implementation prompt

Implement requirement 036 ([Check-aligned setup reminders](../features/036-checkAlignedSetupReminders.md)).

## Goal

Align update reminder logs with check evidence so setup-command reminders appear
only when `DOC-003` would report missing command documentation.

## Mandatory outcomes

- Gate reminder emission on the same condition set as `DOC-003`.
- Suppress reminder noise when documentation already satisfies check.
- Keep reminder behaviour deterministic across repeated update runs.

## Constraints

- Keep existing check taxonomy unchanged.
- Avoid adding unrelated logging policy.

## Deliverables

- Update-path reminder logic changes.
- Tests that assert reminder presence/absence matches `DOC-003` outcomes.
