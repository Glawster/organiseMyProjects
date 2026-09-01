# organiseMyProjects

A Python toolkit for creating, maintaining and validating Glawster projects with
a consistent repository structure, packaging model, logging, coding standards
and agent guidance.

## Documentation

The root `README.md` is the repository documentation entry point. OMP 0.6
reserves `README.md` for the repository root. When a directory genuinely needs
an index, its filename is derived from the folder name as
`<folderName>Index.md`.

The living guides are:

- [Developer Guide](documentation/developer.md)
- [Git Guide](documentation/git.md)
- [Release Guide](documentation/howToRelease.md)
- [Release Notes](documentation/releaseNotes.md)
- [Repository Layout](documentation/repositoryLayout.md)
- [Requirements Management](documentation/requirementsManagement.md)
- [Testing Process](documentation/testingProcess.md)
- [AI Agent Portability Design](documentation/agentPortabilityDesign.md)
- [GUI Naming Linter Help](organiseMyProjects/HELP.md)
- [Master Agent Instructions](.github/agent-instructions.md)
- [Repository Agent Notes](.github/additional-instructions.md)
- [Architecture Decisions](project/adr/adrIndex.md)
- [Requirements](project/requirements/requirementsIndex.md)

## OMP 0.6 development direction

OMP 0.6 makes the generated scaffold conform to the repository standards that
OMP distributes.

New Python projects use a root-level Python package named after the project.
OMP 0.6 does not use a generic `src/` directory for newly scaffolded projects.
For example:

```text
footballVision/
├── .github/
├── .vscode/
├── documentation/
├── project/
│   ├── adr/
│   │   └── adrIndex.md
│   ├── requirements/
│   │   └── requirementsIndex.md
│   └── reviews/
├── footballVision/
│   ├── __init__.py
│   └── ...
├── tests/
├── pyproject.toml
├── footballVisionEnvironment.yml
├── README.md
└── .gitignore
```

Every newly created Python project is an importable package. A root-level
`main.py` is not part of the standard 0.6 scaffold. Libraries need no executable
entry point; CLI and application entry points are declared according to project
role and point into the project package.

`pyproject.toml` is the authoritative packaged-Python metadata and dependency
definition. New projects use a project-specific camelCase Conda environment
file and an editable-install development workflow.

OMP 0.6 also extends deterministic migrations to cover OMP-managed files and
project scaffold indexes that move to new canonical paths. Obsolete legacy
copies are removed only when OMP can establish a deterministic, no-loss
migration; ambiguous or user-owned files are preserved.

Requirements are flat numbered specifications, for example
`project/requirements/features/003-viewManagement.md`. A single prompt uses the
same filename under `project/requirements/prompt/`; multiple prompts use the
existing `003a-`, `003b-` suffix convention.

See
[requirement 003](project/requirements/features/003-omp06ManagedMigrationAndScaffold.md)
and
[requirement 004](project/requirements/features/004-requirementDocumentationLayout.md)
for the governing 0.6 behaviour.

## Features

- Preview or create a standard Python project scaffold.
- Update OMP-owned managed files without taking ownership of project code.
- Migrate recognised legacy OMP structures through deterministic, safe rules.
- Validate repository and agent readiness with a read-only check.
- Synchronise shared OMP managed guidance.
- Run OMP Python naming and markup checks.
- Provide pre-commit and coding-standard guidance.

## Installation

OMP itself is a packaged Python project. From its Conda environment, install it
in editable mode for development:

```bash
pip install -e .
```

## Usage

### Create a new project

Creation is preview-only unless `--confirm` is supplied:

```bash
createProject myNewProject
createProject myNewProject --confirm
```

OMP 0.6 creation is governed by the standard package layout above. Optional UI
or Qt scaffolds, where supported, belong within the project package rather than
creating a second application-code ownership model.

```bash
createProject myNewProject --ui --confirm
createProject myNewProject -qt --confirm
```

### Update an existing project

Previewing is the default. Add `--confirm` to apply the update:

```bash
# from anywhere
createProject myExistingProject --update
createProject myExistingProject --update --confirm

# or from the project directory
createProject --update
createProject --update --confirm
```

Updates refresh OMP-owned managed files only when their substantive content
changes. Existing project-owned application code, dependencies and application
layout are preserved unless a specific deterministic migration proves a change
safe.

