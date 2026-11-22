# Release 0.10 closeout

## Delivered scope

The user declared the delivered 0.10 scope complete and requested the release
PR into `main`. The release includes runtime infrastructure (002), branch/version
reporting (024), WoW addon projects (029), optional local runtime deployment
(030) and the earlier 0.10 board/style/account-availability work. Requirement
acceptance reviews remain authoritative for their individual criteria.

Requirements 025 and 027 remain ToDo for 0.11. Other pending requirements stay
in the requirements index; publishing this release does not claim they are done.

## Final version validation

2026-11-22, `release/0.10`, final version `0.10`, using the existing `ompr`
Conda environment with existing `wow` Lua tools on PATH:

- `python -m pytest -q -rs`: **734 passed, no skips**.
- `ruff check .`: passed.
- `black --check --workers 1 .`: 75 files passed.
- `python -m organiseMyProjects.runLinter .`: 75 files passed.
- `python -m organiseMyProjects.runLinter --markup`: passed.
- `python -m organiseMyProjects.agentCheck`: zero failures, zero warnings;
  CLI/log version `0.10`.
- `git diff --check`: passed.
- `python -m build --sdist --wheel --no-isolation --outdir /tmp/ompr010-release-dist`:
  successfully built `organisemyprojects-0.10.tar.gz` and
  `organisemyprojects-0.10-py3-none-any.whl`.
- Authoritative `VERSION` and resolved `pyproject.toml` package metadata both
  report `0.10`; release notes identify the final release.

## Publication contract

Merge `release/0.10` into `main` through a regular merge PR after CI succeeds,
preserving branch ancestry. Create a new annotated `v0.10` tag on that final
`main` commit and verify its remote target. The release PR, CI and Git refs
record publication status; existing alpha tags are retained.

No downstream application repositories or account configuration are modified
by this release closeout. Application migration limits remain documented in
the runtime guide and requirement reviews.
