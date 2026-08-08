Requirement: 001 — project/requirements/features/001-projectRoleAwareUpdates.md
Role: implement

Read the authoritative requirement and all applicable repository instructions
before changing anything. Deliver every acceptance criterion in requirement
001 while preserving its exclusions. Do not infer a UI, application entry
point, or source layout from missing metadata. If role metadata or the
ownership-policy mechanism requires a consequential design choice, propose or
create the applicable ADR and link it from the requirement before depending on
that choice.

Limit changes to `createProject` behaviour and templates, directly related
documentation, requirement or ADR traceability, and tests and fixtures needed
to prove the criteria. Preserve unrelated project-owned content.

Verify with:

- the focused `createProject` unit and integration tests;
- the full pytest suite;
- a subprocess check proving generated pytest settings are loaded; and
- an import check performed in a read-only or sandboxed location.

If the requirement is ambiguous or its outcome must change, stop and report the
decision needed. Do not infer new scope.

Handoff with:

- files changed and why;
- an acceptance-criterion-to-evidence mapping;
- commands run and results; and
- assumptions, risks, decisions, and unresolved items.
