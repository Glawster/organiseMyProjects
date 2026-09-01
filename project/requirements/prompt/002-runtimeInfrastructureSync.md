# Requirement: 002

Source: project/requirements/features/002-runtimeInfrastructureSync.md
Role: implement

Read the authoritative requirement and all applicable repository instructions
before changing anything. Deliver every acceptance criterion in requirement
002 while preserving its exclusions. Follow ADR-002 for the canonical `omp`
package location. Do not copy application business logic or UI code into
`omp`.

Limit changes to the runtime package, create/update/sync deployment, related
documentation, requirement or ADR traceability, and tests needed to prove the
criteria.

Verify with:

- focused omp runtime and sync tests;
- the full pytest suite;
- an import check that a generated project loads `omp` without importing
  `organiseMyProjects`.

If the requirement is ambiguous or its outcome must change, stop and report
the decision needed. Do not infer new scope.

Handoff with:

- files changed and why;
- an acceptance-criterion-to-evidence mapping;
- commands run and results; and
- assumptions, risks, decisions, and unresolved items.
