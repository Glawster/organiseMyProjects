# 019: Implement environment and test configuration consistency

Implement requirement 019,
[Environment and test configuration consistency](../features/019-environmentAndTestConfigConsistency.md).
The requirement is authoritative for scope and acceptance criteria 1–7.

Make the scaffold write one pytest configuration, add `pytest-cov` to the
development dependencies, and add checks for undefined extras, Python
constraint disagreement, a legacy `environment.yml`, duplicate pytest
configuration and a missing black target version. Resolve requirement 014's
open question on which environment file update manages and record the answer.

Constraints:

- Respect ADR-001 managed-file ownership; record an ADR if ownership changes.
- Do not pick a project's Python version for it.

Allowed files: `organiseMyProjects/manageProject.py`, `organiseMyProjects/agentCheck.py`, their tests and the affected documentation.

Verification: run `pytest` in the `ompr` environment, `runLinter .` and
`manageProject --check`, and hand off the evidence for each acceptance
criterion.
