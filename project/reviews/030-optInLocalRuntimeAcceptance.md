# Requirement 030 acceptance evidence

## Scope

Implemented [030](../requirements/features/030-optInLocalRuntime.md) under
[ADR-006](../adr/006-optInLocalRuntime.md) on `feature/030-opt-in-runtime`,
version `0.10a4`. Existing 029 closeout and 030 capture were committed as
`37139ca`; the branch version was reserved in `3328bc2`.

## Acceptance criteria

| Criterion | Evidence |
| --- | --- |
| 1: Default absence and valid scaffolds | `testDefaultCreateOmitsRuntime`, `testCreateModeControlsImportsPackagingAndSavedChoice` |
| 2: Persist enablement | `testPublicCreateRuntimeFlagPersistsThroughUpdate`, `testPublicLocalSyncAndUpdateRespectSavedPreference` |
| 3: Disable, remove and stay disabled | `testPersistEnableDisableReenableAndRepeat`, public local sync/update test |
| 4: Legacy unconfigured cleanup | `testUnconfiguredLegacyCopiesAreRemoved`, current and historical provenance |
| 5: Dry-run preservation | `testDryRunDoesNotChangeAnything`, CLI runtime dry run and existing scaffold dry-run tests |
| 6: Ownership, backups and symlinks | `testUnknownContentAndLinksArePreserved`, `testConfigAndBackupSymlinksBlockBeforeCleanup`, `testFailedBackupDoesNotRemoveAnyHelper`, remote backup-parent protections |
| 7: Whole-operation migration blockers | `testReferencesBlockWholeUpdateAndKeepPreference`, `testSourceSymlinkBlocksRemoval`, `testRemoteDisableBlocksUnmigratedCode` |
| 8: Installed distributions in both modes | `testDefaultWheelRunsWithDeclaredInstalledToolkit`, `testIndependentApplicationAndWheel`; generated imports/packaging and UI package lists also checked |
| 9: Repeatability, validation and roles | persisted transition test; invalid/duplicate/flow settings; conflicting CLI flags; role exclusions; existing 029 regression tests |
| 10: Local and remote contract | local public command tests; remote forwarding, no-flag isolation, preference/tree atomicity, cleanup/backups and blocker-before-instruction tests |

## Verification

2026-11-22, existing `ompr` Conda environment, with existing `wow` tools on PATH:

- Full `python -m pytest -q -rs`: **730 passed, no skips**.
- `ruff check .`: passed.
- Black formatting: all 75 Python files checked/formatted.
- `python -m organiseMyProjects.runLinter .`: 75 files passed.
- `python -m organiseMyProjects.runLinter --markup`: passed.
- `python -m organiseMyProjects.agentCheck`: zero failures, zero warnings.
- `git diff --check`: passed.
- `python -m build --sdist --wheel --no-isolation --outdir /tmp/ompr030-dist`:
  both `0.10a4` distributions built successfully.

Installed missing `setuptools` and `wheel` into the development environment so
the previously skipped distribution evidence now runs. Local runtime sync now
uses the supported shared reconciliation path, also resolving the previously
failing `sync --runtime --project` regression from 029 closeout.

## Review and limits

Cleanup validates the entire reference/ownership plan before touching runtime
files or preferences. Recovery copies of all selected files are made before
unlinking any helper. Unknown content and links are preserved. Remote runtime
preferences, files, backups and deletions use one Git tree commit; failed runtime
validation prevents subsequent instruction writes and automatic merge.

Source and deployment scanning is conservative, not an interpreter for arbitrary
dynamic references or custom file formats. Owners migrate application imports
and packaging themselves. Unowned leftovers and caches can leave an `ompr/`
directory requiring manual review. No live consumer repository was changed;
remote verification uses immutable synthetic GitHub snapshots and API substitutes.

## Suite impact

OMPR changes its create/update defaults and adds saved runtime preferences.
OMS, OMV and OMP are not modified automatically. Their existing managed copies
remain until a maintainer applies an update; a project with no saved choice
must explicitly enable runtime or migrate before cleanup can proceed. WoW
addon role behaviour stays separate and its regression suite passes.
