# ADR-003: Root-level project Python package

## Status

Accepted

## Context

OMP 0.5 created a generic `src/` directory and a root `main.py` for every new
project. The documented 0.6 repository layout is a root-level Python package
named after the project, with role-dependent entry points and
`pyproject.toml` as the packaging source of truth.

## Decision Drivers

- Generated projects should match the layout OMP documents.
- Libraries should not receive a placeholder executable.
- Existing `src/` application code must not be moved by ordinary update.

## Considered Options

1. Keep the generic `src/` scaffold and root `main.py`.
2. Create a root-level package named after the project, with no universal
   `main.py`, and declare CLI/GUI entry points only when that role is selected.

## Decision Outcome

Chosen option 2.

- `createProject footballVision` creates `footballVision/footballVision/`.
- `pyproject.toml` lists the project package and the synchronised `omp`
  package.
- The Conda environment file is `<projectName>Environment.yml` and installs
  the project editable.
- `--ui` / `--qt` place UI modules inside the project package and add
  `package/__main__.py` plus a console-script entry point.
- `manageProject --update` does not move existing `src/` trees.

### Consequences

- Positive: New projects are importable packages that match repository-layout
  guidance.
- Negative: Established `src/` projects keep their layout until a separate,
  proven migration exists.

## Requirements

- [003: OMP 0.6 managed migration and project scaffold](../requirements/features/003-omp06ManagedMigrationAndScaffold.md)
