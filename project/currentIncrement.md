# Current Development Increment

## Increment

0.8 — Existing project scaffold consistency

## Status

InReview

## Requirement

`project/requirements/features/008-existingProjectScaffoldConsistency.md`

## Objective

Complete required OMP context when onboarding an existing repository with update,
without overwriting project-owned content.

## Scope

- Missing-only README, project-specific instructions and idle increment scaffold.
- Language-neutral onboarding documentation and explicit author responsibility
  for actual setup and test commands.
- Regression coverage for fresh and partial repositories, preservation and dry-run.

## Verification

- [x] Nine scaffold regression cases pass.
- [x] Full suite: 356 passed; eight runLinter failures reproduce on untouched HEAD.
- [x] Changed Python files pass Black and Ruff; manageProject passes OMP linter.
- [x] Source distribution and wheel build successfully.

## Next

Review the scaffold changes. Resolve the pre-existing runLinter test failures
before release validation can pass in full.
