# Requirements

Next available number: 005

## Requirement index

| Req ID | Requirement | Description | Status | Agent Prompt | Architecture Decisions |
| --- | --- | --- | --- | --- | --- |
| 001 | [Project-role-aware updates](features/001-projectRoleAwareUpdates.md) | Safely update established projects without taking ownership of project-specific files. | Completed | [Prompt](prompt/001-projectRoleAwareUpdates.md) | [ADR-001](../adr/001-fileOwnershipPolicies.md) |
| 002 | [Runtime Infrastructure Synchronisation](features/002-runtimeInfrastructureSync.md) | Share reusable runtime infrastructure without a second package in this repository. | ToDo | [Prompt](prompt/002-runtimeInfrastructureSync.md) | [ADR-002](../adr/002-ompRuntimePackage.md) |
| 003 | [OMP 0.6 managed migration and project scaffold](features/003-omp06ManagedMigrationAndScaffold.md) | Safely relocate OMP-managed files and make new projects use a root-level project Python package instead of `src/`. | Completed | [Prompt](prompt/003-omp06ManagedMigrationAndScaffold.md) | [ADR-003](../adr/003-rootPackageScaffold.md) |
| 004 | [Requirement, prompt and folder-index layout](features/004-requirementDocumentationLayout.md) | Reserve `README.md` for repository root, use `folderIndex.md` for directory indexes, keep requirements/prompts as flat numbered files, and safely clean legacy generated layouts. | InProgress | [Prompt](prompt/004-requirementDocumentationLayout.md) | Pending |
