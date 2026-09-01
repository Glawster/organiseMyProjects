# 003: OMP 0.6 managed migration and project scaffold

## Status

Completed

## Outcome

As an OMP maintainer, I need project creation and managed-file updates to follow
the OMP 0.6 repository standard so that new projects start in a compliant
state and established projects can adopt managed path changes safely.

## Context

OMP 0.5 distributes repository-layout guidance that is broader than the
structure created by `manageProject --create`. In particular, the Python
scaffold uses a generic `src/` package root and may create a root `main.py`,
while the 0.6 convention is that every new Python project is an importable
Python package whose package directory is named after the project and lives at
the repository root.

OMP 0.6 also relocates managed documentation from legacy `.github/` paths to
`documentation/`. `manageProject --update` must be able to deploy the canonical
managed file at its new path and remove the obsolete managed copy, but only
where OMP can establish that the old file is OMP-managed. User-owned or
ambiguous files must not be deleted.

## Scope

### Managed-file relocation cleanup

- Extend the deterministic migration mechanism so that it supports managed
  path relocations as well as filename renames.
- For each recognised relocation, deploy or update the current managed file at
  its canonical destination.
- Remove the obsolete source-path copy only when OMP can safely establish that
  it is OMP-managed.
- Never delete an arbitrary file merely because it occupies a legacy managed
  path.
- For the 0.5 to 0.6 migration, support at least:
  - `.github/repositoryLayout.md` to `documentation/repositoryLayout.md`;
  - `.github/requirementsManagement.md` to
    `documentation/requirementsManagement.md`;
  - `.github/howToRelease.md` to `documentation/howToRelease.md`.
- Log relocation cleanup explicitly. Applied updates should use messages
  equivalent to:

  ```text
  updated <new-path>
  removed obsolete managed file <old-path>
  ```

- Dry-run output must describe the same intended relocation without changing
  the working tree.
- Re-running an already completed relocation must be idempotent.

### Standard Python package scaffold

- All newly created OMP Python projects must be importable Python packages.
- OMP must use a root-level package directory named after the project. OMP 0.6
  does not use a generic `src/` directory for newly created projects.
- A project named `footballVision` therefore uses:

  ```text
  footballVision/
  ├── footballVision/
  │   ├── __init__.py
  │   └── ...
  ├── documentation/
  ├── project/
  ├── tests/
  ├── pyproject.toml
  ├── footballVisionEnvironment.yml
  ├── README.md
  └── .gitignore
  ```

- Generated application and domain Python modules belong inside the project
  package unless they have a genuine repository-level responsibility.
- A root-level `main.py` is not part of the standard scaffold.
- Executable behaviour is role-dependent:
  - libraries require no executable entry point;
  - command-line applications declare a console-script entry point in
    `pyproject.toml`;
  - GUI or standalone applications expose an application entry point from the
    package;
  - `package/__main__.py` may be used where `python -m package` is an intended
    interface.
- `pyproject.toml` is the authoritative packaged-Python dependency and entry
  point definition for new projects.
- Create a project-specific camelCase Conda environment file named
  `<projectName>Environment.yml`.
- The documented Conda workflow must install the project in editable mode.
- Do not make `requirements.txt` the primary dependency mechanism for newly
  scaffolded packaged projects.
- The generated management/documentation tree must match the OMP repository
  layout, including the applicable `project/requirements/`, `project/adr/`,
  `project/reviews/`, `documentation/` and `tests/` structure.

### Documentation alignment

Update all affected managed and maintainer documentation so that OMP describes
one canonical project structure. At minimum review:

- `documentation/repositoryLayout.md`;
- `documentation/developer.md`;
- `.github/agent-instructions.md` where it states Python layout or dependency
  policy;
- generated README content and scaffold templates;
- release notes/current increment documentation.

Use **Python package** for an importable directory containing `__init__.py` and
**Python module** for an individual `.py` module.

## Out of scope

- Automatically moving arbitrary existing application code from `src/` into a
  new package directory.
- Reorganising an established project's application layout during ordinary
  `manageProject --update` unless a separate migration can prove the operation
  safe and deterministic.
- Deleting user-owned files at legacy managed paths.
- Requiring executable entry points for library-only packages.

## Acceptance criteria

1. Given a recognised OMP-managed file at a legacy path, when
   `manageProject --update --confirm` runs, then the current managed file exists
   at the canonical path and the obsolete managed copy is removed.
2. Given the same relocation in dry-run mode, when update runs without
   confirmation, then the intended update/removal is reported and no file is
   changed or removed.
3. Given a file at a legacy path whose OMP ownership cannot be established,
   when update runs, then the file is preserved and the ambiguity is reported.
4. Given a completed managed relocation, when update is run again, then no
   additional file changes occur.
5. The three 0.5 to 0.6 managed documentation relocations listed in this
   requirement are covered by automated tests.
6. Given `manageProject --create footballVision`, then the generated project
   contains `footballVision/__init__.py` and does not contain a scaffolded
   `src/` directory.
7. A newly generated project has a valid `pyproject.toml` that describes the
   package and supports editable installation.
8. A newly generated project contains `footballVisionEnvironment.yml` (using
   the actual project name) and the documented Conda workflow installs the
   package editable.
9. A newly generated project contains the standard project-management,
   documentation and test directories required by the repository-layout
   guidance.
10. A library scaffold does not receive a root `main.py` solely to satisfy a
    generic layout.
11. CLI/application entry points are generated or declared according to the
    selected/detected project role rather than through a universal root
    `main.py`.
12. Managed documentation and generated README guidance describe the same
    package structure that `createProject()` actually creates.
13. Existing projects are not blindly reorganised by `manageProject --update`.
14. Automated tests cover scaffold tree creation, package importability,
    packaging/environment metadata, dry-run behaviour, confirmed relocation,
    obsolete managed-file removal, ambiguous-file protection and idempotent
    reruns.

## Dependencies and decisions

- Builds on the safe-update ownership principles from requirement 001.
- Runtime logging continues to live in the `organiseMyProjects` package.
- The no-`src/` root-package convention is an OMP 0.6 project-layout decision.
- [ADR-003](../../adr/003-rootPackageScaffold.md) records that layout choice.

## Verification

- Unit tests for managed relocation ownership and removal logic.
- Unit tests for dry-run and idempotent update behaviour.
- Scaffold tree tests for representative project names.
- Import/install tests for generated packages.
- Tests that generated `pyproject.toml` and Conda environment metadata are
  internally consistent.
- `manageProject --check` against a newly generated fixture repository.
- Full OMP test, lint and markup validation before release.

## Traceability

- Implementation: `organiseMyProjects/manageProject.py`
- Tests: `tests/test_omp06Scaffold.py`, `tests/test_createProject.py`
- Documentation: this requirement plus OMP 0.6 documentation updates
- Pull request: pending
- Agent runs: v0.6 implementation

## Change history

- 2026-08-31: created for OMP 0.6 from scaffold review and managed-file
  relocation backlog.
- 2026-08-31: completed — root-package scaffold and managed-path relocation
  delivered on `release/0.6`.
