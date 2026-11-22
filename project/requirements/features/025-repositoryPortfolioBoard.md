# 025: myProjects repository portfolio

## Status

ToDo

## Outcome

As a developer maintaining many repositories, I need a `myProjects`
portfolio dashboard above `myBoard`, so that I can see which projects need
attention and navigate directly into a project's requirements and working
environment.

## Context

`myBoard` presents the Backlog, ToDo, InProgress and Completed requirements
of one project. The portfolio should aggregate repository-level status, not
merge all requirements into one giant Kanban board. The command must work
the same whether launched from `~`, `~/Source` or any other directory.

This feature is planned for OMPR **0.11**, after the 0.10 close-out of
REQ-002 and REQ-024. It is a key milestone on the path to 1.0.

## Scope

- Provide an installed `myProjects` CLI and optional Textual TUI.
- Use the authenticated GitHub account's accessible repositories as the
  authoritative inventory, including remote-only repositories. Match local
  repositories and additional worktrees read-only beneath `~/Source`,
  `~/bin` and `~/Documents` using normalised Git remote identity.
- The working directory never becomes an implicit discovery root; support
  explicit `--root` overrides and document configuration for additional
  discovery roots.
- When GitHub is unavailable, show a clearly labelled partial local
  inventory rather than falsely reporting zero repositories.
- Show name, owner/repo, local path(s), current branch, version, clean/dirty,
  ahead/behind relative to `main` and release branch, unmerged branches,
  and last known activity.
- For OMP-managed repositories, reuse the `myBoard` requirements parser to
  show Backlog, ToDo, InProgress and Completed counts, increment information
  and record/index drift. For others, display `not managed` instead of failure.
- Surface independently attributable attention flags for dirty worktrees,
  branch/version drift, incomplete requirements, failed/stale/unavailable
  validation, ambiguous remotes and missing Git metadata. Do not infer test
  success from a clean working tree.
- Supply a scriptable `list`, `list --json`, `show NAME`, an attention
  filter, and a deterministic refresh operation before/alongside the TUI.
- Textual dashboard: concise repository table, search/filter/sort, summary
  counts, selected-repository detail panel, and accessible keyboard controls.
  Enter opens detail; `b` opens `myBoard` with an explicit project path;
  `v` opens the selected directory in VS Code after user action; `g`
  refreshes; `q` quits or returns; `/` starts search.
- Support multiple local worktrees as distinct checkouts associated with one
  GitHub repository, with an explicit selection for project launch.
- Default operations are read-only and do not run validation or external
  processes across all repositories. Opening external tools is user initiated.
- Deliver in stages: (1) discovery and CLI/JSON, (2) Textual portfolio and
  navigation, (3) editor/worktree integration and validation snapshots.

## Out of scope

- Automatic clone, fetch, checkout, commit, branch changes, merge or push.
- Running tests, lint or CI automatically across every project.
- Pull-request, issue, review or workflow data beyond repository inventory.
- Turning the portfolio into a board of every requirement across every repo.
- Assigning a lifecycle label from Git state alone; lifecycle classification
  may be separately configured in a future increment.

## Acceptance criteria

1. Running `myProjects` from `~`, `~/Source` or a nested directory
   produces the same default repository inventory.
2. Every accessible GitHub repository appears once; remote-only entries
   are marked `not cloned`.
3. Local discovery matches SSH and HTTPS GitHub remotes and handles linked
   Git worktrees without duplicates or traversal into `.git`.
4. Missing network/authentication yields a clearly partial local view;
   unreadable remotes/files do not prevent other rows loading.
5. Each local checkout displays branch, reported version, dirty state,
   ahead/behind values where available, and unknowns when unavailable.
6. Unmerged branch names and versions are reused from the verified read-only
   myBoard Git context where applicable, with no checkout/fetch.
7. For OMP-managed projects the four requirement counts and drift match
   `myBoard`; unmanaged repositories remain visible.
8. Attention flags preserve distinct causes rather than forcing one
   mutually exclusive project status or fabricating verification results.
9. `list --json` emits the same data and flags as the text view with
   stable, documented keys and no logging noise on stdout.
10. The Textual screen provides keyboard search, filters, detail navigation
    and refresh, and remains usable for dozens of repositories.
11. Opening `myBoard` passes the selected project root explicitly;
    opening VS Code/worktrees requires a direct user action.
12. Scan and refresh never change repository files, refs or remotes,
    and never automatically run an expensive test suite.
13. Tests cover clean/dirty/divergent/unavailable/local-only/remote-only
    cases, multiple worktrees, both launch directories, JSON equivalence,
    and TUI navigation.
14. The developer guide describes the command, inventory scope, attention
    flags, security boundaries and navigation.

## Dependencies and decisions

- Builds on REQ-021 (`myBoard`), REQ-024 (branch/version context) and
  [ADR-004](../../adr/004-githubPortfolioDiscovery.md).
- Planned for 0.11 after 0.10 closes; no dependency on REQ-002 runtime code
  beyond normal OMPR installation.
- Keep `myProjects` as the app name, separate from `myBoard` and from
  the `ompr` runtime package name.

## Verification

- Isolated Git repository/worktree fixtures, GitHub inventory fakes and
  no-write checks.
- Integration tests for text/JSON and launch-path independence.
- Textual key/navigation tests using its pilot.
- Full OMPR suite, runLinter, Black and package entry-point verification.

## Change history

- 2026-10-25: created — repository status above the per-project board.
- 2026-10-25: adopted authenticated GitHub inventory and bounded local roots.
- 2026-11-06: refined into the `myProjects` CLI/Textual design for 0.11
  and identified the planned transition toward 1.0.
