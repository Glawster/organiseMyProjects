# 002: Runtime infrastructure synchronisation

## Status

InReview

## Outcome

Applications use synchronised OMPR runtime helpers so that they can run without
installing the organiseMyProjects development tools.

## Context

OMPR means organiseMyProjects. OMP means organiseMyPhotos. The consumer runtime
package is `ompr`; `omp` is not a name for organiseMyProjects infrastructure.
Canonical helpers remain in `organiseMyProjects/`, with no second runtime
package in this repository.

## Scope

- Deploy an explicit allowlist of self-contained runtime files to consumers'
  `ompr/` packages through create, update and opt-in batch/repository sync.
- Initially deploy Python logging, Bash logging, OMPR version metadata and a
  minimal package initializer. Tooling, UI and application code are excluded.
- Generate application imports using `ompr.logUtils` and package the runtime,
  including shell resources, with new applications.
- Include source repository, release and managed ownership in deployment headers.
- Refresh managed copies even when locally modified; preserve executable bits,
  support dry runs, avoid timestamp churn and keep repeated updates idempotent.
- Refuse ambiguous ownership, symlinks and collisions before runtime deployment.
- Preserve existing application code and packaging. Report legacy imports and
  required packaging/dependency review rather than rewriting arbitrary projects.
- Keep OMPR available as a development tool; it is not required at application
  runtime once the consumer has completed the reported migration.

## Out of scope

- Automatically rewriting arbitrary application imports or packaging metadata.
- Synchronising business logic, UI, databases, project configuration or tests.
- Inventing configuration/YAML/filesystem helpers without a concrete shared need.
- Deploying runtime code to other repositories without an explicit confirmed sync.

## Acceptance criteria

1. New projects receive a managed `ompr` package containing only the approved
   runtime subset, sourced from `organiseMyProjects/`.
2. Generated application entry points import runtime helpers through `ompr`;
   generated distributions include that package and its Bash resource.
3. A generated application can import and use the helpers in an isolated Python
   process without site packages, the OMPR checkout or organiseMyProjects imports.
4. Each deployed file identifies the canonical repository, release and ownership.
5. Create/update and opt-in repository/batch sync use the same runtime manifest.
6. Updates replace locally changed managed helpers, preserve executable modes,
   leave unchanged content untouched and produce no further changes on rerun.
7. Dry runs report changes without writing runtime files, Git refs or API data.
8. Unowned runtime paths and symlink destinations are preserved and reported;
   application code and packaging remain unchanged during ordinary updates.
9. Updates report detected legacy organiseMyProjects imports and the required
   consumer packaging/dependency review. Migration instructions explain how to
   verify an independent installation before removing the runtime dependency.
10. Adding an approved self-contained helper to the manifest extends deployment
    without consumer-specific changes to the synchronisation implementation.
11. Guidelines distinguish OMPR/`ompr` from organiseMyPhotos/OMP, retain canonical
    sources in `organiseMyProjects` and document consumer runtime imports.

## Dependencies and decisions

- [ADR-005: Deployed OMPR runtime](../../adr/005-deployedOmprRuntime.md).
- [ADR-001: File ownership](../../adr/001-fileOwnershipPolicies.md).
- [ADR-002](../../adr/002-ompRuntimePackage.md) is superseded and must not be
  used as an implementation instruction.

## Verification

- `tests/test_runtimeDeployment.py`: clean-process runtime and application
  import, wheel contents/install, managed overwrite, idempotence, permissions,
  dry runs, collisions, source protection and migration reports.
- Sync boundary tests cover Git tree payloads, ownership, mode preservation,
  API failures, dry runs, idempotence and shared-manifest wiring.
- Existing create/update/sync regressions and full suite in the `ompr` environment.
- Black, Ruff, source/markup lint and `git diff --check`.

## Change history

- 2026-08-31: original runtime proposal; sibling canonical package was reverted.
- 2026-10-22: set InProgress through myBoard.
- 2026-11-01: agreed canonical sources in organiseMyProjects and independent
  consumer deployment; user clarified OMPR/ompr naming versus organiseMyPhotos.
