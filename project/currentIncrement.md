# Current Development Increment

## Increment

0.8 — Scaffold consistency and log section separators

## Status

InReview

## Requirement

`project/requirements/features/008-existingProjectScaffoldConsistency.md`

`project/requirements/features/009-logSectionLinting.md`

## Objective

Complete required OMP context when onboarding an existing repository with update,
without overwriting project-owned content.

## Scope

- Missing-only README, project-specific instructions and idle increment scaffold.
- Language-neutral onboarding documentation and explicit author responsibility
  for actual setup and test commands.
- Regression coverage for fresh and partial repositories, preservation and dry-run.
- Shared 80-character separator convention after headers and before summaries,
  documented in scaffold guidance and applied to linter headers.
- Linter API naming compatibility and console/log-file output-order coverage.
- Python and Bash runStart/line helpers write plain run boundaries and section
  separators to stdout and the application log without logging machinery.
- Entry points and generated applications emit one run marker before the header.

- Enforce LOG-SEC-001/002/003 in conventional Python logger entry points, with
  regression coverage for misplaced calls, summary counts and conditional endings.

## Verification

- [x] Nine scaffold regression cases pass.
- [x] Full suite: 388 passed, including updated tests for current linter routing.
- [x] Changed Python files pass Black and Ruff; manageProject passes OMP linter.
- [x] Source distribution and wheel build successfully.

## Next

Review the scaffold and separator changes before release validation.
