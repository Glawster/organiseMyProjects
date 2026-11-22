# ADR-006: Opt-in local runtime

## Status

Accepted — 2026-11-22. Revises ADR-005's unconditional local deployment policy.

## Decision

Store the boolean `localRuntime` at the top level of `project/project.yaml`.
An explicit mutually exclusive `--runtime` or `--no-runtime` overrides the saved
value; omission uses the saved value, defaulting to false. Validate even when
overridden. Preserve unrelated metadata and comments. Confirmed reconciliation
saves the effective choice only after validation; dry runs never save it.

Default scaffolds import canonical `organiseMyProjects` logging helpers and
declare that distribution as a dependency. Opted-in scaffolds import `ompr`
and bundle the manifest and shell resources instead. Existing application
code and packaging remain project-owned: disabling reports file-level migration
blockers rather than rewriting them. No dependency is installed at runtime.

Before any disabled-mode cleanup, validate the whole plan. Recognise current
provenance and historical OMPR-RUNTIME-MANAGED headers. Back up every removed
managed file under `output/omprRuntimeBackups/` before unlinking any copy;
this preserves modified helpers and their modes. Preserve unknown files and
symlinks and report leftovers. Remove only empty runtime directories. Refuse
symlinked configuration or backup paths. Scan source and deployment text while
excluding version-control metadata, environments, caches and output; dynamic
references outside those checks require maintainer review.

Local `sync --project PATH` reconciles the same preference and manifest as
update, without unrelated scaffold changes. Remote sync remains instruction-only
unless an explicit runtime flag is supplied, even for saved-enabled projects.
Remote `--runtime` enables and saves true; `--no-runtime` disables and saves false.
Runtime files, preference, deletions and recoverable backups share one atomic
Git tree commit after validating an immutable snapshot. A blocker prevents the
runtime commit and automatic merge. Addon and canonical OMPR repositories do
not receive local runtime copies.

## Consequences

Ordinary new and legacy projects default to no local runtime. Existing consumers
with local imports must explicitly retain deployment or migrate before cleanup.
Generated files are project-owned; switching modes does not silently rewrite
them. Canonical source ownership and manifest selection from ADR-005 remain.

## References

- [Requirement 030](../requirements/features/030-optInLocalRuntime.md)
- [ADR-005](005-deployedOmprRuntime.md)
