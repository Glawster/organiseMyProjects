# Requirement 034 implementation prompt

Implement requirement 034 ([Role-aware onboarding context seeding](../features/034-roleAwareOnboardingContextSeeding.md)).

## Goal

Make onboarding role detection and context-file seeding coherent across
migrate/update so projects are not left in contradictory interim states.

## Mandatory outcomes

- Detect role once per onboarding context and persist consistent role metadata.
- Prevent incorrect seeded default roles during migrate/update flows.
- Seed required managed onboarding context files without overwriting
  project-owned files.
- Keep onboarding idempotent across repeated runs.

## Constraints

- Preserve existing ownership protections.
- Avoid broad changes unrelated to onboarding role/context alignment.

## Deliverables

- migrate/update onboarding logic updates.
- Tests for role consistency, context seeding, and idempotency.
