# 019: Environment and test configuration consistency

## Status

ToDo

## Outcome

As an OMPR user, I need the files OMPR scaffolds and manages for environments,
packaging and tests to agree with one another and with the testing standard,
so that a project's environment installs what it claims, pytest reads one
configuration, and the coverage standard can actually be measured.

## Context

The 2026-10-20 `mailAgent` review found:

- The OMP-managed block in `mailAgentEnvironment.yml` installs `-e .[dev]`,
  but `pyproject.toml` defines no `dev` extra.
- The managed environment declares `python>=3.10`, `pyproject.toml` requires
  `>=3.11`, and a legacy `environment.yml` pins `3.12`; both environment files
  exist.
- `pytest.ini` and `[tool.pytest.ini_options]` both exist, so pytest warns
  "ignoring pytest config in pyproject.toml". The new-project scaffold in
  `manageProject.py` writes both (`PYTEST_INI_CONTENT` and the pyproject
  section), so new projects start with the same conflict.
- `.github/agent-instructions.md` requires core logic coverage above 90%, but
  neither the scaffolded `dev` extra nor `DEV_REQUIREMENTS_MANAGED_BLOCK`
  includes `pytest-cov`, so coverage cannot be measured.
- Existing projects onboarded by update receive no `[tool.black]
  target-version`; black then warned that it inferred Python 3.15.

Requirement 014 recorded the related open question that update still manages
`environment.yml` while new projects use `<packageName>Environment.yml`.

## Scope

- Scaffold exactly one pytest configuration for new projects.
- Report a project that has both `pytest.ini` and
  `[tool.pytest.ini_options]`.
- Report a managed environment that installs an extra not defined in
  `pyproject.toml`.
- Report disagreement between the managed environment's Python constraint and
  `requires-python`.
- Report a legacy `environment.yml` alongside `<packageName>Environment.yml`
  and resolve requirement 014's open question on which one update manages.
- Include `pytest-cov` in the scaffolded and managed development dependencies.
- Report a missing `[tool.black] target-version` and offer the scaffold value
  during update when the project does not already set one.

## Out of scope

- Enforcing a coverage percentage in `manageProject --check`.
- Choosing a project's Python version for it.
- Environment managers other than Conda.

## Acceptance criteria

1. Given a newly scaffolded project, when pytest runs, then it reports no
   ignored configuration warning.
2. Given a project with both pytest configurations, when checked, then a
   finding names both files.
3. Given a managed environment installing `.[dev]` and a `pyproject.toml`
   without a `dev` extra, when checked, then a failure is reported.
4. Given a managed `python>=3.10` and `requires-python = ">=3.11"`, when
   checked, then a warning reports the disagreement.
5. Given both `environment.yml` and `<packageName>Environment.yml`, when
   checked, then a warning identifies the legacy file, and update's behaviour
   is documented.
6. Given a newly scaffolded or updated project environment, when created, then
   `pytest --cov` runs without installing anything else.
7. Given a project without `[tool.black] target-version`, when checked, then a
   warning is reported.

## Dependencies and decisions

- Resolves the open question recorded in requirement 014.
- Builds on requirement 008 scaffold consistency for existing projects.
- May need an ADR if the choice between `pytest.ini` and `pyproject.toml`
  changes managed-file ownership in ADR-001.

## Verification

- Scaffold a fixture project and run pytest and `pytest --cov`.
- Fixture tests for each check.
- Run `manageProject --check` against `mailAgent` and confirm the findings
  listed in Context are reported.

## Change history

- 2026-10-20: created — `mailAgent` review found inconsistent environment,
  packaging and test configuration; captured for the 0.9 backlog.
