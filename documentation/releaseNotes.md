# Release notes

## 0.9 — 2026-10-26

OMP 0.9 adds the `myBoard` requirement board and the `agentSessions` command,
makes `runLinter` report and exit like pytest, and gives every development
branch its own alpha version.

### Requirement board

- New `myBoard` command: shows the requirements of the project it is run from
  in Backlog, ToDo, InProgress and Completed columns.
- `myBoard move` updates the requirement record, `requirementsIndex.md` and
  `project/currentIncrement.md` together. Without `--confirm` it only reports
  the files it would change.
- `myBoard edit NUMBER` replaces a requirement's title, index description or
  prose sections and keeps the index and increment in step (requirement 023).
  Values that would break the index are refused, and a section the record
  does not have yet is added in template order.
- Only one card is selected at a time. A right click selects a card; a left
  click or Enter opens it.
- An open requirement shows its linked branch, that branch's commits and each
  changed file. Checks, `runLinter` and pytest (`p`) run on request, and pytest
  failures that name the requirement's files are listed on its card.
- Command errors are logged as errors.
- See [Requirement board](myBoard.md).

### Agent sessions

- New `agentSessions` command, moved from linuxMigration: lists local Codex,
  Claude, Grok and Copilot sessions for the current directory, with titles.
  Session stores are never edited.
- `--resume` picks a session from a menu and resumes it in its own directory.
- `--claude`, `--codex`, `--copilot` and `--grok` list only those agents'
  sessions, from every directory; the flags combine. `--all`, `--history` and
  `--search` widen or narrow the listing.
- The DIRECTORY column shows only the folder name.
- See [Agent sessions](agentSessions.md).

### runLinter reporting

- `runLinter` reports pytest-style: relative `path:line:` locations, a stable
  rule identifier and rule-specific message for every finding, per-file
  `PASSED`/`FAILED` progress and a closing summary line.
- **Exit status now reflects the result:** `0` clean, `1` findings, `2` invalid
  invocation or unusable target, `5` nothing linted. Previously `runLinter`
  always exited `0`, so pre-commit hooks and CI jobs that run it will now fail
  on existing findings. Run `runLinter` in each project and fix or review its
  findings before upgrading.
- See [the linter guide](linter.md#output-and-exit-status).

### List editing interaction

- New [list editing interaction](listEditingInteraction.md) standard for list-
  and table-driven applications: list-first editing, consistent single-key
  actions (`a` add, `e` edit, `d` delete, `Enter`, `Esc`, `Space`), choosing
  known values instead of retyping them, confirmation for destructive actions,
  internally scrolling tables and discoverable key bindings.
- Requirement 027 covers deploying the guide through manageProject and adding
  reliable static checks.

### Release process

- Every development branch takes its own alpha version, one that no tag or
  other branch holds, so a version always identifies one branch's work.
- Each branch's work is tagged with its alpha version (`v0.9a4`) when it is
  integrated, with the pull request in the tag message.
- Projects without release branches record that exception in
  `.github/additional-instructions.md`; numbering and tagging still apply.
- See the [release guide](howToRelease.md).

### Other changes

- A shared Textual style mockup command, `styleMockup`, renders the canonical
  stylesheet to a reproducible SVG.
- Import-time patch installation is removed from the package; the behaviour
  now lives in the modules that own it.

## 0.8 — 2026-10-17

OMP 0.8 centralises downstream linting, distinguishes repository and project
roots, and provides shared Textual styling.

### Linting and logging

- Downstream projects use the installed OMP linter. Updates remove recognised
  obsolete local linter copies while preserving custom implementations.
- Naming checks accept digit-aware names, approved proper names and acronyms,
  and framework-required Textual hooks.
- Spelling checks ignore docstrings; documentation checks ignore generated
  cache directories.
- Entry-point logging checks validate run markers and section separators.
  `runLinter` reports its OMP version at startup, and `logUtils.line()` provides
  a shared section separator.

### Repository checks

- Git-aware discovery resolves repository-owned entry points against the
  repository root while retaining the selected project root for local checks.
- Diagnostics identify both roots when they differ or verbose output is used.
- Non-Git projects and systems without Git use a deterministic fallback.

### Shared styling and guidance

- The packaged `myStyles.css` supplies the shared palette and one-row Textual
  buttons with consistent borders, padding and semantic colours.
- Opt-in horizontal button groups provide equal sizing and consistent gaps.
- Theme deployment supports provenance checks, previews and idempotent updates,
  preserves custom themes and exempts `clannEolas`.
- See [Shared TUI Styling](tuiStyling.md) for adoption and
  [Agent Implementation Workflow](agentImplementationWorkflow.md) for delivery
  guidance. The optional development dependencies include Textual for rendering
  tests.

## 0.7

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

## 0.6

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

### OMP 0.5 adoption

Existing projects do not need to rewrite historical requirements or other
documents solely to adopt 0.5. Run an update preview, inspect the proposed
managed changes, apply with `--confirm`, and then run `manageProject --check`.
