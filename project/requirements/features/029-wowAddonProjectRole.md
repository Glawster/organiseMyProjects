# 029: WoW addon project role

## Status

InProgress

## Outcome

As a World of Warcraft addon maintainer, I need `manageProject` to scaffold and
update addon repositories that are driven by a root `.toc` and Lua sources,
without imposing Python-application packaging files that do not apply to addon
projects.

## Context

`manageProject` already supports standalone Python applications and runtime
deployment concerns. WoW addons have a different repository shape, release flow
and tooling (`luacheck`, `stylua`, `.pkgmeta`, flavour-specific `.toc`
metadata), so they require a dedicated project role.

## Scope

The implementation must add a dedicated `wow-addon` role with deterministic
create/update behaviour:

- `create --wow-addon --flavour retail|classic|forever` scaffolds addon-managed
  files and addon-specific quality tooling.
- `update` detects addon repositories by a root `.toc` and refreshes only files
  owned by the addon role.
- Addon repositories must not be forced into Python package scaffolding
  (`pyproject.toml`, `ompr/` runtime, `src/`, `main.py`).
- Managed docs and agent guidance must include addon-role instructions.

`migrate` must also be able to generate an addon `project.yaml` record using
addon metadata when a WoW addon is detected.

## Acceptance criteria

1. `manageProject create --wow-addon` creates addon scaffolding at repository
   root, including `.toc` and addon Lua entrypoint files.
2. Create supports flavour-specific `.toc` templates for `retail`, `classic`
   and `forever`.
3. Addon scaffolding includes managed addon tooling/configuration files:
   `.pre-commit-config.yaml`, `.luacheckrc`, `.stylua.toml`, `.pkgmeta`, and a
   wow environment file.
4. Addon create does not generate Python-application package/runtime files
   (`pyproject.toml`, `ompr/`, `src/`, Python UI templates).
5. `manageProject update` detects addon role from repository contents and uses
   addon-specific managed updates.
6. Addon update refreshes addon-managed files while preserving project-owned
   addon code.
7. `agentCheck` accepts addon lint command defaults when validating project
   metadata.
8. `manageProject migrate` writes addon `project.yaml` metadata (including
   version/description) using addon `.toc` data when available.
9. Managed documentation deployment includes a WoW addon guide and sync routing
   for addon repositories.
10. Automated tests cover create/update/migrate and metadata behaviour for addon
    repositories.

## Out of scope

- Changing existing non-addon project roles beyond what is required to keep
  behaviour stable.
- Introducing WoW gameplay features, addon business logic or release pipelines
  beyond scaffold support.

## Dependencies and decisions

- Reuses the existing role-detection pattern in `manageProject`.
- Treats a root `.toc` as the addon role discriminator for update/sync
  behaviour.
- Uses managed-content ownership rules already established for scaffold files.

## Verification

- Targeted tests for addon create/update/migrate and sync routing are required.
- Existing non-addon create/update tests remain green.
- Agent-readiness checks keep reporting known legacy requirement-template
  warnings and add no new warning classes.

## Change history

- 2026-11-14: Added as the next `release/0.10` increment to integrate the
  `feature/wow-addon` implementation stream.
