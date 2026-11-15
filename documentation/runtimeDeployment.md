# Deployed OMPR runtime

OMPR means organiseMyProjects. OMP means organiseMyPhotos. Applications receive
shared runtime helpers in a managed `ompr/` package so they can run without the
OMPR development tools installed. Canonical sources remain in
`organiseMyProjects/`; that repository has no sibling runtime package.

## New applications

`manageProject create myApplication --confirm` deploys Python and Bash logging,
OMPR version metadata and a minimal package initializer. Generated UI entry
points use:

```python
from ompr.logUtils import getLogger, setApplication
```

The generated packaging includes `ompr` and its shell resources. OMPR's
`version.py` identifies the helper source release, not the application version.
Use application-relative paths to source Bash helpers:

```bash
source "${applicationRoot}/ompr/logUtils.sh"
setApplication "myApplication"
```

The application establishes `applicationRoot` from its own installed layout.
OMPR tooling itself continues importing `organiseMyProjects.logUtils`.

## Existing applications

Preview `manageProject update` and apply with `--confirm`. Managed runtime
copies are refreshed, including locally modified managed helpers. Unmarked
packages/files and symlink destinations require review and are preserved.
Unchanged files retain their timestamps and original provenance release.

Ordinary updates preserve application code and packaging. They report detected
legacy imports in root Python files, the project-named package, `src/` and
`scripts/`, and always report the packaging review. This is a bounded aid,
not a complete analysis of dynamic imports, custom source roots or Bash scripts.

Complete consumer migration explicitly:

1. Change application runtime imports to `ompr.logUtils`. Review other imports
   individually; development tools still belong to `organiseMyProjects`.
2. Include `ompr` in package discovery or explicit package lists and include
   `ompr/logUtils.sh` as package data. Preserve the application's other packages.
3. Update Bash source paths and deployment manifests for the installed layout.
4. Build and install the application in a clean environment without OMPR and
   exercise its actual entry point, logging and resources.
5. Remove OMPR from production dependencies only after that verification. Keep
   it available in the development environment for linting and management tools.

An existing user-owned `ompr/` package is never adopted automatically. Resolve
that namespace collision manually before running deployment again. Do not
rename or modify an organiseMyPhotos `omp/` package as part of this migration.

## Repository and batch sync

Instruction-only sync remains the default. Add `--runtime` to include runtime
helpers in a selected repository or the eligible repository batch:

```bash
manageProject sync --repo Glawster/myApplication --runtime
manageProject sync --repo Glawster/myApplication --runtime --confirm
manageProject sync --runtime
```

Without `--confirm`, no API writes or runtime changes are made. Remote runtime
updates validate ownership before an atomic Git tree commit, preserve executable
modes and keep unrelated files. Existing application imports and packaging are
not rewritten. Review the generated branch before opting into `--merge`.
Runtime errors prevent automatic merging of that repository's sync branch.

## Extending the runtime

`organiseMyProjects/runtimeDeployment.py` declares the shared manifest. Add only
self-contained helpers or include their complete dependency closure. Never add
the tooling initializer, application logic, UI or project configuration. Add
isolated deployment tests for new helpers; create, update and runtime sync then
use the same manifest without consumer-specific synchronisation code.
