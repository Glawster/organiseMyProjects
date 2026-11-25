# Requirement 035 implementation prompt

Implement requirement 035 ([Project-neutral release guidance deployment](../features/035-projectNeutralReleaseGuidance.md)).

## Goal

Ensure managed release guidance deployed to consumers is project-neutral and
free from OMPR-internal release-history specifics.

## Mandatory outcomes

- Define a neutral managed release-guide baseline for consumer repositories.
- Keep OMPR-specific release-history details in OMPR-owned docs only.
- Ensure update/check remain consistent with the neutral deployed guide.

## Constraints

- Preserve managed ownership and idempotent deployment semantics.
- Do not remove valid project-local exception documentation.

## Deliverables

- Managed release-guide source/deployment updates.
- Tests/fixtures validating neutral guide deployment.
