# Current Development Increment

## Increment

0.10 — Requirement 029: WoW addon project role

## Status

InProgress

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

## Acceptance evidence (in progress)

- Added WoW addon implementation and tests from the `feature/wow-addon`
  stream.
- Added requirement and prompt records for requirement 029.
- Added release-notes and repository-layout coverage for addon role usage.

## Verification

- Pending targeted pytest verification for addon role tests and touched
  scaffolding behaviour.

## Remaining 0.10 backlog

- [024](requirements/features/024-myBoardBranchVersions.md): verify existing
  implementation against branch/version acceptance criteria.
- [025](requirements/features/025-repositoryPortfolioBoard.md): repository
  portfolio board.
- [027](requirements/features/027-listEditingInteractionStandard.md): list
  editing interaction standard and enforcement.
