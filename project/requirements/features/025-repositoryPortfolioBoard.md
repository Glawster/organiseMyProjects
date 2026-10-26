# 025: Repository portfolio board

## Status

ToDo

## Outcome

As a developer working across my accessible GitHub repositories, I need a
portfolio-level board that shows each repository's actionable status and local
availability so that I can prioritise work without opening every individual
requirement board.

## Context

myBoard shows requirements for one nearest project. Developers also need a
compact view above that level to find GitHub repositories with uncommitted
work, branches needing integration, version drift, incomplete requirements,
stale validation evidence, or no local clone.

## Scope

- Use the authenticated GitHub account's accessible repositories as the
  authoritative inventory.
- Find matching local Git worktrees read-only beneath `~/Source`, `~/bin` and
  `~/Documents`, using normalized `origin` remote URLs without cloning,
  fetching or modifying them.
- Show GitHub repositories without a matching local worktree as not cloned.
- Show each repository's name and path, current branch, reported version,
  dirty state, and ahead/behind counts against `main` and its release branch.
- Show open local and remote-only branch counts, including their version
  spread when it differs from the current branch.
- Summarise requirement counts by Backlog, ToDo, InProgress and Completed for
  repositories that own a requirements index.
- Surface attention flags for dirty work trees, branch/version drift, missing
  `main` or release branches, inconsistent requirement status, failed or
  stale local validation, and unavailable metadata.
- Provide a scriptable text and JSON view before adding an optional Textual
  portfolio interface.

## Out of scope

- Editing, committing, merging, checking out, creating or deleting branches.
- Automatically running expensive tests, linting or CI jobs across every
  repository.
- Pull-request, issue, review or workflow status beyond repository inventory.
- Replacing the per-project myBoard requirement view.

## Acceptance criteria

1. Given an authenticated GitHub account, when the portfolio list runs, then
   every accessible GitHub repository appears once with its owner/name and
   local-clone state.
2. Given a GitHub repository with a matching local worktree under `~/Source`,
   `~/bin` or `~/Documents`, when it is listed, then it shows its local path,
   branch, version and dirty state.
3. Given a GitHub repository without a matching local worktree, when it is
   listed, then it is marked not cloned and the portfolio continues.
4. Given a repository with `main`, a release branch or unmerged work, when its
   status is loaded, then ahead/behind and open-branch information are shown
   without changing that repository.
5. Given a repository owning `project/requirements/requirementsIndex.md`,
   when it is listed, then the four requirement-column counts and any
   record/index status drift are shown.
6. Given missing Git metadata, version data, requirements, or local validation
   evidence, when the board loads, then it reports the unavailable information
   as an attention flag and continues with other repositories.
7. Given `--json`, when the portfolio list runs, then it emits the same
   repository fields and attention flags in machine-readable form.

## Dependencies and decisions

- Depends on requirements 021 and 024 for the per-repository board and
  read-only Git/version context.
- [ADR-004](../../adr/004-githubPortfolioDiscovery.md) defines GitHub inventory,
  local discovery and validation-evidence storage.

## Verification

- Unit tests using temporary Git repositories with clean, dirty, divergent and
  metadata-missing states.
- Integration test covering multiple repositories and JSON output.
- Read-only evidence showing no repository files or refs change after a scan.

## Change history

- 2026-10-25: created — request for status above the repository-level board.
- 2026-10-25: GitHub inventory and local roots refined at user request.
