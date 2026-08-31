# Runtime Infrastructure Synchronisation

## Status

Proposed

## Objective

Establish a standard mechanism for sharing reusable runtime infrastructure
between Glawster projects without introducing runtime dependencies between
repositories.

The canonical implementation of shared runtime modules shall reside in the
`organiseMyProjects` repository.

Each consuming project shall receive synchronised deployment copies of those
modules within a reserved `omp` package.

The name `omp` represents **organiseMyProjects**.

---

## Motivation

Many projects require common runtime functionality including:

- logging
- version reporting
- configuration helpers
- command-line helpers
- YAML utilities
- Git helpers

Maintaining separate implementations leads to divergence.

Introducing `organiseMyProjects` as a runtime dependency would make deployment,
distribution and packaging more complex.

Synchronised deployment copies provide the benefits of a single canonical
implementation while keeping every application self-contained.

---

## Repository Layout

The canonical repository shall contain:

```text
organiseMyProjects/
├── omp/
│   ├── __init__.py
│   ├── logUtils.py
│   ├── version.py
│   ├── configUtils.py
│   ├── yamlUtils.py
│   └── ...
```

Each consuming project shall contain:

```text
project/
├── omp/
│   ├── __init__.py
│   ├── logUtils.py
│   ├── version.py
│   └── ...
```

The internal structure should remain identical wherever practical.

---

## Runtime Imports

Applications shall import runtime infrastructure using:

```python
from omp.logUtils import getLogger
```

Applications shall not import runtime modules directly from
`organiseMyProjects`.

---

## Ownership

Every module inside `omp` shall have one canonical owner:

`Glawster/organiseMyProjects`

Projects shall treat the local copy as generated deployment content.

Behavioural changes shall always be made in the canonical repository before
being synchronised into consuming repositories.

---

## Synchronisation

Synchronisation shall be performed by the standard project management tools.

The synchronisation process shall:

- deploy runtime modules
- preserve executable permissions where required
- overwrite locally modified managed files
- include provenance information
- support dry-run mode
- support repository selection
- support batch synchronisation

Synchronised runtime modules shall use a standard deployment header indicating:

- originating repository
- release/version
- warning against local modification

---

## Package Contents

Modules within `omp` shall contain only reusable runtime infrastructure.

Typical examples include:

- logging
- version information
- configuration helpers
- filesystem helpers
- CLI helpers
- Git helpers
- YAML helpers

---

## Exclusions

The `omp` package shall not contain:

- application business logic
- user interface code
- OCR
- databases
- project-specific configuration
- domain models
- application requirements
- tests specific to one application

---

## Repository Standards

The directory name `omp` is reserved across all Glawster repositories.

Its meaning shall always be:

> Local runtime infrastructure synchronised from
> `organiseMyProjects`.

Projects shall not use `omp` for unrelated code.

---

## Deployment

Projects shall remain fully deployable without requiring
`organiseMyProjects` to be installed.

Runtime dependencies on the canonical repository are explicitly prohibited.

---

## Versioning

The synchronisation process shall record the originating
`organiseMyProjects` release.

Future tooling may validate whether a consuming repository is using the latest
approved runtime infrastructure.

---

## Acceptance Criteria

1. Every synchronised project contains an `omp` package.
2. Runtime modules are imported exclusively through `omp`.
3. Runtime dependencies on `organiseMyProjects` do not exist.
4. Synchronised modules include provenance information.
5. Synchronisation can update all managed runtime modules automatically.
6. Only reusable infrastructure is stored within `omp`.
7. Application-specific code is never synchronised into `omp`.
8. Projects remain independently deployable.
9. The repository standards document defines `omp` as a reserved package name.
10. Future shared runtime modules can be added without changing consuming
projects beyond synchronisation.
