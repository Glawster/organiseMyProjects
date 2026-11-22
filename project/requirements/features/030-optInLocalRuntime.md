# 030: Opt-in local runtime

## Status

Completed

## Outcome

As a project maintainer, I need local OMPR runtime copies only in projects
that explicitly need them, so ordinary scaffolds do not contain an `ompr/`
folder and disabling deployment removes obsolete managed copies.

## Context

Create and ordinary update currently deploy `ompr/` automatically under
requirement 002 and ADR-005. The user requested an option to enable this
behaviour, with absence as the normal state and removal when no longer needed.
Existing generated imports and packaging also assume the folder exists, so
changing deployment alone would leave broken applications.

## Scope

- Make local runtime deployment disabled by default for projects without an
  explicit saved choice, including existing projects with legacy managed copies.
- Provide `--runtime` and `--no-runtime` on create/update and persist the choice
  in project-owned configuration. Propose `localRuntime` in `project/project.yaml`;
  finalise the configuration location and precedence in an ADR before delivery.
- With neither flag, use the saved choice, falling back to false. Reject
  conflicting flags and invalid setting values with actionable messages.
- Enable installs missing helpers and refreshes existing managed helpers through
  the shared manifest. Disable reconciles the project to having no managed copy.
- Generate imports, packaging, dependencies and usage documentation appropriate
  to the selected mode. Without a local runtime, use installed canonical helpers
  where required and declare the corresponding dependency explicitly.
- Remove only positively identified OMPR-managed runtime files. Preserve
  unowned files, ambiguous ownership and symlinks, reporting remaining content;
  remove the directory only when empty. Cover recognised historical ownership
  markers and recoverable handling of locally modified managed files.
- Check existing imports, shell source paths and packaging before cleanup.
  Correct only recognised tool-owned content; report project-owned migration
  work. If unresolved references would break the application, block cleanup
  with an actionable report rather than report successful disablement.
- Preserve dry-run/`--confirm` behaviour, repeatability and project-role rules.
- Keep remote sync's existing explicit runtime opt-in consistent with the saved
  choice, so instruction-only sync cannot recreate a disabled runtime. Specify
  explicit enable/disable and persistence semantics for remote sync in the ADR.

## Out of scope

- Removing the installed organiseMyProjects development toolkit.
- Removing arbitrary user-owned packages or changing organiseMyPhotos `omp/`.
- Inferring deployment preference solely from the presence of an `ompr/` folder.
- Automatically rewriting arbitrary application code or deployment manifests.
- Applying changes to other repositories during implementation verification.

## Acceptance criteria

1. Default create produces no `ompr/` folder, no imports of a missing local
   runtime and no packaging entries requiring that folder.
2. Create/update with `--runtime --confirm` saves an enabled choice and deploys
   the manifest. A subsequent update without either flag retains that choice.
3. Update with `--no-runtime --confirm` saves a disabled choice and removes
   recognised managed runtime files when application migration is satisfied.
   Subsequent updates do not recreate them.
4. An existing project without a saved choice defaults to disabled and plans
   cleanup of recognised legacy copies, subject to the same migration checks.
5. A dry run reports the effective choice, configuration changes, deployments,
   cleanup and blockers without modifying configuration or filesystem content.
6. Unowned or ambiguous content and symlinks are preserved. Modified managed
   helpers are backed up or otherwise recoverable before removal. Remaining
   content and blocked cleanup are reported explicitly.
7. Known unresolved application references block unsafe cleanup with file-level
   migration guidance; a blocked operation does not save a successful disabled
   state or partially remove the managed runtime.
8. Generated application entry points run and built distributions install in
   clean environments in both modes with their declared dependencies.
9. Repeated reconciliation is idempotent. Conflicting flags or invalid settings
   fail before mutation. Existing role exclusions, including WoW addons and
   the canonical OMPR repository, remain effective.
10. Local create/update and remote runtime sync have documented, tested option
    precedence and persistence; instruction-only sync never installs runtime.

## Dependencies and decisions

- [Requirement 002](002-runtimeInfrastructureSync.md): reuse its canonical
  sources, deployment manifest and ownership protections.
- [ADR-005](../../adr/005-deployedOmprRuntime.md): a new ADR must revise its
  unconditional local deployment decision while retaining explicit opt-in use.
- [Requirement 001](001-projectRoleAwareUpdates.md): preserve ownership rules.
- [ADR-006](../../adr/006-optInLocalRuntime.md): accepted preference, precedence,
  cleanup and remote sync contract.
- Proposed CLI and configuration spellings above are the implementation design
  to refine; explicit opt-in, default absence and safe removal are the outcomes.

## Verification

- Exercise default, enabled and disabled create/update; saved and missing
  preferences; conflicting flags; invalid settings; and dry runs.
- Verify enable/disable/re-enable transitions, repeat runs, both historical and
  current markers, modified helpers, unowned content, symlinks and blockers.
- Exercise generated UI entry points and built/installed distributions in both
  modes, including Python logging and shell helper availability where used.
- Verify remote option precedence without live repository mutations.
- Follow `documentation/testingProcess.md` for implementation checks; map each
  acceptance criterion to evidence and update user-facing CLI/runtime guidance.

## Change history

- 2026-11-22: created from the user's request to make local runtime deployment
  opt-in and remove copies when no longer needed.
- 2026-11-22: implemented and verified; 730 tests passed with no skips. See
  [acceptance evidence](../../reviews/030-optInLocalRuntimeAcceptance.md).
