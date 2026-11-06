# ADR-005: Namespaced synchronised runtime helpers

## Status

Accepted

## Context

Requirement 002 needs one canonical source of reusable runtime helpers with
self-contained copies deployed to consuming repositories. ADR-002 previously
proposed a sibling `omp` package, but that decision was superseded. The
package name `omp` denotes organiseMyPhotos; the abbreviation `ompr` denotes
organiseMyProjects. The old proposal conflicts with that ownership and with
the existing `organiseMyProjects` canonical source.

## Decision drivers

- Keep `omp` reserved for organiseMyPhotos, and use `ompr` for
  organiseMyProjects runtime infrastructure.
- Maintain exactly one canonical source for reusable helper implementations.
- Keep consuming projects independently installable and runnable without
  installing organiseMyProjects.
- Preserve existing imports and prevent unrelated project files from being
  overwritten.
- Support deterministic, previewable and verifiable synchronisation.

## Decision

1. The canonical source stays inside the `organiseMyProjects` package, in
   clearly designated reusable runtime modules. Do not create a second,
   independently maintained source tree.
2. The managed deployment namespace in consumers is `ompr`. An application
   imports an explicitly synchronised helper, for example
   `from ompr.logUtils import getLogger`. Never create a shared-runtime
   `omp` package.
3. A manifest maintained by OMPR identifies deployable modules and necessary
   dependencies. Only manifest-listed reusable runtime files are copied;
   business logic, UI, tests, private configuration and unrelated modules are
   excluded.
4. `manageProject` create/update/sync expose a preview and an explicit
   confirmation path, with provenance/version metadata, executable-mode
   preservation where needed, and clear reporting of missing or modified
   managed files. All deployment remains opt-in and avoids overriding
   non-managed, project-owned files.
5. Supported consumers have no install-time or runtime dependency on the
   `organiseMyProjects` distribution for those helpers. Existing
   `organiseMyProjects.*` imports may remain in OMPR itself; consumer
   migrations must be explicit and compatibility-tested.
6. Local data files or packaging owned by an existing `ompr` directory
   cannot be overwritten without a documented ownership migration.

## Rejected options

- A sibling `omp/` tree: conflicts with organiseMyPhotos and duplicates the
  canonical source.
- Direct runtime dependency on organiseMyProjects in every consumer: conflicts
  with independent deployment.
- Blind copying of every file in `organiseMyProjects/`: would propagate
  application-specific behaviour and unnecessary dependencies.

## Consequences

- The new `ompr` package name is distinct from `omp`.
- A manifest, packaging rules, and deployment tests are required before
  REQ-002 can be considered complete.
- Consumers may need a controlled import migration; this is not automatic
  just because the shared files are deployed.
- New scaffolds explicitly include `ompr` in setuptools package lists and
  package data. Existing consumers must update project-owned packaging
  explicitly; runtime deployment does not overwrite it.

## Requirements

- [002: Runtime infrastructure synchronisation](../requirements/features/002-runtimeInfrastructureSync.md)

## Verification

- 2026-11-06: REQ-002 implementation on `feature/002-runtime-sync` passed GitHub Validate workflow, including 637 pytest tests, Black, Ruff, runLinter and agent readiness.
- Isolated consumer tests verify `ompr.logUtils` imports without an installed OMPR toolkit, managed overwrite/collision protections, idempotence and explicit local batch selection.
- Existing consumer import migrations remain opt-in and must be verified independently for each project.
