# Release notes

## 0.7 — in development

OMP 0.7 improves default `runLinter` discovery for root-package repositories
and relaxes class-method and private-constant naming.

### Linter discovery

- With no CLI targets, `runLinter` inspects `pyproject.toml` packaging
  configuration, then a package directory matching the repository name, then
  `src/`, `ui/`, `qt/` and `tests/`.
- It does not lint the whole repository merely because `src/` is absent.
- `.` is used only when no plausible source directory exists.
- Duplicate discoveries are collapsed. Explicit targets still override
  discovery.

### Commands

- `manageProject` uses commands: `create`, `update`, `check`, `migrate` and
  `sync`.
- `manageProject update -y` updates the current project; it does not create a
  directory named `update`.
- `create` requires `--project PROJECTNAME`.
- `update`, `check` and `migrate` default to the current directory; pass
  `--project PROJECTNAME` to target another directory.
- Legacy flags such as `--update` and `--check` still map to those commands.

### Naming

- Class methods may use action-only names such as `Project.update()`.
- Module-level functions still require `domainAction`.
- Nested or local helpers may use ordinary descriptive names and are not
  required to use `domainAction`.
- Private constants such as `_MAX_RETRIES` are accepted.

## 0.6 — in development

OMP 0.6 aligns generated project structure with the standards OMP distributes
and makes established-project updates policy-driven.

### Project scaffold

- New OMP Python projects use a root-level Python package named after the
  project rather than a generic `src/` directory.
- A root-level `main.py` is no longer part of the standard scaffold; executable
  entry points are role-dependent and live in or point into the project
  package.
- New projects are packaged through `pyproject.toml` and use a project-specific
  camelCase Conda environment file with an editable-install development
  workflow.
- The generated project-management, documentation and test structure matches
  `documentation/repositoryLayout.md`.

### Managed-file migration

- Deterministic migration covers managed path relocations as well as filename
  renames.
- The 0.5 to 0.6 migration covers the managed guides moved from `.github/` to
  `documentation/`, including repository layout, requirements management and
  release guidance.
- Obsolete legacy copies may be removed only when OMP can establish that the
  file is OMP-managed; ambiguous or user-owned files are preserved.
- Dry-run output, explicit relocation logging and idempotent reruns are required
  behaviours.

### Project-role-aware updates

- Every file `createProject` can deploy has exactly one ownership policy:
  managed overwrite, managed-block merge, or project-owned missing-only.
- Pytest, pre-commit, editor, environment and dependency files keep
  project-owned content and merge only the marked `OMP-MANAGED` block.
- Dry-run update output says `would create` or `would update` and ends with
  an unambiguous simulation summary.

### Adoption

Existing project application layouts are not automatically reorganised merely
to adopt 0.6. Ordinary update does not blindly move existing `src/` application
code. Managed-file path cleanup is limited to files whose OMP ownership can be
established safely.

See requirement 003 for the governing 0.6 scaffold and migration behaviour.

## 0.5

OMP 0.5 strengthens safe project updates, portable agent context and repository
validation while reducing documentation and managed-file churn.

### Project management

- `manageProject` supports create, update, migrate, sync and read-only check
  workflows with safe preview behavior and `--confirm` for applied changes.
- Project-role detection recognizes standalone applications, packaged CLIs and
  libraries using `main.py`, `pyproject.toml`, `setup.cfg`, `setup.py` and
  `src/` markers. OMP itself is identified as a packaged CLI.
- Project updates preserve project-owned application structure and perform only
  narrow, deterministic legacy filename migrations.
- Updating the canonical OMP repository is a deliberate no-op, preventing
  downstream scaffolds such as copied linter modules or generic configuration
  from being applied over their source repository.
- Managed files are updated only when substantive content changes. OMP release
  markers alone do not cause rewrites, and repeated managed headers are
  normalized to one marker.

### Agent and documentation portability

- `AGENTS.md` provides a vendor-neutral entry point, with lightweight Copilot
  and Claude compatibility pointers.
- Managed repository-layout, requirements-management, testing and release
  guides give downstream projects the same baseline.
- `manageProject --check` validates agent entry points, documentation links,
  current-increment consistency and requirements/ADR relationships.
- `project/currentIncrement.md` is the sole transient implementation-status
  record. Requirements retain durable obligations and lifecycle state; ADRs own
  decisions, documentation owns durable behavior, tests own executable evidence
  and Git owns delivery history.

### Linting and naming

- Python test filenames use `test_camelCaseName.py`.
- The Python linter understands test context instead of applying production
  naming rules blindly. It exempts dunder methods, pytest fixtures, required
  framework overrides, private test helpers and `_PascalCase` test doubles.
- Module-level function spacing remains enforced without requiring blank lines
  inside method bodies.
- Markup checking and automatic fixes are available through `runLinter
  --markup`, `runLinter --markup --fix` and `fixMarkup`.

### Logging

- Python and Bash logs use fixed four-character levels such as `[INFO]`,
  `[WARN]` and `[ERRO]`.
- `manageProject` logs the running OMP version, including during `--check`.
- Semantic progress logging distinguishes safe previews from applied actions.

### Adoption

Existing projects do not need to rewrite historical requirements or other
documents solely to adopt 0.5. Run an update preview, inspect the proposed
managed changes, apply with `--confirm`, and then run `manageProject --check`.
