# ADR-002: Canonical omp runtime package

## Status

Superseded

A separate `omp/` package was not added to this repository. The canonical
runtime package is already `organiseMyProjects`.

## Context

Projects need shared runtime helpers such as logging without taking a runtime
dependency on the `organiseMyProjects` install. Requirement 002 reserves the
`omp` package name for synchronised copies of that infrastructure.

## Decision Drivers

- One canonical implementation.
- Consuming projects remain independently deployable.
- Adding a future runtime module should require only synchronisation in
  downstream repositories.

## Considered Options

1. Keep runtime helpers inside `organiseMyProjects` and require that package
   at application runtime.
2. Copy selected files from `organiseMyProjects/` into each project's `omp/`
   package, leaving the canonical source in the tooling package.
3. Make repository-root `omp/` the canonical runtime package in this
   repository and deploy/sync that directory into consuming projects.

## Decision Outcome

Chosen option 3.

- Canonical runtime modules live in `omp/` at the organiseMyProjects
  repository root.
- Applications import `from omp.logUtils import getLogger, setApplication`.
- `organiseMyProjects.logUtils` remains a compatibility re-export.
- Create, update and `--sync` deploy every `.py` and `.sh` file in `omp/` as
  managed overwrite, with provenance headers and executable bits preserved
  for shell helpers.
- Product-specific modules such as `kohyaConfig.py` stay out of `omp/`.

### Consequences

- Positive: Generated projects do not depend on `organiseMyProjects` at
  runtime.
- Positive: New runtime modules added under `omp/` are picked up automatically
  by create, update and sync.
- Negative: Two import paths exist during the compatibility window
  (`omp.logUtils` and `organiseMyProjects.logUtils`).
- Negative: Generated `pyproject.toml` must map the root `omp` package in
  addition to `src/` modules.

## Requirements

- [002: Runtime infrastructure synchronisation](../requirements/features/002-runtimeInfrastructureSync.md)
