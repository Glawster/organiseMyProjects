# Agent implementation workflow

## Purpose

organiseMyProjects (OMPR) must support projects that are increasingly implemented and reviewed with Codex, Grok, GitHub Copilot, and similar coding assistants. Agents follow project requirements and conventions; they do not replace them.

The suite-level workflow is defined by organiseMediaStudio. OMPR owns the project-management/tooling implications: discoverable project structure, managed conventions, linting, requirement traceability, and repeatable verification.

## Standard implementation loop

```text
Requirement / ADR
      |
      v
Codex implementation
      |
      v
Grok independent review
      |
      v
Codex fixes
      |
      v
Human/integration verification
      |
      v
Merge
```

Copilot may assist with focused local coding throughout the loop.

## OMPR responsibilities

OMPR should make this workflow easier without encoding vendor-specific implementation logic. `manageProject`, `runLinter`, templates, and managed project infrastructure should expose enough discovered project information and consistent verification conventions that any coding agent can work from the repository itself.

In particular OMPR should:

- discover source/package/test/documentation/requirement layouts where unambiguous;
- keep project configuration focused on policy and overrides rather than duplicated observable state;
- make required verification commands discoverable from repository documentation/configuration;
- preserve requirement and ADR locations consistently;
- support traceability from requirements to implementation, tests, pull requests, and agent runs where the project uses that metadata;
- detect stale managed conventions when suite architecture changes;
- avoid requiring an agent to know private historical conventions that can be represented in the repository.

## Required implementation/review report

A substantial agent run should report:

1. requirement/ADR addressed;
2. branch and commits;
3. materially changed files;
4. tests added/changed;
5. verification commands/results;
6. unmet acceptance criteria;
7. unresolved risks/ambiguities;
8. proposed requirement/ADR changes;
9. OMS/OMV/OMP/OMPR impact considered.

## Architecture and requirement authority

When code and documentation conflict, the agent must surface the conflict. It must not silently alter architecture, weaken safety boundaries, or invent project policy. Accepted changes to conventions should be documented first and OMPR should then be checked for required updates to discovery, scaffolding, `manageProject`, `runLinter`, templates, or validation.

## Relationship to REQ-008

REQ-008 project structure discovery is a prerequisite for making agent workflows portable across repositories. Agents should be able to inspect a repository and obtain most observable project facts without bespoke prompts describing its layout.

The long-term goal is that a freshly invoked coding/review agent can determine from the repository itself:

```text
what the project is
where its code lives
where requirements and ADRs live
which conventions are managed
how to test it
how to lint it
what branch/work item is active
what safety/architecture constraints apply
```

User intent, policy, and ambiguous decisions remain explicit rather than inferred silently.

## Suite impact rule

Changes to suite architecture or project conventions require an explicit impact check for OMS, OMV, OMP, and OMPR. Not every change requires edits in every repository, but OMPR must be considered whenever package layout, requirements structure, linting, managed infrastructure, development workflow, or shared conventions change.
