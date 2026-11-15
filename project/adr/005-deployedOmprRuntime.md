# ADR-005: Deployed OMPR runtime

## Status

Accepted — 2026-11-01. Replaces the runtime deployment proposal in superseded
[ADR-002](002-ompRuntimePackage.md).

## Context

[Requirement 002](../requirements/features/002-runtimeInfrastructureSync.md)
requires applications to run independently of installed OMPR development tools.
The canonical runtime implementation already lives in `organiseMyProjects/`.
The user clarified that OMP means organiseMyPhotos and OMPR means
organiseMyProjects.

## Decision

Keep canonical runtime sources in `organiseMyProjects/`. Deploy an explicit
allowlist into consumers' `ompr/` packages, starting with `logUtils.py`,
`logUtils.sh`, `version.py` and a minimal initializer. Do not deploy the tooling
package initializer, UI or application code. Do not create a sibling runtime
package in the canonical repository.

New applications import `ompr.logUtils` and package the deployed runtime,
including shell resources. OMPR tooling continues using
`organiseMyProjects.logUtils`. Bash applications source their deployed
`ompr/logUtils.sh` by a path relative to their application root.

Create and update deploy local managed copies. Remote instruction sync adds
runtime deployment only with `--runtime`, preserving instruction-only usage
for non-Python repositories. Both use one manifest. Remote runtime updates use
an atomic Git tree commit so file modes are explicit and a partial runtime
package is never committed.

Managed files carry provenance and may be overwritten. Existing unmarked
packages/files and symlinks require review. Ordinary updates preserve
application code and packaging and report migration work. Consumers must
migrate imports, include `ompr` and its resources in their distributions, and
verify an isolated installation before removing OMPR from runtime dependencies.

## Consequences

- Applications remain self-contained while OMPR owns shared helper behaviour.
- Consumers require explicit migration from previous runtime imports.
- An allowlist prevents accidental deployment of unrelated tooling; new shared
  helpers must be self-contained or include all dependencies in that manifest.
- Existing packaging layouts remain project-owned; sync alone does not prove
  that an established application's migration is complete.
- OMS, OMV and organiseMyPhotos can adopt deployed copies through reviewed
  updates; this decision does not change those repositories automatically.
