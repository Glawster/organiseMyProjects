# 014: OMPR test environment

## Status

ToDo

## Outcome

As an OMPR maintainer, I need a defined Conda test environment for
organiseMyProjects, and a test suite that behaves predictably outside it, so
that release evidence is complete and reproducible without installing
test-only dependencies into every environment that uses OMPR.

## Context

OMPR is a development tool installed in many Conda environments. Its runtime
dependencies are deliberately small, but its own test suite needs development
dependencies such as `pytest`, `ruff`, `black` and `textual`, the last for
rendering the shared `myStyles.css` Textual styles.

During 0.9 planning the full suite was run from a general-purpose environment
(`py313`) without `textual`, and six shared-style tests failed with
`ModuleNotFoundError`. The fix was to install `textual` into that shared
environment, which is the kind of pollution a dedicated test environment
avoids.

The repository already contains an `environment.yml` defining an
`organiseMyProjects` environment with `-e .[dev]`, but the environment had not
been created, and the filename does not follow OMPR's own
`<projectName>Environment.yml` convention used for generated projects.

## Scope

- Provide `organiseMyProjectsEnvironment.yml` defining the `organiseMyProjects`
  Conda environment, installing OMPR in editable mode with the `dev` extras.
- Replace the existing `environment.yml` and update its references in
  `MANIFEST.in` and `.github/additional-instructions.md`.
- Tests that need an optional development dependency, such as `textual`, skip
  with a clear reason when it is not installed instead of failing at import.
- Document creating, updating and using the environment in
  `documentation/testingProcess.md`.
- Make the release checklist in `documentation/howToRelease.md` run validation
  inside the `organiseMyProjects` environment and treat any dependency-related
  skip as a release failure.
- Keep OMPR's runtime dependencies unchanged so it remains cheap to install in
  any environment.

## Out of scope

- Changing how `manageProject` names or manages environment files for
  downstream projects.
- Removing `textual` or other packages from existing shared environments;
  that is a manual clean-up.
- CI configuration beyond what the release checklist already covers.
- Alternative environment managers such as `venv`, `tox` or `nox`.

## Acceptance criteria

1. Given a clean machine with Conda, when
   `conda env create -f organiseMyProjectsEnvironment.yml` is run, then an
   `organiseMyProjects` environment exists with OMPR installed in editable mode
   and every `dev` extra available.
2. Given the `organiseMyProjects` environment, when `pytest` is run, then the
   full suite runs with no dependency-related skips.
3. Given an environment where OMPR is installed without `textual`, when
   `pytest` is run, then the shared-style tests are reported as skipped with a
   reason naming the missing dependency, and no test errors at import.
4. Given the repository, when it is inspected, then `environment.yml` no longer
   exists and no packaging metadata or guidance refers to it as OMPR's own
   environment file.
5. Given `documentation/testingProcess.md`, when read, then it explains how to
   create, update and activate the test environment.
6. Given `documentation/howToRelease.md`, when the release checklist is
   followed, then validation runs in the `organiseMyProjects` environment and a
   dependency-related skip blocks the release.
7. Given OMPR's runtime dependencies, when this requirement is complete, then
   they are unchanged.

## Dependencies and decisions

- Supports release evidence for requirement 012 acceptance criterion 9, which
  depends on the `textual` style tests running.
- Relates to requirement 002: once shared runtime code is synchronised into
  projects, OMPR remains a development tool in each environment rather than a
  runtime dependency.
- Open question: `manageProject` creates `<packageName>Environment.yml` for new
  projects but update still manages `environment.yml`, and
  `.github/agent-instructions.md` still requires `environment.yml`. Resolving
  that downstream inconsistency is outside this requirement.
- No architecture decision is expected.

## Verification

- Create the environment from the file and run `pytest`, confirming no skips.
- Run `pytest` from an environment without `textual`, confirming clean skips.
- `runLinter --markup` on the changed documentation.

## Change history

- 2026-10-18: created — 0.9 planning found OMPR's tests depended on whichever
  Conda environment happened to be active; agreed to define a dedicated test
  environment.
