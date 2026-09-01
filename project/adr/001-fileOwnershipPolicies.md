# ADR-001: Declared file ownership policies

## Status

Accepted

## Context

`createProject` / `updateProject` deploy many files into established
repositories. Without an explicit per-file rule, updates can overwrite
project-owned configuration or fail to refresh OMP-owned standards.
Requirement 001 requires exactly one policy for every deployed file.

## Decision Drivers

- Preserve project-owned application code, layout and local configuration.
- Keep shared standards current when they actually change.
- Make dry-run output match the policy that would be applied.

## Considered Options

1. Treat all scaffold files as managed overwrite.
2. Treat configuration files as missing-only and never merge later OMP
   standards into them.
3. Declare one of three policies for every deployed path: managed overwrite,
   managed-block merge, or project-owned missing-only.

## Decision Outcome

Chosen option 3.

- **Managed overwrite** applies to OMP-owned guidance, vendor shims, test
  helper copies and the `omp` runtime package. Files are replaced when
  substantive content changes; release-marker-only differences are ignored.
- **Managed-block merge** applies to pytest, pre-commit, editor, environment
  and dependency files. Existing project content is preserved and only the
  marked `OMP-MANAGED-BEGIN` / `OMP-MANAGED-END` block is inserted or updated.
  Missing files may be created from the scaffold.
- **Project-owned missing-only** applies to application entry points, source
  layout, UI/Qt templates and project-management records. Update never infers
  a UI or adds `main.py` / `src/globalVars.py` to a packaged CLI or library.

The mapping lives in `FILE_OWNERSHIP` in `manageProject.py`. Adding a
deployable file without a policy is an error.

### Consequences

- Positive: Established projects can adopt OMP standards without losing local
  pytest, editor or dependency customisation.
- Positive: Role detection plus missing-only application files prevents UI and
  `main.py` from being inferred.
- Negative: Authors must add a policy when introducing a new scaffold file.
- Negative: JSONC managed blocks in `.vscode/settings.json` are not strict JSON.

## Requirements

- [001: Project-role-aware updates](../requirements/features/001-projectRoleAwareUpdates.md)
