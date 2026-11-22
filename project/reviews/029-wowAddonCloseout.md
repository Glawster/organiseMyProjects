# Requirement 029 acceptance review

## Scope

Reviewed requirement 029 on `release/0.10`, based on integrated implementation
commit `40be75c`. Closeout corrects import ordering and logging message casing
in `manageProject.py`. No new feature behaviour or tests were needed.

## Acceptance evidence

| Criterion | Evidence |
| --- | --- |
| 1: Root addon scaffold | `testCreateWritesAddonAtRepositoryRoot`, `testCliCreateWowAddon` |
| 2: Three flavours | `testTocCarriesStandardFields`, `testFlavourDetect` |
| 3: Quality tooling and environment | `testCreateWritesAddonAtRepositoryRoot`, `testLuacheckDeclaresAddonGlobals`, `testPkgmetaLeavesDevelopmentFilesOut` |
| 4: No Python scaffold | `testCreateAddsNoPythonScaffold`; review of `createWowAddon` and `_wowAddonUpdate` |
| 5: Detect addon updates | `testRoleDetectedFromRootToc`, `testTocInSubfolderIsNotAnAddon`, `testUpdateExistingAddonAddsStandardWithoutPython` |
| 6: Ownership preservation | `testUpdateReplacesOnlyTheManagedPrecommitBlock`, `testUpdateExistingAddonAddsStandardWithoutPython`, `testUpdateIsIdempotent`, `testUpdateDryRunChangesNothing` |
| 7: Addon readiness commands | `testCreatedAddonPassesAgentCheck`, `testAddonTestCommandSatisfiesDocCheck`, `testCreatedAddonReadmeHasTestCommand` |
| 8: Metadata migration | `testMigrateWritesAddonProjectYaml` |
| 9: Managed guide and sync | `TestRoleSpecificSync`; review of addon managed templates and `documentation/wowAddon.md` |
| 10: Automated coverage | Addon, scaffold, readiness and sync suites: 189 passed, no skips |

The StyLua configuration is named `stylua.toml` throughout implementation,
documentation and tests. Corrected criterion 3's `.stylua.toml` spelling to
match that established contract; no tooling behaviour changed.

## Verification

Verification date: 2026-11-22. Python tools use the existing `ompr` Conda
environment; PATH also includes the existing `wow` environment for Lua.

- `python -m pytest tests/test_wowAddon.py tests/test_createProject.py tests/test_syncAgentInstructions.py tests/test_agentCheck.py -q -rs`:
  189 passed, no skips, including generated Lua compilation with real `luac`.
- `ruff check .`: passed.
- `black --check --workers 1 .`: 73 files passed.
- `python -m organiseMyProjects.runLinter .`: 73 files passed.
- `python -m organiseMyProjects.runLinter --markup`: no remaining issues.
- `python -m organiseMyProjects.agentCheck`: zero failures, zero warnings.
- `git diff --check`: passed.
- Full `python -m pytest -q -rs` outside the filesystem/terminal sandbox:
  684 passed, one failed, one skipped. The failing
  `testManageProjectCliRuntimeSync` supplies unsupported `sync --project`;
  reproduced the same failure after loading the unchanged `HEAD` version of
  `manageProject.py`, confirming it predates these closeout changes. The
  distribution evidence test skipped because `setuptools` is unavailable to
  that test environment. Both are requirement 002/runtime verification items,
  not gaps in addon acceptance. The release regression baseline is not green.
- Initial sandboxed runs could not reliably exercise PTY/TUI tests or Black
  workers; the full suite and formatting checks above used approved execution
  outside that sandbox. No dependency-related skips occurred in 029's focused
  suite.

## Limits and suite impact

No game client execution is claimed: gameplay and release pipelines are outside
requirement 029. Remote sync routing is tested with substituted GitHub responses;
no consumer repository was modified. Canonical OMPR changes add role-specific
scaffolding and guidance; OMS, OMV and OMP keep their existing non-addon roles
and deployment behaviour. Requirement 030's opt-in runtime changes remain
separate and unimplemented.