Requirement 004 cleanup includes recognised migration of OMP-owned nested
`README.md` indexes and the mistaken `folderIndex.md` form to the canonical
folder-derived names, including:

```text
project/requirements/requirementsIndex.md
project/adr/adrIndex.md
```

It also safely flattens provable per-requirement and per-prompt directory
mistakes. Arbitrary nested README files are not renamed or deleted merely
because of their filename.

For 0.6, recognised managed path relocations also include the guides moved from
`.github/` to `documentation/`. A relocation may remove the obsolete path only
when OMP ownership is established.

When the target is the canonical `organiseMyProjects` source repository,
`manageProject --update` avoids applying downstream scaffold copies over their
canonical sources.

### Migrate an existing project

Migration adds missing OMP project-management/context structures without
blindly reorganising project-owned application code:

```bash
createProject --migrate
createProject --migrate --confirm
```

Existing projects that use `src/` are not automatically moved into the 0.6
root-package structure merely because OMP has adopted a new creation standard.

### Check repository readiness

```bash
manageProject --check
```

The check operation is read-only and validates the applicable OMP repository,
documentation and agent conventions, including the one-root-README rule and
canonical named directory indexes.

### Run Python and GUI naming checks

```bash
runLinter
runLinter <file-or-directory>
```

### Run markup checks and fixes

```bash
runLinter --markup
runLinter --markup --fix
fixMarkup
fixMarkup --check
```

## Python packaging and environment policy

OMP projects target Python 3.10 or later unless a project records a stricter
runtime requirement.

For newly scaffolded projects:

- prefer Conda for Python environment management;
- use `<projectName>Environment.yml` with the project name in camelCase;
- declare packaged dependencies in `pyproject.toml`;
- install the package in editable mode for development;
- document Conda setup before alternative `venv` instructions;
- do not auto-install dependencies at runtime;
- validate required external tools explicitly and fail fast when missing.

A `requirements.txt` file may exist for a specific compatibility or deployment
need, but it is not the primary dependency definition for new packaged OMP
projects.

## Testing

Run the OMP test suite with:

```bash
pytest
```

Useful focused commands include:

```bash
pytest tests/test_createProject.py
pytest tests/test_requirementLayout.py
pytest tests/test_integration.py
pytest -v
ruff check .
black --check .
```

OMP 0.6 scaffold and migration work must include regression tests for dry-run
behaviour, confirmed updates, managed-file ownership protection, idempotent
reruns, generated package importability and packaging/environment metadata.

## Development conventions

- Functions and variables use camelCase.
- Classes use PascalCase.
- Constants use UPPER_CASE_WITH_UNDERSCORES.
- `README.md` is reserved for repository root.
- Use `<folderName>Index.md` when a directory genuinely needs an index.
- Use the OMP logging utilities from `organiseMyProjects.logUtils` rather
  than ad-hoc output where application logging is required.
- Use Black, Ruff, pytest and the OMP linter before release.
- Requirements live under `project/requirements/features/`.
- The requirements index is `project/requirements/requirementsIndex.md`.
- Architecture decisions live under `project/adr/` and their index is
  `project/adr/adrIndex.md`.
- Transient implementation status belongs only in
  `project/currentIncrement.md`.

## Shared runtime infrastructure

Runtime helpers such as logging live in the `organiseMyProjects` package.
Applications import `from organiseMyProjects.logUtils import getLogger`.

## Sync agent instructions and managed guidance

`organiseMyProjects` is the canonical source for shared agent guidance and
managed documentation. `syncAgentInstructions.py` distributes those managed
files to eligible repositories.

Examples:

```bash
# preview all eligible repositories
python syncAgentInstructions.py

# choose one repository interactively
python syncAgentInstructions.py --repo

# choose one repository explicitly
python syncAgentInstructions.py --repo Glawster/myRepository

# apply changes
GITHUB_TOKEN=<your-pat> python syncAgentInstructions.py --confirm
```

Managed files contain deployment markers identifying their OMP source release.
Marker-only version differences do not force a substantive rewrite.

## Release process

The maintained release procedure is in
[documentation/howToRelease.md](documentation/howToRelease.md). Release notes
are maintained in [documentation/releaseNotes.md](documentation/releaseNotes.md).

## License

This project is licensed under the [MIT License](LICENSE).
