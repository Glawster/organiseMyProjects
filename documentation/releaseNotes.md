# Release notes

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
