# Current Development Increment

## Increment

0.10a2 — Release readiness: runtime synchronisation and branch/version reporting

## Status

InProgress

## Objective

Finish and verify REQ-002 and REQ-024 before finalising the 0.10 release.
REQ-028 is completed and its agent-availability implementation already forms
part of this release branch. No 0.10 final release is declared yet.

## Requirements

- [002: Runtime infrastructure synchronisation](requirements/features/002-runtimeInfrastructureSync.md) — InProgress; canonical source and `ompr` deployment naming clarified; ADR-005 Proposed, implementation and tests outstanding.
- [024: Requirement board branch versions](requirements/features/024-myBoardBranchVersions.md) — InReview; implementation and existing tests inspected, final local regression/lint/manual verification outstanding.
- [028: Agent usage availability](requirements/features/028-agentUsage.md) — Completed; implemented and verified previously as documented in the release notes.

## Current work

- Confirm ADR-005 against consuming-project import and packaging requirements,
  then implement REQ-002's manifest-based managed runtime synchronisation.
- Rerun focused tests, runLinter, Black and `myBoard list` for REQ-024; close
  only when the live verification is recorded.
- Once both are complete, run the full release checklist, change
  `organiseMyProjects/version.py` from `0.10a2` to final `0.10`, open a
  release PR to `main`, and tag `v0.10` only after merging.

## Verification and limitations

- REQ-028 historical closure: 627 tests passed with no skips in the `ompr`
  environment on 2026-11-01; this is previous evidence, not a fresh run of
  today's 0.10 branch.
- REQ-024 source review found `_openBranches` and `_branchVersion` plus
  focused Git tests that exercise local and remote-only version display.
  Final checks remain required.
- REQ-002 is not implemented: no downstream runtime packaging, import
  isolation or overwrite-safety tests have yet been demonstrated.
- Grok 1.0.70 did not expose the usage percentage; REQ-028 intentionally
  reports `UNKNOWN`. Claude terminal parsing may become unavailable when
  its provider screen changes.

## Next increment — 0.11

- [025: myProjects repository portfolio](requirements/features/025-repositoryPortfolioBoard.md) — ToDo; detailed 0.11 design and implementation prompt approved for planning.
- Keep 0.11 focused on portfolio CLI, Textual screen and navigation to
  `myBoard`, followed by stabilisation toward OMPR 1.0.
- Do not create a release/0.11 branch or assign 0.11 alpha versions until
  the 0.10 release completes and branch/tag availability is checked.
