# Requirement 024 acceptance review

## Scope and conclusion

Reviewed [024](../requirements/features/024-myBoardBranchVersions.md) on
`feature/030-opt-in-runtime` for version `0.10a5`, including CLI and Textual
presentation. All four acceptance criteria now have direct evidence.

## Findings and corrections

- Unreadable version metadata could raise `UnicodeDecodeError` for either the
  current working file or committed metadata read through Git. `_branchVersion`
  now reports an unavailable version in both cases, preserving the branch row.
- Branch enumeration included remotes other than `origin`. Restricted its Git
  ref query to local branches and `refs/remotes/origin`, matching the requirement.
- Added real-repository coverage for deduplication, current-first ordering,
  absent metadata, invalid text and read-only discovery. Added a real Textual
  integration test comparing its rendered branch rows with the CLI summary.

## Acceptance evidence

| Criterion | Evidence |
| --- | --- |
| 1: Every unmerged local/remote-only origin branch shown once | `testOpenBranchVersionsAreCompleteUniqueAndReadOnly` creates real refs, verifies local/remote duplicate suppression, includes a remote-only branch and excludes merged `main` and an unrelated remote. |
| 2: Current branch first | The same test names the current branch `z-current` and another local branch `a-other`, verifying current-first ordering independently of alphabetical ref order. Existing `testGitLinksTheRequirementId` also verifies working-copy version metadata. |
| 3: Unavailable metadata is safe | The real-ref test includes absent committed metadata; parametrized `testUnreadableBranchVersionDoesNotBreakBoard` exercises invalid text in the current working copy and another branch's committed blob. All render `version unavailable`. |
| 4: CLI/Textual parity | `testCliAndTextualShowSameRealBranchVersions` invokes the real CLI, loads the real Textual board, waits for Git/status workers and verifies identical rendered `Open:` pairs. |

The read-only test compares Git refs, symbolic HEAD and working-tree status
before/after discovery. Neither normal display path checks out, creates,
deletes or merges branches, and no GitHub API lookup was introduced.

## Verification

2026-11-22, existing `ompr` Conda environment with `wow` tools available:

- `python -m pytest tests/test_myBoard.py -q -rs`: **44 passed, no skips**.
- Full `python -m pytest -q -rs`: **734 passed, no skips**.
- Ruff and Black checks: passed.
- Source lint: 75 files passed. Markup lint and whitespace checks: passed.
- Manually inspected `myBoard list` in the actual repository. Independently
  enumerated unmerged Git refs, collapsed local/origin counterparts and read
  version assignments using AST parsing; every expected CLI pair appeared once.

Observed current branch `feature/030-opt-in-runtime` reports `0.10a5`; the
release branch reports `0.10a3`, the remote-only runtime feature reports
`0.10a3`, and the historical backup without metadata safely reports unavailable.

## Release and suite impact

Requirements 024 and 002 are explicitly listed in the `0.10a5` release notes
and marked Completed in the requirements index. Version remains `0.10a5` as
requested; the existing immutable `v0.10a5` tag is not moved. These changes join
PR #87 for integration into `release/0.10`.

OMPR's board remains a read-only local Git view. OMS, OMV and OMP receive no
automatic changes, migrations or remote writes. No acceptance gaps remain for
024; repositories without readable version metadata still display an explicit
unavailable value rather than inventing a version.
