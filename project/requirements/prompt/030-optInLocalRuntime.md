# 030: Opt-in local runtime

## Assignment

Implement and verify [requirement 030](../features/030-optInLocalRuntime.md).
Cover all acceptance criteria. Record the option/configuration contract and
revision to ADR-005 in a linked ADR before implementing behaviour changes.

## Boundaries

Inspect `manageProject.py`, `runtimeDeployment.py`, historical `runtimeSync.py`,
remote instruction/runtime sync, project configuration handling, generated UI
templates, packaging and their tests. Reuse the shared runtime manifest and
centralise preference resolution and reconciliation. Preserve project-owned
application code, unrelated configuration, user files and symlinks. Do not
perform live remote writes or remove runtime copies from consumer repositories.

Read the repository instructions, requirements workflow, repository layout and
testing process before implementation. Keep transient delivery state in
`project/currentIncrement.md` and update requirement/index lifecycle together.

## Evidence

Map every acceptance criterion to focused tests or explicit review evidence.
Demonstrate default absence, persisted enablement, safe disablement, migration
blockers, dry-run behaviour, repeatability and clean application installations
in both modes. Update CLI help, scaffold guidance and runtime documentation.
Report verification results and any remaining limitations without marking
unverified criteria complete.
