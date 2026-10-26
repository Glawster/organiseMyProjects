# Current Development Increment

## Increment

0.9 — Acceptance close-out, internal patch removal, runLinter reporting and
runtime architecture decision

## Status

In progress — 004, 012, 013, 014, 021 and the patch-removal refactor done; 002
and release checks remain.

## Objective

Close out requirements 004 and 012, move import-time patch behaviour back into
the modules that own it, deliver pytest-style runLinter reporting, and decide
and document the runtime-sharing architecture for requirement 002 so it can be
implemented in 0.10.

## Requirements

- [004: Requirement, prompt and directory-index layout](requirements/features/004-requirementDocumentationLayout.md) — Completed; all acceptance criteria verified in the 0.9 review.
- [012: Shared TUI button presentation](requirements/features/012-sharedTuiButtonPresentation.md) — Completed; style tests run in the `ompr` environment. `mailAgent` adopted the shared `button-group` on both execute rows in `f75f694`, removing local width/height/padding overrides; headless render tests measure one-row buttons, equal widths, one-column gaps and one free row around each group.
- [013: runLinter pytest-style reporting](requirements/features/013-runLinterPytestStyleReporting.md) — Completed; downstream projects with findings now fail `runLinter` (for example `mailAgent`: one `NAM-003`).
- [014: OMPR test environment](requirements/features/014-omprTestEnvironment.md) — Completed; run tests and release validation in the `ompr` Conda environment.
- [002: Runtime infrastructure synchronisation](requirements/features/002-runtimeInfrastructureSync.md) — InProgress; the no-runtime-dependency goal is retained. 0.9 delivers a new ADR deciding where canonical shared runtime code lives and how it is synchronised, reconsidering rather than reviving superseded ADR-002. Implementation is deferred to 0.10. The ADR must also settle the reserved package name: `omp` denotes organiseMyPhotos, so it cannot mean organiseMyProjects (OMPR).
- [021: Requirement board](requirements/features/021-myBoard.md) — Completed; myBoard lists each requirement in one column. A confirmed move updates the record, the index and the increment together. The detail shows the linked branch, commits and changed files. Checks, runLinter and pytest run on request, and a pytest failure stays with the requirement it names.
- [022: Agent session listing](requirements/features/022-agentSessions.md) — Completed; merged into release/0.9 with parser, CLI subprocess and shared-logging evidence.
- [023: Requirement board editing](requirements/features/023-myBoardEditing.md) — InProgress; edit selected requirement metadata and prose through the confirmed myBoard CLI workflow.
- [024: Requirement board branch versions](requirements/features/024-myBoardBranchVersions.md) — InProgress; show unmerged local and remote-only branches with their OMP versions.
- [026: Shared TUI style mockup](requirements/features/026-sharedTuiStyleMockup.md) — Completed; generate an SVG from the shared Textual stylesheet.

## Internal refactor (no requirement)

Done: the six import-time patch installations are removed from
`organiseMyProjects/__init__.py`. `linter08` and `linterCentralisation` are
folded into `guiNamingLinter`, `runLinter` and `manageProject`; `manageProject`
calls `layoutMigrate` and `promptIndexEnsure` explicitly; the requirement and
README checks live in `agentCheck`. All existing tests pass unchanged apart
from imports.

Follow-up candidate: scaffold `requirementsIndex.md` and `adrIndex.md`
directly instead of writing legacy `README.md` indexes that update then
migrates.

## Backlog

Captured on 2026-10-20 from the `mailAgent` review; all ToDo and not yet
scheduled within the planned order below.

- [015: Requirement record conformance checks](requirements/features/015-requirementRecordConformance.md) — Completed; REQ-007 to REQ-012 added to `manageProject --check`.
- [016: Requirement naming correction during update](requirements/features/016-requirementNamingCorrection.md) — Completed; `manageProject --update` corrects names, prompts, headings and links.
- [017: Requirements guide clarifications](requirements/features/017-requirementsGuideClarifications.md)
- [018: Framework override naming exemptions beyond Textual](requirements/features/018-frameworkOverrideNamingExemptions.md)
- [019: Environment and test configuration consistency](requirements/features/019-environmentAndTestConfigConsistency.md) — resolves the open question in 014.
- [020: Documentation completeness checks](requirements/features/020-documentationCompletenessChecks.md)
- [025: Repository portfolio board](requirements/features/025-repositoryPortfolioBoard.md) — local cross-repository status and attention signals.

## Planned order

1. Housekeeping — done: removed duplicate
   `documentation/omp-agent-portability-design-proposal(1).md`; captured
   requirements 013 and 014.
2. Requirement 014 test environment — done.
3. Requirement 004 evidence and close-out — done.
4. Patch-removal refactor — done.
5. Requirement 013 — done.
6. Requirement 012 downstream verification in `mailAgent` — done.
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

- Run the full release validation for every 0.9 change.

## Immediate next action

Continue with requirement 002, then the release checks.
