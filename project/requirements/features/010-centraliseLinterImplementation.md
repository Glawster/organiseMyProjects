# 010: Centralise linter implementation

## Status

Completed — implemented for OMP 0.8.

## Outcome

Make the installed `organiseMyProjects` package the single authoritative source
for OMP linting behaviour and remove duplicated linter implementations from
managed projects.

## Problem

OMP previously installed linter functionality as part of the Python package while
also deploying copies such as:

- `tests/runLinter.py`
- `tests/guiNamingLinter.py`

into managed repositories.

This duplicated implementation code across every project, created a risk that
project-local copies drifted from the installed OMP version, and made it unclear
which linter implementation was authoritative.

## Scope

- Treat the linter implementation shipped by the installed
  `organiseMyProjects` package as the canonical implementation.
- Stop deploying full copies of `tests/runLinter.py` and
  `tests/guiNamingLinter.py` into managed projects when equivalent packaged
  functionality is available.
- Update `manageProject create` and `manageProject update` so new and existing
  projects use the packaged linter rather than maintaining copied
  implementations.
- As part of the OMP 0.8 migration, `manageProject update` must actively remove
  obsolete project-local linter files such as `tests/runLinter.py` and
  `tests/guiNamingLinter.py` when they are recognised as OMP-managed copies.
- Removal is part of the normal update operation, not a separate manual cleanup
  step. The update log must explicitly report each removed obsolete file.
- OMP must not delete a user-owned or locally modified linter file unless
  ownership can be established safely. Ambiguous or modified files must be
  preserved and reported clearly for manual review.
- Re-running `manageProject update` after migration must be idempotent: already
  removed obsolete files must not cause errors or warnings merely because they
  are absent.
- Update generated `.pre-commit-config.yaml`, documentation, agent guidance and
  other OMP-managed references so the documented/default invocation uses the
  installed command:

  ```bash
  runLinter
  ```

- Ensure linter version/behaviour therefore follows the installed OMP package
  version consistently across projects.

## Acceptance criteria

1. A newly created OMP project does not contain a duplicated linter
   implementation when the packaged implementation is available.
2. `manageProject update` removes obsolete `tests/runLinter.py` and
   `tests/guiNamingLinter.py` files when they are recognised as unmodified
   OMP-managed copies.
3. The migration requires no separate cleanup command or manual deletion for
   recognised OMP-managed copies.
4. `manageProject update` preserves user-owned, ambiguous, or locally modified
   files and reports why they were not removed.
5. Removal of each obsolete managed linter file is shown in the update log.
6. A second `manageProject update` is idempotent and does not recreate the old
   files or complain that they are absent.
7. `runLinter` executed from a managed project uses the implementation supplied
   by the currently installed `organiseMyProjects` package.
8. Pre-commit integration invokes the packaged implementation successfully.
9. GUI naming checks continue to operate without requiring a project-local
   `tests/guiNamingLinter.py` implementation.
10. Updating the OMP package is sufficient to update linter behaviour across all
    managed projects; individual projects do not require copied-linter refreshes.
11. Existing linter tests remain in the `organiseMyProjects` repository and cover
    both direct CLI and pre-commit invocation.
12. Migration behaviour is tested for unmodified OMP-managed copies, modified
    project-local copies, ambiguous ownership, and projects that never contained
    the old files.

## Verification

- `pytest`
- `black --check --diff .`
- `ruff check .`
- `runLinter .`
- `manageProject check`

## Change history

- 2026-10-12: implemented for OMP 0.8; packaged linter is authoritative,
  downstream copies are no longer deployed, recognised legacy copies are
  removed by `manageProject update`, and migration/documentation tests were
  added.
- 2026-10-12: renumbered from duplicate backlog identifier 008 to 010 because
  008 was already assigned to existing-project scaffold consistency.
- 2026-09-15: clarified that `manageProject update` itself must remove recognised
  obsolete OMP-managed linter copies, log those removals, preserve ambiguous or
  modified files, and keep the migration idempotent.
- 2026-09-15: created for the OMP 0.8 backlog after identifying that
  `runLinter` and GUI naming linter functionality are installed with the OMP
  package while implementations are also copied into each managed project's
  `tests/` directory.
