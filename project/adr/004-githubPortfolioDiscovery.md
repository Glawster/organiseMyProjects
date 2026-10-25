# ADR-004: GitHub portfolio discovery

## Status

Accepted

## Context

The repository portfolio board needs a stable inventory even when a repository
is not cloned locally. Local filesystem scanning alone cannot distinguish an
uncloned accessible repository from one outside the selected workspace. The
owner specified that GitHub should be the repository source and that local
matching should search `~/Source`, `~/bin` and `~/Documents`.

## Decision Drivers

- Show every repository accessible to the authenticated GitHub account.
- Identify local availability without cloning or changing any repository.
- Avoid scanning unrelated areas of the filesystem.
- Keep remote-only repositories visible and actionable.

## Considered Options

1. Discover repositories only from local filesystem roots.
2. Use GitHub inventory, then find local worktrees by remote URL beneath fixed
   workspace roots.
3. Clone every accessible GitHub repository into a managed workspace.

## Decision Outcome

Chosen option 2.

- The portfolio invokes authenticated GitHub CLI/API repository enumeration for
  all repositories accessible to the signed-in account.
- It scans `~/Source`, `~/bin` and `~/Documents` recursively for Git
  worktrees, without traversing `.git` directories.
- It normalizes each worktree's `origin` remote URL to an owner/name identity
  and matches it to GitHub inventory entries.
- A GitHub repository with no match is displayed as not cloned.
- Inventory, local scan, Git inspection and validation evidence are read-only;
  the portfolio does not clone, fetch, alter refs, or write in scanned
  repositories.
- A missing GitHub authentication, inaccessible repository list, unreadable
  local worktree, absent `origin`, or unrecognized remote is surfaced as an
  attention flag rather than stopping other repositories.

### Consequences

- Positive: The board distinguishes remote-only repositories from local work
  and has bounded, user-chosen filesystem discovery.
- Positive: It does not require a separate registry of repositories or clone
  potentially large/private projects.
- Negative: GitHub CLI authentication and network availability are required
  for complete inventory; local scan results may be partial when roots are
  unavailable.
- Negative: Repositories whose primary remote is not `origin` or whose URL
  cannot be normalized need an attention flag or later configuration support.

## Requirements

- [025: Repository portfolio board](../requirements/features/025-repositoryPortfolioBoard.md)
