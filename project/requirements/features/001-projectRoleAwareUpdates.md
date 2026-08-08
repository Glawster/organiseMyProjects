# 001: Project-role-aware updates

## Status

ToDo

## Outcome

As a maintainer of an established Python project, I need `createProject`
updates to respect the project's role and ownership boundaries so that shared
standards can be adopted without damaging its entry point, layout, tooling, or
local configuration.

## Context

The current update workflow can apply application and UI assumptions to an
existing packaged command-line project. An update needs an explicit execution
gate, a truthful preview, consistent file-ownership rules, and integration
coverage representative of an established repository such as
`organiseMyProjects` itself. Missing metadata is not evidence that a project
has a UI.

## Scope

- Detect and respect the project role: library, packaged CLI, standalone
  application, and optional UI.
- Preserve `--confirm` as the update execution gate and clearly distinguish
  simulated changes from applied changes.
- Define and enforce one ownership policy for every deployed file.
- Make shared templates project-neutral and safe to import.
- Align both update and new-scaffold output with the managed project standards.
- Add integration coverage for a representative established packaged CLI.

## Out of scope

- Adding UI capability, changing an established project's role, or replacing
  its source layout unless explicitly requested.
- Broad rewrites of project-owned configuration.
- Product-specific defaults in shared templates.

## Acceptance criteria

1. Given a library, packaged CLI, standalone application, or project with an
   explicitly selected UI, when `createProject` plans an update, then the plan
   is appropriate to that role; absence of role or UI metadata never causes a
   UI to be inferred.
2. Given an update invocation without `--confirm`, when it runs, then no update
   is applied; user documentation identifies
   `createProject --update --confirm` as the command that applies changes.
3. Given a dry run that plans file changes, when output is displayed, then each
   planned action says `would create` or `would update`, and the command ends
   with an unambiguous summary stating that the update was simulated and no
   changes were applied.
4. Given an established packaged CLI, when it is updated without an explicit
   layout or UI request, then the update does not add `main.py`,
   `src/globalVars.py`, UI templates, or a new source layout.
5. Given shared scaffold templates, when their generated content is inspected,
   then it contains no product-specific iCloud defaults.
6. Given existing pytest, pre-commit, environment, editor, or dependency files,
   when an update runs, then those files are treated as project-owned and are
   preserved except for a narrow merge through an explicitly identified
   managed block; when such a file is missing, the applicable scaffold may
   create it.
7. Given generated pytest INI configuration, when pytest loads the generated
   project, then the configuration is valid `[pytest]` INI and an automated
   test demonstrates that pytest actually loads its settings.
8. Given any file deployed by `createProject`, when its deployment rule is
   reviewed, then exactly one policy is declared and enforced: managed
   overwrite, managed-block merge, or project-owned missing-only.
9. Given a read-only or sandboxed environment, when command and deployed-linter
   modules are imported, then import succeeds without creating a log file.
10. Given an integration fixture representing an established packaged CLI such
    as this repository, when a confirmed update is run twice, then the second
    run is idempotent and both runs preserve the console entry point, package
    layout, pytest test discovery, and local configuration.
11. Given a newly generated scaffold, when its managed project files are
    inspected, then it generates `pyproject.toml`, `environment.yml`, and the
    requirements and ADR bootstrap where applicable; any item that remains
    opt-in is explicitly documented with the reason.

## Dependencies and decisions

- The managed standards in `.github/repositoryLayout.md` and
  `.github/requirementsManagement.md`.
- An architecture decision may be needed to define role metadata and the
  ownership-policy manifest; pending refinement.

## Verification

- Unit tests for role classification, dry-run wording, confirmation gating,
  ownership policies, template neutrality, and import-time filesystem effects.
- A subprocess test proving pytest loads the generated `[pytest]` settings.
- Integration tests using an established packaged-CLI fixture, including two
  consecutive confirmed updates and assertions for preserved files and
  behaviour.
- Documentation review of update and scaffold commands and opt-in exceptions.

## Traceability

- Implementation: pending
- Tests: pending
- Documentation: pending
- Pull request: pending
- Agent runs: None

## Change history

- 2026-08-04: created — captured the upstream `createProject` follow-up
  requested for `organiseMyProjects`.
