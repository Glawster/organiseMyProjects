# Optional OMPR runtime

OMPR means organiseMyProjects. OMP means organiseMyPhotos. Canonical runtime
helpers live in `organiseMyProjects/`. Projects normally use the installed
package; local `ompr/` deployment is an explicit opt-in.

## Choose and save the mode

```bash
manageProject create --project myApplication --confirm
manageProject create --project portableApplication --runtime --confirm
manageProject update --runtime --confirm
manageProject update --no-runtime --confirm
```

The saved choice is a top-level boolean in `project/project.yaml`:

```yaml
localRuntime: false
```

`--runtime` saves true and installs or refreshes the manifest. `--no-runtime`
saves false and removes recognised managed copies after migration checks.
Neither flag means use the saved choice, defaulting to false when absent.
Existing folders do not imply opt-in. Duplicate or invalid settings fail before
changes, even with an explicit override. Use unquoted `true` or `false` on its
own top-level line. Other project metadata and comments are preserved.

Without `--confirm` all commands preview their changes. Conflicting runtime
flags are rejected. WoW addons and the canonical OMPR repository do not receive
runtime copies. Update does not rewrite project-owned application code or
packaging when switching modes.

## Default applications

New default scaffolds contain no `ompr/`, import installed canonical helpers,
and declare `organiseMyProjects` as a production dependency:

```python
from organiseMyProjects.logUtils import getLogger, setApplication
```

Install the project in its Conda environment using `pip install -e .`. For Bash,
locate the installed resource in the application's environment:

```bash
runtimeRoot="$(python -c 'from importlib.resources import files; print(files("organiseMyProjects"))')"
source "${runtimeRoot}/logUtils.sh"
setApplication "myApplication"
```

This requires the declared toolkit dependency to be installed; no helper is
automatically installed at application startup.

## Opted-in applications

`--runtime` deploys a minimal initializer, Python and Bash logging, and OMPR
source-release metadata from the shared manifest. Generated entry points use:

```python
from ompr.logUtils import getLogger, setApplication
```

Generated packaging includes `ompr` and its shell resources, without a runtime
dependency on the toolkit. `ompr/version.py` identifies the helper source
release, not the application's version. Bash scripts use application-relative
paths to `ompr/logUtils.sh`. Managed copies may be refreshed on update;
implement shared helper changes in the canonical source.

## Disable and remove existing copies

An unconfigured legacy project now defaults to disabled. To retain existing
local helpers, run `manageProject update --runtime --confirm` before relying
on future updates. To remove them:

1. Migrate application imports from `ompr` to `organiseMyProjects` and declare
   that distribution as a production dependency where logging helpers are used.
2. Remove explicit `ompr` package lists and shell package-data entries from
   application packaging. Update Bash source paths and deployment manifests.
3. Verify the application with the installed dependency, then preview
   `manageProject update --no-runtime` and apply with `--confirm`.

Cleanup scans Python imports and literal dynamic references, shell paths,
packaging and deployment text throughout the project. It excludes version
control, environments, caches and generated output. Unknown dynamic references,
custom file formats and excluded locations require maintainer review. Known
references, unreadable source and symlinks in source paths block cleanup with
file-level guidance; the runtime and saved choice remain untouched.

Only recognised manifest files with current provenance or historical
`OMPR-RUNTIME-MANAGED` headers are removed. Every removed file is first backed
up, including local modifications and executable modes, under
`output/omprRuntimeBackups/<unique-id>/`. Keep those backups until migration is
verified. New scaffolds ignore `output/`; existing projects should keep local
backup output out of their distributions and version control.

Unowned packages, unknown files and symlink runtime paths are preserved and
reported. The directory is removed only when empty; preserved content, including
unowned caches, can leave an `ompr/` directory requiring manual review. Repeated
updates do not recreate disabled managed helpers or duplicate successful backups.

## Local and remote sync

Local runtime-only reconciliation uses the same saved preference:

```bash
manageProject sync --project ~/Source/myApplication --runtime
manageProject sync --project ~/Source/myApplication --runtime --confirm
manageProject sync --project ~/Source/myApplication --no-runtime --confirm
```

Remote sync stays instruction-only unless a runtime flag is supplied, even for
saved-enabled projects:

```bash
manageProject sync --repo Glawster/myApplication --runtime
manageProject sync --repo Glawster/myApplication --runtime --confirm
manageProject sync --repo Glawster/myApplication --no-runtime --confirm
```

Remote explicit flags save the corresponding preference and reconcile runtime
files in one atomic Git tree commit. Disabling checks tracked source and
configuration from the same immutable snapshot and commits recovery backups
alongside deletions. Unknown runtime paths and unsupported symlinks require
review. Runtime errors prevent automatic merging of that repository's sync
branch. Review generated branches before requesting `--merge`; application
imports and packaging are never rewritten automatically.

## Extend the manifest

`organiseMyProjects/runtimeDeployment.py` declares the shared manifest. Add only
self-contained helpers or their complete dependency closure. Never add tooling
initializers, UI, application logic or project configuration. Add isolated
runtime and reconciliation tests when extending the manifest.
