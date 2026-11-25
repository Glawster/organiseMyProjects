# 034: Role-aware onboarding context seeding

## Status

ToDo

## Outcome

As a maintainer onboarding existing repositories, I need migrate/update to seed
the correct project role and required context files in one coherent flow so
that onboarding does not leave projects in contradictory intermediate states.

## Context

The OMPR 0.10 alignment review observed `manageProject migrate` initially wrote
`role: "library"` before update detected `standalone-application`. Update then
appended `localRuntime` but did not seed all missing context files that still
required separate migration steps.

## Scope

- Detect and persist project role deterministically during onboarding.
- Ensure migrate/update use consistent role inference and do not seed known
  incorrect default roles.
- Seed missing managed context files required for role-consistent onboarding,
  without overwriting project-owned content.
- Keep onboarding idempotent across repeated migrate/update runs.

## Out of scope

- New role definitions unrelated to onboarding correctness.
- Overwriting project-authored documentation or requirement content.

## Acceptance criteria

1. Given an existing repository enters onboarding, when migrate/update run in
   sequence, then the persisted role matches detected repository characteristics
   without contradictory interim role values.
2. Given required managed context files are missing, when onboarding runs, then
   they are seeded according to ownership rules without clobbering project-owned
   files.
3. Given onboarding reruns after initial seeding, when migrate/update run
   again, then role and seeded-context state remain stable and idempotent.

## Dependencies and decisions

- Builds on requirements 001 and 008 onboarding consistency boundaries.

## Verification

- Add onboarding tests that cover role detection, context seeding, and
  idempotent re-run behaviour.
- Validate seeded-file ownership handling against update/check expectations.

## Change history

- 2026-11-25: created from OMPR 0.10 alignment review findings recorded in
  `organiseMyConda/project/reviews/2026-11-25-ompr010Alignment.md`.
