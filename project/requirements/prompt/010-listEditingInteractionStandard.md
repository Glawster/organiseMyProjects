# Requirement: 010 — project/requirements/features/010-listEditingInteractionStandard.md

Role: implement and verify for OMP 0.8.

Read the authoritative requirement, `documentation/listEditingInteraction.md`, the existing UI-organisation guidance in `.github/agent-instructions.md`, managed-file ownership/update code, `manageProject check`, and the packaged linter tests before changing behaviour.

Implement REQ-010 so the list-editing standard is not merely documentation:

- keep `documentation/listEditingInteraction.md` as the canonical guide;
- add an explicit agent-instruction pointer requiring the guide to be read before implementing or reviewing list/table interfaces;
- deploy the guide and pointer through `manageProject create` and `manageProject update` using existing managed-file ownership rules;
- make update idempotent and preserve project-owned content;
- make `manageProject check` detect missing/stale managed guide content or missing required agent reference;
- ensure confirmed update followed immediately by check is clean for deficiencies update owns;
- add only low-false-positive static UI checks that can be derived reliably;
- keep ambiguous/subjective UX rules as guidance rather than hard lint errors;
- preserve framework independence and UI/business-logic separation.

The interaction standard must cover list-first views, contextual compact editing, `a`/`e`/`d`, navigation, Enter/Esc/Space semantics, discoverable bindings, selectors for known values, minimal free text, `Add...` handling for new choices, hidden irrelevant controls, deliberate truncation/scrolling, consistent peer-button sizing, destructive-action confirmation and concise feedback.

Add focused regression tests for create/update/check/idempotence/ownership and any new linter rules. Include both compliant and non-compliant UI examples for static checks.

Run the full applicable verification before handoff, including:

- focused tests for the new managed guide and agent reference;
- focused linter tests;
- `pytest`;
- `runLinter`;
- `black --check .`;
- `ruff check .`;
- `git diff --check`.

Do not claim checks were run unless they were actually executed.
