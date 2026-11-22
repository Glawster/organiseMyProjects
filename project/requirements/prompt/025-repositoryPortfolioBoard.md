# 025: Implement myProjects repository portfolio

## Assignment

Implement [REQ-025](../features/025-repositoryPortfolioBoard.md) as the
portfolio-level `myProjects` command, following
[ADR-004](../../adr/004-githubPortfolioDiscovery.md) and the existing
`myBoard` conventions. Target OMPR 0.11, not 0.10.

## Architecture

Implement `myProjects.py` (CLI), `projectPortfolio.py` (aggregated model),
small GitHub/local-Git discovery helpers, and a separate Textual screen.
Reuse `requirementBoard` reading/Git-version logic rather than duplicating
parsers. Do not add an unrelated top-level Python package.

## Delivery stages

1. Build authenticated GitHub inventory and bounded read-only local worktree
   matching; add `list`, `list --json`, `show`, root overrides and
   attention filtering. Provide stable error/partial-inventory semantics.
2. Add table-first Textual dashboard with counters, search, filters, detail
   and keyboard navigation.
3. Add explicit `myBoard` and VS Code launch actions, worktree selection
   and cached (never invented) validation snapshots.

## Boundaries

Runs identically from `~` or `~/Source` by default. Don't scan all of
home recursively; inspect the configured roots. No automatic clone/fetch,
mutating Git operations, batch tests, credentials logging or project writes.
GitHub inventory failure must not erase discoverable local projects.
Do not represent unknown validation as passed.

## Verification and handoff

Use isolated temp Git repositories and worktrees, mocked GitHub inventory,
JSON equivalence and read-only snapshots. Exercise the TUI pilot and both
launch directories. Run complete pytest, runLinter, Black, package checks,
and map tests to all fourteen acceptance criteria. Report any partial
inventory or provider limitations transparently.
