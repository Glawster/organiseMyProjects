# OMPR runtime synchronisation

OMPR means **organiseMyProjects**. The `ompr` directory is the managed
deployment package for shared runtime helpers. The name `omp` belongs to
**organiseMyPhotos** and is never used for OMPR runtime files.

The source of truth remains `organiseMyProjects/logUtils.py` and
`organiseMyProjects/logUtils.sh` in the OMPR repository. The
`organiseMyProjects/runtimeSync.py` allowlist identifies the precise files
eligible for deployment; adding an unrelated toolkit module never causes it
to be copied.

## Installation into an existing local repository

Preview without writing:

```bash
manageProject sync --runtime --project ~/Source/mailAgent
```

Confirm a selected repository:

```bash
manageProject sync --runtime --project ~/Source/mailAgent --confirm
```

Batch preview and confirmation require explicit targets:

```bash
manageProject sync --runtime --project ~/Source/mailAgent --project ~/Source/organiseMyVideo
manageProject sync --runtime --project ~/Source/mailAgent --project ~/Source/organiseMyVideo --confirm
```

`manageProject update` previews runtime deployment by default and installs
the copies with `--confirm`. `manageProject create --confirm` includes an
`ompr/` package in a new scaffold. Existing remote GitHub instruction sync
is unaffected: `manageProject sync` without `--runtime` retains its
existing behaviour.

## Safety and provenance

Every deployed file begins with an `OMPR-RUNTIME-MANAGED` comment naming
the canonical source and the OMPR version; shell shebangs remain first.
Changes are previewed before confirmation. Only recognised marked runtime
files can be replaced; unowned modules are not overwritten. A conflicting
unowned `ompr` package blocks that selected target, without stopping other
batch targets. Symlinked destinations are not followed. A repeat sync is
idempotent; files modified under the managed marker are deliberately refreshed
from canonical content.

After deployment, application code can use:

```python
from ompr.logUtils import getLogger, setApplication
```

Shell scripts can source their local `ompr/logUtils.sh`. The deployed
Python module has no dependency on the installed OMPR toolkit.

## Packaging existing consumers

New OMP-generated project `pyproject.toml` files explicitly include both
the application package and `ompr`, plus `ompr/*.sh` as package data.
An **existing** project's `pyproject.toml` is project-owned and is not
rewritten by runtime sync. For a setuptools project using an explicit package
list, add `ompr` to that list and configure shell package data if required;
other build backends need equivalent configuration. Verify the installed
wheel or source distribution, not just imports from the checkout.

Runtime sync does not automatically rewrite existing imports or alter
packaging metadata. Adoption is an explicit project migration.

## Validation

Run focused tests with:

```bash
python -m pytest tests/test_runtimeSync.py
```

Before merging also run the full OMPR suite, Black, Ruff, runLinter,
markup checks and a clean distribution build. Tests must prove that an
isolated consumer can import `ompr.logUtils` without installing OMPR.
