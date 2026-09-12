# Current Development Increment

## Increment

0.7 — Linter source discovery and naming refinements

## Status

InReview

## Requirement

- `project/requirements/features/005-runLinterSourceDiscovery.md`
- `project/requirements/features/006-guiNamingMethodAndConstantRules.md`

## Objective

Make `runLinter` find Python packages in root-package repositories, and allow
class methods and private constants to follow the 0.7 naming rules.

## Scope

- Discover default lint targets from packaging metadata, a root-level package
  matching the repository name, and auxiliary `src/`, `ui/`, `qt/` and `tests/`
  directories.
- Keep explicit CLI targets unchanged.
- Allow action-only class method names while keeping module-level
  `domainAction`.
- Allow `_UPPER_CASE` private constants.

## Verification

- [x] Discovery unit tests for src, root package, pyproject, tests, missing
      configured paths, duplicates, fallback and explicit targets
- [x] Class method action-only and module-level domainAction tests
- [x] Private constant tests
- [x] Full test suite
- [x] Black and Ruff

## Next

Review the `release/0.7` diff and run release-branch CI.
