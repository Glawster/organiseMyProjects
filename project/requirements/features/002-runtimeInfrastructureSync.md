# 002: Runtime infrastructure synchronisation

## Status

Completed

## Outcome

As a developer maintaining independently deployable projects, I need runtime
helpers owned by organiseMyProjects (OMPR) to be synchronised safely into
each consuming repository under the `ompr` namespace, so that applications
share maintained infrastructure without a runtime dependency on the OMPR
developer toolkit.

## Context

Shared helpers such as logging need one canonical implementation. Existing
ADR-002 proposed a sibling `omp` package, but that ADR is superseded:
`omp` denotes organiseMyPhotos, whereas `ompr` denotes
organiseMyProjects. The canonical helper source remains in
`organiseMyProjects` and is deployed into a managed `ompr` package in
consuming repositories. ADR-005 records the accepted strategy.

## Scope

- Identify a manifest of reusable runtime modules inside the canonical
  `organiseMyProjects` package, starting with logging. Exclude UI, domain
  logic, tests and project-specific configuration.
- Deploy manifest-listed files to a managed `ompr/` namespace in consumers.
  Preserve compatible import behaviour and necessary executable permissions.
- Support safe preview, explicit confirmation, provenance and originating
  version in standard create/update/sync workflows; report every change.
- Never silently overwrite project-owned files or a pre-existing unrelated
  `ompr` package; handle conflicts explicitly.
- Support selected repositories and batch synchronisation without requiring
  consumers to depend at runtime on the toolkit package.
- Document the reserved names: `ompr` = organiseMyProjects and `omp` =
  organiseMyPhotos.
- Keep the canonical source in `organiseMyProjects`, rather than maintaining
  a duplicate root-level source package.

## Out of scope

- Automatically changing every consumer import or application architecture.
- Business logic, databases, OCR, UI, or application-specific configuration.
- Making arbitrary downloaded or GitHub-only repositories writable.
- Introducing a new external runtime service.

## Acceptance criteria

1. A manifest defines exactly which canonical runtime modules may be deployed.
2. The managed output is called `ompr`, never `omp`; standards document both names.
3. Create/update/sync preview the changes and require explicit confirmation.
4. Only recognised managed files are replaced; unmanaged files and collisions
   remain intact with actionable diagnostics.
5. Sync includes origin/version provenance and preserves executable modes where needed.
6. Each targeted consuming repository can import its synchronised helpers as
   `ompr.*` without importing or installing `organiseMyProjects`.
7. Application-specific modules are excluded even when present in the toolkit.
8. An additional reusable module can be added through the manifest and synced
   without modifying the deployment algorithm.
9. A selected-repository run and a batch run report per-repository outcomes
   and do not alter unrelated repositories.
10. Tests verify idempotence, dry-run, overwrite protections, packaging,
    imports, and downstream self-contained runtime behaviour.

## Dependencies and decisions

- [ADR-002](../../adr/002-ompRuntimePackage.md) is superseded and must not be
  used as implementation guidance.
- [ADR-005](../../adr/005-omprRuntimeSync.md) accepts the corrected
  namespace and canonical-source decision.
- Builds on existing `manageProject` managed-file ownership rules.

## Verification

- 2026-11-06 GitHub Validate workflow passed: 637 pytest tests with no failures, Black, Ruff, OMP runLinter and agent readiness.
- `tests/test_runtimeSync.py` verifies preview and idempotence, managed changes, unowned-package and symlink protection, explicit batch selection, shell executable bit, CLI/update integration and isolated imports without an installed OMPR toolkit.
- Newly scaffolded setuptools metadata includes `ompr` and the shell helper as package data; existing project packaging is project-owned and requires explicit migration.
- Live deployment into existing downstream applications was not performed; consumers must independently validate their imports and build artifacts after opting in.

## Change history

- 2026-08-31: a sibling `omp/` package was reverted.
- 2026-10-22: status ToDo -> InProgress — myBoard.
- 2026-11-06: corrected namespace to `ompr`, reconciled superseded ADR-002
  and proposed ADR-005.
- 2026-11-06: completed managed runtime deployment, CLI integration, packaging,
  documentation and isolated tests; GitHub validation passed.
