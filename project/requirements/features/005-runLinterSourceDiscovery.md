# 005: runLinter source directory discovery

## Status

Completed

## Outcome

As a maintainer of a root-package Python project, I need `runLinter` with no
arguments to lint the project package rather than missing `src/` or walking
the whole repository.

## Context

Default discovery previously searched only `src`, `ui` and `tests`. OMP 0.6
projects keep the package at the repository root.

## Scope

- Discover default targets from `pyproject.toml` packaging configuration.
- Support `src/<package>/`, a root-level package matching the repository
  name, and configured setuptools locations.
- Keep `ui/`, `qt/` and `tests/` as auxiliary targets when they exist.
- Do not lint `.` merely because `src/` is absent.
- Deduplicate overlapping discoveries.
- Leave explicit CLI targets unchanged.

## Out of scope

- Changing markup-mode target handling beyond using the same explicit
  targets already supplied.

## Acceptance criteria

1. Given a conventional `src/` layout, when `runLinter` has no targets, then
   `src/` is linted.
2. Given `footballVision/footballVision/`, when no targets are supplied, then
   that package directory is linted and `.` is not.
3. Given setuptools `where` or `packages` configuration, when those paths
   exist, then they are used.
4. Given a configured source path that does not exist, when other plausible
   directories exist, then only the existing directories are used.
5. Given the same directory identified twice, when discovery runs, then it
   appears once.
6. Given no plausible source directory, when discovery runs, then `.` is the
   fallback.
7. Given explicit CLI targets, when `runLinter` runs, then automatic
   discovery is not used.

## Verification

- Unit tests for `lintTargetsDiscover`.
- Existing CLI tests for explicit targets and the no-target message.

## Traceability

- Implementation: `organiseMyProjects/runLinter.py` (`lintTargetsDiscover`)
- Tests: `tests/test_runLinter.py`

## Change history

- 2026-09-11: completed on `release/0.7`.
