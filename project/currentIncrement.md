# Current Development Increment

## Increment

0.10 — Requirement 030: Opt-in local runtime

## Status

Completed — requirement 030. Release 0.10 still has outstanding backlog.

## Objective

Deliver [030](requirements/features/030-optInLocalRuntime.md) using
[ADR-006](adr/006-optInLocalRuntime.md): default runtime deployment to off,
persist explicit project choices and safely remove managed copies when disabled.

## Implementation

- Branch: `feature/030-opt-in-runtime`, version `0.10a5`.
- Shared preference resolution and recoverable cleanup for create/update/local
  runtime sync; matching atomic remote runtime preference and cleanup updates.
- Mode-appropriate generated imports, dependencies and package resources.
- Focused tests cover saved choices, legacy copies, backups, blockers, symlinks
  and dry runs; distribution evidence covers both application modes.

## Verification

- Full regression after 024 review: 734 passed, no skips, including installed application wheels
  in both modes and real Lua compilation for the addon regression suite.
- Ruff, Black, source/markup lint and agent readiness passed; both toolkit
  distribution formats built successfully.
- [Acceptance review](reviews/030-optInLocalRuntimeAcceptance.md) maps all ten
  criteria and records migration limits and suite impact.
- The earlier runtime-sync CLI failure and packaging dependency skip recorded
  during 029 closeout are resolved in this branch.
- Requirement 002 is reviewed and complete: all eleven criteria mapped in its
  [closeout review](reviews/002-runtimeInfrastructureCloseout.md), with 124
  focused and 730 full-suite tests passing without skips. Existing-consumer
  migration guidance now explicitly requires an isolated installation check
  before removing the toolkit production dependency.
- Requirement 024 is reviewed and complete: 44 board tests passed without skips,
  including real Git/CLI/Textual parity and unreadable version handling. See its
  [closeout review](reviews/024-myBoardBranchVersionsCloseout.md).
- Requirements 002 and 024 are listed in the `0.10a5` release notes and included
  in the current release PR.

## Remaining backlog

- [025](requirements/features/025-repositoryPortfolioBoard.md): portfolio board.
- [027](requirements/features/027-listEditingInteractionStandard.md): list editing.
- Requirement 029 is complete; evidence is in its
  [closeout review](reviews/029-wowAddonCloseout.md).
