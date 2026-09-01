# Requirement: 003

Source: project/requirements/features/003-omp06ManagedMigrationAndScaffold.md
Role: implement

Read the authoritative requirement and ADR-003 before changing anything.
Deliver every acceptance criterion in requirement 003. Preserve existing
project `src/` layouts during ordinary update. Remove obsolete managed files
only when an OMP deployment or sync marker is present.

Limit changes to create/update behaviour, templates, tests, and documentation
needed to prove the criteria.

Verify with dry-run and confirmed relocation tests, scaffold tree tests for
`footballVision`, package importability, and the full pytest suite.
