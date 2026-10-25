# 024: Implement requirement board branch versions

## Assignment

Implement and verify
[requirement 024](../features/024-myBoardBranchVersions.md). The requirement
is authoritative for scope and acceptance criteria.

## Boundaries

Extend the existing read-only Git context and its focused tests. Do not check
out, modify, merge or delete branches, and do not add a GitHub API dependency.

## Verification and handoff

Run pytest tests/test_myBoard.py, runLinter on the changed module, Black check
and git diff --check. Report the acceptance evidence and any unavailable Git
metadata cases.
