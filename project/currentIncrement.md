# Current Development Increment

## Increment

0.10 — Requirement 029: WoW addon project role

## Status

Completed — requirement 029. Release 0.10 still has outstanding work.

## Objective

Deliver [029](requirements/features/029-wowAddonProjectRole.md): add and
integrate the `wow-addon` project role so `manageProject` can scaffold and
maintain WoW addon repositories with addon-specific managed files, while
preserving non-addon project behaviours.

## Implementation

- Add addon role detection and dedicated create/update paths in
  `manageProject`.
- Scaffold addon-specific files and configuration, including flavour-aware
  `.toc` handling and addon lint/format setup.
- Keep addon projects free of Python runtime/package scaffolding that applies
  only to standalone Python applications.
- Support addon metadata extraction and migration behaviour for
  `project.yaml`.
- Deploy and sync addon-specific documentation and agent guidance.

## Acceptance evidence

- Added WoW addon implementation and tests from the `feature/wow-addon`
  stream.
- Added requirement and prompt records for requirement 029.
- Added release-notes and repository-layout coverage for addon role usage.
- All ten acceptance criteria reviewed in the
  [closeout review](reviews/029-wowAddonCloseout.md).

## Verification

- 189 focused addon, scaffold, sync and agent-readiness tests passed, no skips;
  real Lua compilation used the existing `wow` environment.
- Ruff, full Black, source lint, markup lint and agent readiness passed.
- Full regression: 684 passed, one failed, one skipped. Existing runtime-sync
  CLI test expects unsupported `sync --project`; reproduced on the unchanged
  committed implementation. Distribution evidence skipped for unavailable
  `setuptools`. Resolve these runtime verification items before release.

## Remaining 0.10 backlog

- [024](requirements/features/024-myBoardBranchVersions.md): verify existing
  implementation against branch/version acceptance criteria.
- [025](requirements/features/025-repositoryPortfolioBoard.md): repository
  portfolio board.
- [027](requirements/features/027-listEditingInteractionStandard.md): list
  editing interaction standard and enforcement.
- [030](requirements/features/030-optInLocalRuntime.md): opt-in local runtime;
  captured as ToDo and not started.
