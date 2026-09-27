# 008: Project structure discovery

## Status

ToDo

## Outcome

As a project maintainer, I need organiseMyProjects to discover observable project structure and tooling before requiring configuration so that `manageProject`, `runLinter`, scaffolding, and project checks adapt safely to real repositories instead of assuming one package layout.

## Principle

OMPR follows the organise-suite `Discovery before configuration` principle:

```text
DISCOVER -> INFER -> REVIEW -> POLICY -> PLAN -> APPLY
```

Configuration records intent and overrides. It should not duplicate repository facts that can be established reliably from authoritative project files and the filesystem.

## Discoverable project model

OMPR should discover where practical:

- project language/runtime and packaging system;
- Python package/module layout, including packaged and `src/` layouts;
- `pyproject.toml` and other authoritative build/package metadata;
- test roots and test tooling;
- documentation roots;
- project requirements/ADR/review structure;
- GUI/UI framework and UI source locations;
- formatter, linter, pre-commit, and test configuration;
- build/package/release tooling;
- Git repository and branch conventions that can be observed safely;
- existing OMPR-managed infrastructure and its version/state;
- project role where evidence is sufficient, while preserving an explicit override for ambiguous projects.

REQ-005 runLinter source discovery is an existing specialised example of this broader requirement and should converge on the common project-discovery model rather than grow a separate set of layout assumptions.

## `project.yaml`

`project.yaml` should increasingly contain policy, intent, and explicit overrides rather than a duplicate description of the repository.

For example, an unambiguous package directory, tests directory, or documentation directory should normally be discovered. Configuration is appropriate where discovery is ambiguous, the repository deliberately departs from convention, or the user wants to override the inferred result.

## `manageProject`

`manageProject create`, `update`, and `check` shall consume the same discovered project model. An existing raw project should be inspectable and adoptable without requiring the user to recreate it merely to establish discoverable structure.

Updates must distinguish between:

- discovered user/project structure;
- user policy/overrides;
- OMPR-managed infrastructure.

OMPR must not overwrite user-owned project structure merely because it differs from a default template.

## Suite maintenance responsibility

OMPR is part of the organise-suite architecture and must be considered when OMS, OMV, or OMP changes conventions that affect project management, package layout, requirements/documentation structure, linting, shared themes, managed infrastructure, or development tooling.

A suite convention change need not always modify OMPR, but an OMPR impact check is required.

## Acceptance criteria

1. Given an existing Python project, OMPR can discover its package/source layout without assuming `src/` or a package-at-root layout.
2. Tests, documentation, requirements, UI/tooling, and managed infrastructure are discovered when authoritative evidence is available.
3. `manageProject create`, `update`, and `check` use a common project-discovery model rather than independent layout guesses.
4. `project.yaml` is not required to restate unambiguous discoverable paths.
5. Explicit user overrides take precedence over inference.
6. Ambiguous role/layout discovery is reported rather than silently forced.
7. Existing user-owned structures are not destructively rewritten merely because they differ from a template.
8. REQ-005 source discovery can be represented through the broader discovery model.
9. Changes to organise-suite conventions include an OMPR impact check.
10. Tests cover multiple package layouts and raw/unmanaged as well as OMPR-managed projects.
