# Current Development Increment

## Increment

0.11 — Backlog planning (`0.11a1`)

## Status

InProgress

## Outcome

Define and sequence the 0.11 delivery backlog after 0.10 closeout, with the
branch now at version `0.11a1` and requirement records ready for implementation.

## Objective

Start 0.11 with a prioritised, implementation-ready backlog focused on
repository portfolio UX, list-editing standards, managed-content parity, and
runtime/onboarding consistency refinements identified during alignment review.

## Planned 0.11 backlog

- [025](requirements/features/025-repositoryPortfolioBoard.md): repository
  portfolio board (`myProjects`) above per-repository requirement boards.
- [027](requirements/features/027-listEditingInteractionStandard.md): list/table
  editing interaction standard and enforceable checks.
- [031](requirements/features/031-installedManagedContentParity.md): installed
  wheel managed-content parity across update/check and sync/update paths.
- [032](requirements/features/032-environmentPythonPinPreservation.md): preserve
  stricter project Python pins during managed environment merge.
- [033](requirements/features/033-obsoleteLinterCopyEnforcement.md): enforce
  convergence away from obsolete local linter wrappers/copies.
- [034](requirements/features/034-roleAwareOnboardingContextSeeding.md): align
  migrate/update role detection and onboarding context seeding.
- [035](requirements/features/035-projectNeutralReleaseGuidance.md): deploy
  project-neutral managed release guidance for consumer repositories.
- [036](requirements/features/036-checkAlignedSetupReminders.md): align update
  setup reminders with `DOC-003` check conditions.
- [037](requirements/features/037-standaloneBashLogUtilsSourcing.md): define
  reliable standalone Bash `logUtils.sh` sourcing and fail-fast behaviour.

## Ordering proposal

1. [031](requirements/features/031-installedManagedContentParity.md)
2. [033](requirements/features/033-obsoleteLinterCopyEnforcement.md)
3. [034](requirements/features/034-roleAwareOnboardingContextSeeding.md)
4. [032](requirements/features/032-environmentPythonPinPreservation.md)
5. [036](requirements/features/036-checkAlignedSetupReminders.md)
6. [035](requirements/features/035-projectNeutralReleaseGuidance.md)
7. [037](requirements/features/037-standaloneBashLogUtilsSourcing.md)
8. [025](requirements/features/025-repositoryPortfolioBoard.md)
9. [027](requirements/features/027-listEditingInteractionStandard.md)

## Notes

Backlog items 031-036 are derived from the OMPR 0.10 alignment review in
`organiseMyConda/project/reviews/2026-11-25-ompr010Alignment.md`.
