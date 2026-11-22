# Current Development Increment

## Increment

0.10 — Release closeout

## Status

Completed — delivered 0.10 scope. Publication is tracked by the release PR
and final Git tag.

## Outcome

Final version `0.10` includes the reviewed runtime infrastructure (002), board
branch/version reporting (024), WoW addon project role (029) and opt-in local
runtime (030), plus the earlier 0.10 board, style and account-availability work.
See [release notes](../documentation/releaseNotes.md).

## Acceptance evidence

- [002 runtime infrastructure review](reviews/002-runtimeInfrastructureCloseout.md).
- [024 branch versions review](reviews/024-myBoardBranchVersionsCloseout.md).
- [029 addon role review](reviews/029-wowAddonCloseout.md).
- [030 optional runtime review](reviews/030-optInLocalRuntimeAcceptance.md).

## Release verification

Final version `0.10` passed all 734 tests without skips in the `ompr`
environment with `wow` Lua tools available. Source/markup lint, Ruff, Black,
readiness and distribution builds passed. Source, package metadata and CLI
report the same final version. See the
[release closeout review](reviews/release010Closeout.md).

## Next-release backlog

- [025](requirements/features/025-repositoryPortfolioBoard.md): repository
  portfolio, already planned for 0.11.
- [027](requirements/features/027-listEditingInteractionStandard.md): list editing
  standard, carried forward to 0.11. It remains ToDo and is not delivered in 0.10.
- Other ToDo requirements remain in the requirements index; closing 0.10 does
  not mark them completed.
