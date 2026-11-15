# Requirement 029 implementation prompt

Implement requirement 029 ([WoW addon project role](../features/029-wowAddonProjectRole.md)).

## Goal

Add a dedicated `wow-addon` project role to `manageProject` that supports addon
repository scaffolding and managed updates without imposing Python application
runtime/package layout.

## Mandatory outcomes

- Add role detection and role-specific create/update handling for WoW addons.
- Add `--wow-addon` scaffolding with flavour support (`retail`, `classic`,
  `forever`).
- Ensure addon scaffolding includes addon managed files/tooling and excludes
  Python package/runtime scaffolding.
- Add migration support for addon `project.yaml` metadata from `.toc` where
  applicable.
- Update shared instructions/docs for addon projects.
- Add or update automated tests for addon role behaviour and edge cases.

## Constraints

- Preserve existing behaviour for non-addon roles.
- Keep file ownership semantics explicit and safe.
- Keep implementation deterministic and dry-run aware where applicable.
- Follow repository naming, lint and documentation conventions.

## Deliverables

- Updated implementation in `organiseMyProjects/`.
- Updated user/developer documentation and release notes entries.
- Requirement index and current increment tracking updates.
- Passing targeted tests for addon role behaviour.
