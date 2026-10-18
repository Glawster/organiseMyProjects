# Current Development Increment

## Increment

0.9 — Acceptance close-out, internal patch removal, runLinter reporting and
runtime architecture decision

## Status

Planning agreed — scope fixed; implementation not yet started.

## Objective

Close out requirements 004 and 012, move import-time patch behaviour back into
the modules that own it, deliver pytest-style runLinter reporting, and decide
and document the runtime-sharing architecture for requirement 002 so it can be
implemented in 0.10.

## Requirements

- [004: Requirement, prompt and directory-index layout](requirements/features/004-requirementDocumentationLayout.md) — Completed; all acceptance criteria verified in the 0.9 review.
- [012: Shared TUI button presentation](requirements/features/012-sharedTuiButtonPresentation.md) — InProgress; style tests run in the `ompr` environment; verify downstream `mailAgent` adoption for acceptance criteria 5 and 6.
- [013: runLinter pytest-style reporting](requirements/features/013-runLinterPytestStyleReporting.md) — ToDo; confirm proposed format, exit codes and quiet/verbose modes, then implement after the patch-removal refactor.
- [014: OMPR test environment](requirements/features/014-omprTestEnvironment.md) — Completed; run tests and release validation in the `ompr` Conda environment.
- [002: Runtime infrastructure synchronisation](requirements/features/002-runtimeInfrastructureSync.md) — ToDo; the no-runtime-dependency goal is retained. 0.9 delivers a new ADR deciding where canonical shared runtime code lives and how it is synchronised, reconsidering rather than reviving superseded ADR-002. Implementation is deferred to 0.10. The ADR must also settle the reserved package name: `omp` denotes organiseMyPhotos, so it cannot mean organiseMyProjects (OMPR).

## Internal refactor (no requirement)

Remove the six import-time patch installations from
`organiseMyProjects/__init__.py` (`requirementLayout`,
`requirementsPromptIndex`, `linter08`, `linterCentralisation`) by moving their
behaviour into `manageProject`, `agentCheck`, `guiNamingLinter` and
`runLinter`. Existing tests define the behaviour and must remain green.

## Planned order

1. Housekeeping — done: removed duplicate
   `documentation/omp-agent-portability-design-proposal(1).md`; captured
   requirements 013 and 014.
2. Requirement 014 test environment — done.
3. Requirement 004 evidence and close-out — done.
4. Patch-removal refactor.
5. Requirement 013.
6. Requirement 012 downstream verification in `mailAgent`.
7. Requirement 002 ADR and requirement refinement.
8. Release checks per `documentation/howToRelease.md`.

## Not in 0.9

- `origin/feature/0.8-list-editing-standard` — left untouched; any future
  list-editing requirement takes the next available number.
- Repository-wide rename of "OMP" to "OMPR" for organiseMyProjects in
  existing documentation; candidate for 0.10.
- `origin/docs/project-self-discovery` and
  `origin/standards/branch-squash-workflow` — not requirements; the latter
  conflicts with the release-branch model in `documentation/howToRelease.md`.

## Verification still required

- `runLinter .` currently reports four findings in this repository
  (`syncAgentInstructions.py` LOG-SEC-001/002/003, `manageProject.py` logging
  case) while exiting `0`; requirement 013 makes these release-blocking.
- Render the adopted shared buttons in the downstream `mailAgent` checkout.
- Run the full release validation for every 0.9 change.

## Immediate next action

Confirm the proposed details of requirement 013, then start the patch-removal
refactor in the `ompr` environment.
