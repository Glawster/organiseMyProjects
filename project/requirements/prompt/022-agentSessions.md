# 022: Move agentSessions into organiseMyProjects

## Assignment

Implement and verify [requirement 022](../features/022-agentSessions.md),
acceptance criteria 1–11, following .github instructions and the shared process
guides. The command arrives from linuxMigration; keep its behaviour unchanged.

## Boundaries

Change organiseMyProjects/agentSessions.py, its console-script entry in
pyproject.toml, tests/test_agentSessions.py, documentation/agentSessions.md,
README navigation, release notes and the requirement records. Preserve
session-store formats and read-only discovery. Do not alter managed guidance or
unrelated commands. No architecture decision is required.

## Verification and handoff

Run pytest tests/test_agentSessions.py with coverage, the full OMP test suite,
Black check, runLinter on the module and git diff --check.

Report branch/commits, changed files, acceptance evidence, remaining review,
risks and suite impact (OMS, OMV, OMP, OMPR).
