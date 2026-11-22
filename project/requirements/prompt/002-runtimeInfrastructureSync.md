# 002: Runtime infrastructure synchronisation

## Assignment

Implement and verify [requirement 002](../features/002-runtimeInfrastructureSync.md)
using [ADR-005](../../adr/005-deployedOmprRuntime.md). Canonical sources remain
in `organiseMyProjects/`; consumers receive a managed `ompr/` runtime subset.
OMP means organiseMyPhotos, not organiseMyProjects.

Apply the subsequent opt-in policy from
[requirement 030](../features/030-optInLocalRuntime.md) and
[ADR-006](../../adr/006-optInLocalRuntime.md): review this requirement's deployed
runtime capability with local runtime enabled; do not restore unconditional
deployment to new or existing projects.

## Boundaries

Keep application code and packaging project-owned on update. Report migration
needs rather than rewriting arbitrary projects. Reject unowned runtime paths
and symlinks. Do not deploy business logic or UI, or perform confirmed remote
sync as part of local implementation verification.

## Evidence

Map acceptance criteria to focused deployment/sync tests, independent generated
application execution and a built/installed distribution without OMPR. Run the
full suite, Black, Ruff, source/markup lint and whitespace checks. Report
remaining gaps and impacts on OMPR, OMS, OMV and organiseMyPhotos.
