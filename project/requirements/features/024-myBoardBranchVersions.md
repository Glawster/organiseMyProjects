# 024: Requirement board branch versions

## Status

InReview

## Outcome

As a developer using myBoard, I need to see each open branch and its OMP
version so that I can identify the current development state without checking
each branch manually.

## Context

myBoard already reports the current branch and its divergence from `main` and
the configured release branch. It does not show other unmerged work or the
version each branch reports.

## Scope

- Discover all local branches and remote-only `origin/*` branches not merged
  into `main`.
- Read each branch's `organiseMyProjects/version.py` without checking it out.
- Show branch/version pairs in the board Git strip and `myBoard list` summary.
- Keep the current branch first and report unavailable version metadata safely.

## Out of scope

- GitHub API pull-request lookup.
- Branch creation, deletion, checkout or merge operations.
- Reading version metadata outside the OMP package path.

## Acceptance criteria

1. Given unmerged local and remote-only branches, when the board Git context
   loads, then every branch is shown once with its version.
2. Given the current branch is unmerged, when branches are shown, then it is
   first in the summary.
3. Given a branch lacks readable OMP version metadata, when it is shown, then
   its version is marked unavailable without failing the board.
4. Given `myBoard list` or the Textual board, when its Git summary is shown,
   then it contains the same branch/version pairs.

## Dependencies and decisions

- Builds on requirement 021's read-only Git context.
- No ADR required.

## Verification

- Code review on 2026-11-06 confirms `gitContextLoad`, `_openBranches`, `_branchNames` and `_branchVersion` provide the specified read-only behaviour.
- Existing `testGitLinksTheRequirementId` exercises local, remote-only and current-branch versions, plus unavailable release metadata and presentation via `gitContextLines`.
- Before closure, rerun `python -m pytest tests/test_myBoard.py`, `runLinter organiseMyProjects/requirementBoard.py`, Black, and `git diff --check` in `ompr`; manually inspect `myBoard list` against current branches.
- Status stays InReview until those checks are independently completed.

## Change history

- 2026-10-25: created — show open branches and versions in myBoard.
- 2026-11-06: reviewed existing implementation and tests; moved to InReview pending final runtime verification.
