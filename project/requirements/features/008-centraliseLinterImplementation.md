# 008: Centralise linter implementation

## Status

ToDo — planned for OMP 0.8.

## Outcome

Make the installed `organiseMyProjects` package the single authoritative source
for OMP linting behaviour and remove duplicated linter implementations from
managed projects.

## Problem

OMP currently installs linter functionality as part of the Python package while
also deploying copies such as:

- `tests/runLinter.py`
- `tests/guiNamingLinter.py`

into managed repositories.

This duplicates implementation code across every project, creates a risk that
project-local copies drift from the installed OMP version, and makes it unclear
which linter implementation is authoritative.

## Scope

- Treat the linter implementation shipped by the installed
  `organiseMyProjects` package as the canonical implementation.
- Stop deploying full copies of `tests/runLinter.py` and
  `tests/guiNamingLinter.py` into managed projects when equivalent packaged
  functionality is available.
- Update `manageProject create` and `manageProject update` so new and existing
  projects use the packaged linter rather than maintaining copied
  implementations.
- Remove obsolete OMP-managed project-local linter copies during update only
  when OMP ownership can be established; preserve user-owned or modified files.
- Update generated `.pre-commit-config.yaml`, documentation, agent guidance and
  other OMP-managed references so the documented/default invocation uses the
  installed command, preferably:

  ```bash
  runLinter
  ```

  or the equivalent packaged module invocation where required.
- If a project-local entry point is still needed for compatibility, keep it as
  a minimal wrapper that delegates to the installed OMP implementation rather
  than duplicating linter logic.
- Ensure linter version/behaviour therefore follows the installed OMP package
  version consistently across projects.

## Acceptance criteria

1. A newly created OMP project does not contain a duplicated linter
   implementation when the packaged implementation is available.
2. `manageProject update` migrates an existing OMP-managed project away from
   obsolete copied linter implementations without deleting user-owned or
   modified files.
3. `runLinter` executed from a managed project uses the implementation supplied
   by the currently installed `organiseMyProjects` package.
4. Pre-commit integration invokes the packaged implementation successfully.
5. GUI naming checks continue to operate without requiring a project-local
   `tests/guiNamingLinter.py` implementation.
6. Updating the OMP package is sufficient to update linter behaviour across all
   managed projects; individual projects do not require copied-linter refreshes.
7. Existing linter tests remain in the `organiseMyProjects` repository and cover
   both direct CLI and pre-commit invocation.
8. Migration behaviour is tested for unmodified OMP-managed copies, modified
   project-local copies, and projects that never contained the old files.

## Verification

- `runLinter`
- `pre-commit run --all-files`
- `pytest`
- `git diff --check`

## Change history

- 2026-09-15: created for the OMP 0.8 backlog after identifying that
  `runLinter` and GUI naming linter functionality are installed with the OMP
  package while implementations are also copied into each managed project's
  `tests/` directory.
