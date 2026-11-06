# 002: Implement OMPR runtime synchronisation

## Assignment

Implement [requirement 002](../features/002-runtimeInfrastructureSync.md)
after reviewing [ADR-005](../../adr/005-omprRuntimeSync.md) and all project
agent/developer instructions. Reconcile any decision issues before coding.

## Key naming rule

`ompr` means organiseMyProjects; `omp` means organiseMyPhotos.
Do not create or deploy an `omp` runtime package. ADR-002 is superseded.
Canonical reusable helper implementations stay in `organiseMyProjects`;
their explicitly managed deployment copies live under `ompr` in consumers.

## Work

- Audit existing managed-file ownership, create/update/sync and packaging.
- Implement manifest-directed deployment, provenance, safe dry-run, explicit
  confirmation, collision diagnostics and per-repository summaries.
- Add selected-target and batch sync without mutating unrelated repositories.
- Keep application-owned modules and configuration out of deployed packages.
- Verify consumer independence from an installed OMPR toolkit.
- Update relevant guides and ADR status only when the decision is validated.

## Verification and handoff

Run focused tests in isolated repositories (idempotence, no-overwrite,
permissions, import isolation, packaging, batch selection), full pytest,
runLinter, Black and git diff --check. Report each acceptance criterion with
concrete evidence and any remaining exceptions. Do not mark Completed on
design-only evidence.
