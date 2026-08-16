# Current Development Increment

## Status

Active

## Objective

Implement AI Agent Portability and Context Integrity (Increment 1: vendor-neutral AGENTS.md, direct pointer shims, project-owned scaffolding, and deterministic agentCheck validator).

## Governing References

- Primary Reference: `documentation/agentPortabilityDesign.md`
- Supporting ADRs: None
- Milestone / Roadmap: Release 0.4b

## Scope

- Vendor-neutral AGENTS.md entry point and direct pointer shims (CLAUDE.md, .github/copilot-instructions.md).
- Scaffolding of project-owned documentation templates (architecture.md, currentIncrement.md, project.yaml, roadmap.md, requirements and ADR templates).
- Deterministic relational validator `agentCheck` to evaluate agent-readiness and detect broken links, status contradictions, and unedited placeholders.
- Synchronization specifications in `syncAgentInstructions.py` updated to sync pointer shims rather than duplicate instruction bodies.

## Explicit Exclusions

- Unified CLI framework rewrite (e.g. `omp` subparser umbrella).
- GitHub Projects / Kanban integration.
- Portfolio-wide management tooling.

## In-Progress Tasks

- [x] Create branch `release/0.4b`
- [x] Add `CLAUDE.md` and `.github/copilot-instructions.md` direct shims
- [x] Implement `agentCheck.py` validation engine and CLI entry point
- [x] Update `manageProject.py` with project-owned templates and non-destructive update guards
- [x] Update `syncAgentInstructions.py` sync specs
- [x] Add comprehensive test suite in `tests/test_AgentCheck.py` and update integration tests
- [ ] Run full test suite and validation checks

## Relevant Files & Components

- Implementation: `organiseMyProjects/agentCheck.py`
- Scaffolding: `organiseMyProjects/manageProject.py`
- Sync: `syncAgentInstructions.py`
- Tests: `tests/test_AgentCheck.py`
- Documentation: `documentation/agentPortabilityDesign.md`

## Verification Procedures

```bash
pytest
python tests/agentCheck.py
```

## Definition of Done

1. All unit and integration tests in `pytest` pass.
2. `python tests/agentCheck.py` passes with zero failures.
3. Documentation and sync specifications match the agreed direct-pointer architecture.

## Handoff & Unresolved Context

- Implementation of Increment 1 is in place on branch `release/0.4b`.
