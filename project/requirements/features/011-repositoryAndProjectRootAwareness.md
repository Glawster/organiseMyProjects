# 011: Repository and project root awareness

## Status

Completed

## Outcome

As a user running `manageProject check` from a project contained inside a larger Git repository, I need OMP to distinguish the Git repository root from the selected project root so that repository-level checks are evaluated in the correct location and do not produce false positives.

## Context

OMP currently assumes that the directory being checked is also the Git repository root. That assumption is not valid for repositories that contain one or more independently managed projects in subdirectories.

A concrete example is the `linuxMigration` repository, where `mailAgent` is a project below the repository root:

```text
linuxMigration/                 <- Git repository root
├── AGENTS.md
├── .github/
│   ├── copilot-instructions.md
│   └── additional-instructions.md
└── mailAgent/                  <- project root
    ├── pyproject.toml
    ├── src/
    └── tests/
```

When `manageProject check` is run with `mailAgent` as the project root, OMP currently looks for repository-owned files inside `mailAgent` and can incorrectly report:

- `ENT-001` — `AGENTS.md is missing`
- `ENT-002` — `.github/copilot-instructions.md is missing`
- `ENT-003` — `.github/additional-instructions.md is missing`

Those files belong at the actual Git repository root, not inside the nested project directory.

OMP therefore needs two distinct concepts:

- **repository root** — the root of the containing Git work tree;
- **project root** — the project selected for `manageProject check`, which may be the repository root or a descendant of it.

## Scope

- Resolve the Git repository root independently of the project root when running `manageProject check`.
- When the selected project is inside a Git work tree, determine the repository root using Git-aware discovery, equivalent to `git rev-parse --show-toplevel`.
- Continue to treat the explicit/default `manageProject check` target as the project root.
- Classify checks by ownership/scope so repository-level checks are evaluated relative to the repository root and project-level checks are evaluated relative to the project root.
- At minimum, treat the following as repository-level checks:
  - `ENT-001` — `AGENTS.md`;
  - `ENT-002` — `.github/copilot-instructions.md`;
  - `ENT-003` — `.github/additional-instructions.md`.
- Do not require or suggest duplicate repository-level files inside a nested project merely to satisfy `manageProject check`.
- If the project root and repository root differ, make that distinction visible in check diagnostics or verbose output so the user can understand where each class of file is being resolved.
- Preserve existing behaviour when the project root is also the Git repository root.
- Define deterministic behaviour when no containing Git repository can be resolved; the check must not crash and should fall back to the project root for repository-scoped checks unless a more explicit non-Git policy is adopted.
- Add regression coverage for nested-project repositories, using the `linuxMigration/mailAgent` layout as the representative scenario.

## Out of scope

- Moving repository-owned files into project subdirectories.
- Requiring every project in a monorepo or multi-project repository to have its own `.github` directory or `AGENTS.md`.
- Changing the ownership or content rules for the repository-level files themselves.
- Automatically restructuring existing repositories.

## Acceptance criteria

1. Given a project directory that is also the Git repository root, when `manageProject check` runs, then existing repository-level checks behave exactly as before.
2. Given a nested project such as `linuxMigration/mailAgent`, and valid `AGENTS.md`, `.github/copilot-instructions.md`, and `.github/additional-instructions.md` at `linuxMigration/`, when `manageProject check` runs against `mailAgent`, then `ENT-001`, `ENT-002`, and `ENT-003` do not report missing-file findings.
3. Given the same nested project, when one of those repository-level files is genuinely missing from the Git repository root, then the corresponding `ENT-*` finding is reported against the repository-root path rather than the nested project path.
4. Given a nested project, when project-scoped validation is performed, then project files such as package, test, requirement, or project-management content continue to be resolved from the selected project root rather than from the repository root.
5. Given a nested project whose repository-level files already exist at the Git root, when `manageProject check` runs, then OMP does not instruct the user to create duplicate copies inside the nested project.
6. Given a nested project, when verbose/root diagnostic output is requested or roots differ, then OMP can identify both the project root and repository root clearly enough to diagnose path-scoping issues.
7. Given a directory outside a Git work tree, when `manageProject check` runs, then it completes deterministically without a Git-root discovery exception and applies the documented fallback behaviour.
8. Regression tests cover both a single-root repository and a repository containing a nested project, including the `ENT-001`, `ENT-002`, and `ENT-003` cases.

## Dependencies and decisions

- Repository-root discovery should use Git work-tree semantics rather than walking upward merely looking for individual OMP files.
- This requirement introduces an explicit distinction between repository-owned and project-owned checks; future check rules should declare which root they use rather than assuming all paths share one root.

## Verification

- `pytest`
- focused `agentCheck`/`manageProject check` tests for nested projects
- `manageProject check` from a repository-root project
- `manageProject check --project <nested-project>` or equivalent nested-project invocation
- `git diff --check`

## Change history

- 2026-10-13: created after `manageProject check` treated `mailAgent`, a nested project inside the `linuxMigration` Git repository, as the repository root and produced false-positive `ENT-001`, `ENT-002`, and `ENT-003` findings.
