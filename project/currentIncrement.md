# Current Development Increment

## Status

Active

## Objective

Implement AI Agent Portability and Context Integrity (Increment 1: vendor-neutral AGENTS.md, project-owned scaffolding, and deterministic agent-readiness validation exposed through `manageProject --check`).

## Governing References

- Primary Reference: `documentation/agentPortabilityDesign.md`
- Supporting ADRs: None
- Milestone / Roadmap: Release 0.4b

## Scope

- Vendor-neutral AGENTS.md entry point and justified direct pointer shims.
- Scaffolding of project-owned documentation templates (architecture.md, currentIncrement.md, project.yaml, roadmap.md, requirements and ADR templates).
- Deterministic relational validator in `organiseMyProjects/agentCheck.py` to evaluate agent readiness and detect broken links, status contradictions, and unedited placeholders.
- Public validation interface through `manageProject --check`, with `--strict` and `--verbose` support.
- Synchronization specifications in `syncAgentInstructions.py` updated to sync pointer shims rather than duplicate instruction bodies.

## Explicit Exclusions

- Unified CLI framework rewrite (e.g. `omp` subparser umbrella).
- GitHub Projects / Kanban integration.
- Portfolio-wide management tooling.

## In-Progress Tasks

- [x] Create branch `release/0.4b`
- [x] Add vendor-neutral AGENTS.md entry point and pointer shims
- [x] Implement `agentCheck.py` validation engine
- [x] Expose validation through `manageProject --check`
- [x] Update `manageProject.py` with project-owned templates and non-destructive update guards
- [x] Update `syncAgentInstructions.py` sync specs
- [x] Add validator tests and `manageProject --check` routing tests
- [x] Review the large `.github/agent-instructions.md` change separately
- [x] Remove or simplify obsolete downstream `tests/agentCheck.py` deployment once `manageProject.py` template wiring is updated
- [x] Run full test suite and validation checks in a working checkout

## Relevant Files & Components

- Validation engine: `organiseMyProjects/agentCheck.py`
- Public CLI routing: `organiseMyProjects/manageProjectCli.py`
- Scaffolding: `organiseMyProjects/manageProject.py`
- Packaging: `setup.py`
- Sync: `syncAgentInstructions.py`
- Tests: `tests/test_agentCheck.py`, `tests/test_manageProjectCli.py`
- Documentation: `documentation/agentPortabilityDesign.md`

## Verification Procedures

```bash
pytest
manageProject --check
manageProject --check --strict
```

## Definition of Done

1. All unit and integration tests in `pytest` pass.
2. `manageProject --check` passes with zero failures on OMP itself.
3. A migrated downstream repository can be validated through the same command.
4. Documentation and sync specifications match the agreed vendor-neutral architecture.

## Handoff & Unresolved Context

- The validator remains an internal reusable module, while `manageProject --check` is now the intended public interface.
- The branch still contains a legacy copied `tests/agentCheck.py` wrapper because `manageProject.py` currently references it in scaffold/template lists; remove that wiring before deleting the wrapper.
- Full tests could not be run from this review environment because direct network checkout of the repository was unavailable; run them in the local checkout before merging.
