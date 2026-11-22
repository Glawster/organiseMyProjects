# Requirement 002 acceptance review

## Scope and conclusion

Reviewed requirement 002 against ADR-005, the implementation on
`feature/030-opt-in-runtime` at `49f1d41`, and the subsequent opt-in policy in
requirement 030 / ADR-006. All eleven acceptance criteria have evidence for the
opted-in runtime capability. Default absence and preference/cleanup behaviour
remain governed by 030; this review does not restore unconditional deployment.

No runtime implementation defects were found in this review. One documentation
gap was corrected: the guide now explicitly covers migrating existing consumers
to bundled helpers, verifying an isolated installation and only then removing
the production toolkit dependency. No code or tests changed during closeout.

## Criterion evidence

| Criterion | Evidence reviewed |
| --- | --- |
| 1: Approved runtime subset | `runtimeDeployment.RUNTIME_FILES` explicitly selects minimal initializer, Python/Bash logging and source version; opted-in create delegates to that manifest. Wheel contents are checked by `testIndependentApplicationAndWheel`. |
| 2: Imports and packaging | Generated opted-in entry points import `ompr.logUtils`; `testRuntimeCliForwardingAndUiPackaging` checks package lists and shell package data; independent wheel execution checks installed imports. |
| 3: Independence from toolkit | `testIndependentApplicationAndWheel` builds/installs a real consumer wheel, executes from outside the checkout using `-I -S`, rejects all `organiseMyProjects` imports, exercises Python logging and sources the installed Bash resource. |
| 4: Provenance | `testManagedOverwriteModesAndIdempotence` checks release/repository headers on every manifest file; `testRuntimeSyncAtomicTreeAndModes` checks remote headers and shell shebang placement. |
| 5: Shared manifest | Create/update/local sync use `runtimeReconcile` and `runtimeDeploy`; remote repository and batch sync call the same canonical `runtimeFiles`. The historical low-level `runtimeSync` compatibility API is not the public management command's deployment path. |
| 6: Refresh, modes and repeatability | `testManagedOverwriteModesAndIdempotence`, `testManifestExtensionAndExecutableMode`, `testManagedRemoteModificationRefreshesOnlyChangedFile`, and remote idempotence tests. |
| 7: Dry runs | `testDryRunAndCollisionProtection` and `testRuntimeSyncDryRunIdempotenceAndOwnership` verify preserved bytes and no branch, tree, commit or ref writes; preference dry-run tests cover the new local wrapper. |
| 8: Ownership and project preservation | Local/remote unowned-package and symlink tests; `testExistingMigrationReportsWithoutEditing` verifies application code and packaging preservation; canonical-source protections cover both local and remote paths. |
| 9: Migration reporting and guide | `testExistingMigrationReportsWithoutEditing` checks detected legacy imports and packaging warnings; reviewed update wiring invokes reporting when enabled. The guide now explicitly requires clean installed-consumer verification before removing the toolkit runtime dependency. |
| 10: Extension | `testManifestExtensionAndExecutableMode` adds a self-contained executable helper to the selected manifest and exercises real local/remote composition without consumer-specific sync changes. |
| 11: Naming and canonical sources | Reviewed runtime guides, README, repository layout, additional instructions, manifest and minimal initializer; OMPR/`ompr` remains distinct from organiseMyPhotos/OMP. No sibling runtime package is created in the canonical repository. |

## Verification

2026-11-22, existing `ompr` Conda environment with `wow` Lua tools on PATH:

- `python -m pytest tests/test_runtimeDeployment.py tests/test_runtimeSync.py tests/test_runtimePreference.py tests/test_syncAgentInstructions.py -q -rs`:
  **124 passed, no skips**.
- Full `python -m pytest -q -rs`: **730 passed, no skips**.
- `ruff check .`: passed.
- `black --check --workers 1 .`: 75 files passed.
- `python -m organiseMyProjects.runLinter .`: 75 files passed.
- `python -m organiseMyProjects.runLinter --markup`: passed.
- `git diff --check`: passed.

## Limits and suite impact

Remote evidence substitutes HTTP boundaries while retaining real validation,
snapshot handling, tree construction and manifest selection. It establishes
the API payload contract, not a live GitHub deployment; no consumer repository
was modified. An established consumer still needs its own installed-application
acceptance before removing dependencies. Import reporting deliberately covers
bounded source roots and does not claim full dynamic-import discovery.

OMPR owns canonical helpers and the opt-in deployment capability. OMS, OMV and
OMP can adopt it through explicit reviewed updates; this closeout makes no
changes to them. Requirement 030's default-off policy and WoW addon exclusions
remain intact. No unresolved acceptance gap remains for requirement 002.
