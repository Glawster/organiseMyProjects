# Current Development Increment

## Increment

0.9 — Acceptance follow-up and next release planning

## Status

Planning — carry forward unfinished acceptance work from 0.8.

## Objective

Complete outstanding cross-repository adoption and acceptance review, then
agree the next release scope before starting additional implementation.

## Requirements

- [012: Shared TUI button presentation](requirements/features/012-sharedTuiButtonPresentation.md) — InProgress; verify downstream `mailAgent` adoption and remove execution-screen-specific button height/border overrides.
- [004: Requirement, prompt and directory-index layout](requirements/features/004-requirementDocumentationLayout.md) — InProgress; review existing implementation and regression evidence against all acceptance criteria.
- [002: Runtime infrastructure synchronisation](requirements/features/002-runtimeInfrastructureSync.md) — ToDo; resolve the copied `omp` runtime proposal against the canonical `organiseMyProjects` package and superseded ADR-002 before implementation.

## Verification still required

- Render the adopted shared buttons in the downstream `mailAgent` checkout.
- Review requirement 004 acceptance evidence and align lifecycle metadata only
  when every criterion is satisfied.
- Run the affected production-path tests and release checks for any 0.9 change.

## Immediate next action

Obtain the downstream `mailAgent` checkout and verify requirement 012 acceptance
criterion 6. Keep requirement 012 InProgress until that evidence exists.
