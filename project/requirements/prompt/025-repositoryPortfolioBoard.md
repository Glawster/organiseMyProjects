# 025: Refine repository portfolio board

## Assignment

Implement [requirement 025](../features/025-repositoryPortfolioBoard.md) after
reviewing [ADR-004](../../adr/004-githubPortfolioDiscovery.md). The requirement
is authoritative for outcome, scope and acceptance criteria.

## Boundaries

Use the authenticated GitHub account's accessible repositories as the inventory.
Scan only `~/Source`, `~/bin` and `~/Documents` read-only for matching Git
remotes. Do not clone, fetch, write to scanned repositories, or request
pull-request, issue, review or workflow data.

## Verification and handoff

Run isolated discovery tests with temporary Git repositories, an integration
test for GitHub-only and locally matched repositories, and prove the scan
changes no repository files or refs. Report inaccessible inventory, unmatched
remotes and unavailable Git metadata clearly.
