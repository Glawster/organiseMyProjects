# 010: List editing interaction standard and enforcement

## Status

ToDo — planned for OMP 0.8.

## Outcome

Define, distribute and enforce a consistent interaction model for list- and table-driven applications managed by OMP, with keyboard-efficient editing, minimal free-text entry, compact contextual editors and deterministic project checks.

## Context

mailAgent exposed a recurring usability problem in Textual/TUI list editing: large permanent forms reduced table space, peer buttons had inconsistent widths, long values could bleed into adjacent areas, known values were retyped instead of selected, and common edit actions were not consistently exposed through single-key controls.

The interaction model is intended to become a shared OMP standard rather than remain a project-specific fix.

## Scope

### Canonical guide

- Maintain `documentation/listEditingInteraction.md` as the canonical user-interface interaction guide.
- The guide applies by default to list- and table-driven interfaces, especially Textual/TUI applications, while allowing deliberate exceptions for forms, wizards, canvases and other specialised interfaces.
- The standard must define list-first presentation, compact contextual editing, minimal typing, selection from known values, discoverable keyboard controls, consistent peer-action layout, safe deletion and concise feedback.

### Agent awareness

- `.github/agent-instructions.md` must explicitly tell implementation and review agents to read `documentation/listEditingInteraction.md` before implementing or reviewing list- or table-based interfaces.
- The instruction must be part of the OMP-managed agent guidance distributed to downstream repositories.
- Agents must not be expected to discover the guide only through a README link.

### manageProject distribution

- `manageProject create` must deploy the canonical guide and corresponding agent instruction to newly created managed projects.
- `manageProject update` must add or refresh the OMP-managed guide and agent instruction in existing managed projects according to the normal managed-file ownership rules.
- Updates must preserve project-owned content and remain idempotent.
- The OMP source repository remains the canonical source; downstream copies must not become independent implementations of the standard.

### manageProject validation

- `manageProject check` must verify that the managed guide exists where required and that the agent instructions contain the required reference.
- Deterministic missing or stale managed guidance should be reported as a check finding.
- A successful confirmed update followed immediately by check must not report a deficiency that update itself is responsible for correcting.

### Interaction model

For list/table editing interfaces, the default interaction model must include, where applicable:

- list/table as the primary view;
- current row as the active item;
- `a` for add, `e` for edit and `d` for delete/remove;
- arrow keys for navigation;
- `Enter` for open/select/confirm where unambiguous;
- `Esc` for cancel/back;
- `Space` for toggles where appropriate;
- context-sensitive help/footer that exposes the active bindings;
- dropdown/select/cycle controls for values already known to the application;
- free-text entry only for genuinely new values;
- safe inferred values pre-filled when available;
- explicit `Add...` handling when a selector also permits a new value;
- compact contextual editors rather than permanently stacked large forms;
- hidden or read-only controls for fields that do not need editing;
- consistent widths/alignment for peer action buttons;
- deliberate column sizing/truncation and internal scrolling so long content does not bleed into neighbouring controls;
- confirmation for destructive or difficult-to-reverse operations;
- concise action feedback and preservation of user input after validation errors.

### Linter and static checks

- OMP should derive static checks only where the rule can be determined reliably from source.
- Initial UI checks should be advisory warnings unless the implementation can establish a deterministic violation with low false-positive risk.
- Candidate checks include:
  - a list/table editor that exposes no discoverable keyboard action bindings for applicable common operations;
  - UI modules that combine list rendering, editing, persistence and unrelated responsibilities beyond the existing UI-organisation guidance;
  - repeated peer action buttons with inconsistent shared sizing/styling when this can be determined reliably;
  - known-choice fields implemented as unconstrained free text only when the valid finite choice set is explicit in the same static context.
- Linter rules must not attempt to judge subjective qualities such as whether a screen is visually attractive.
- Rules with significant ambiguity must remain guidance rather than hard lint failures.

### Framework independence

- The interaction principles are framework-independent.
- Textual-specific implementations may use Textual bindings, `DataTable`, `Select`, modals or widgets, but the canonical guide must describe behaviour rather than require one framework API.
- Core/business logic must remain separate from UI implementation.

## Out of scope

- Automatically rewriting existing UI code to comply with the standard.
- Pixel-level or screenshot-based visual linting.
- Requiring every application to use identical widgets or styling libraries.
- Treating every absence of `a`, `e` or `d` as an error when the corresponding action is not meaningful.
- Replacing project-specific interaction requirements where a deliberate specialised interface is documented.

## Acceptance criteria

1. `documentation/listEditingInteraction.md` exists as the canonical OMP 0.8 guide and describes the required list-first interaction model.
2. `.github/agent-instructions.md` explicitly requires agents to read that guide when implementing or reviewing list/table interfaces.
3. `manageProject create` deploys the guide and agent reference to a newly created managed project.
4. `manageProject update` deploys or refreshes the managed guide/reference in an existing project without overwriting project-owned content.
5. Re-running `manageProject update` is idempotent when the managed files are already current.
6. `manageProject check` reports a deterministic finding when the managed guide or required agent reference is missing or stale.
7. A confirmed update followed by check does not report deficiencies that the update was responsible for correcting.
8. The guide standardises `a`/`e`/`d`, navigation, Enter/Esc/Space semantics and discoverable active bindings where those actions apply.
9. The guide requires selectors/dropdowns/cycling for known finite values and reserves free text mainly for genuinely new values.
10. The guide requires contextual compact editors, hides irrelevant controls, and keeps the list/table as the primary use of screen space.
11. The guide requires long table values to truncate/scroll deliberately rather than bleed into adjacent controls, and peer buttons to use consistent sizing/alignment.
12. Destructive actions require confirmation appropriate to their reversibility.
13. Any implemented linter rules distinguish deterministic structural checks from subjective UX guidance and avoid unacceptable false positives.
14. Static UI checks are covered by focused regression tests, including compliant and intentionally non-compliant examples.
15. Existing OMP tests and managed-file ownership guarantees continue to pass.

## Verification

At implementation time, verify with the focused create/update/check tests, focused UI-linter tests, and the normal OMP release validation, including:

```bash
pytest
runLinter
black --check .
ruff check .
git diff --check
```

Do not claim a verification step has passed unless it was actually run.

## Dependencies and decisions

- Existing OMP managed-file ownership and update semantics.
- Existing UI file-organisation guidance in `.github/agent-instructions.md`.
- Existing packaged `runLinter` direction for OMP 0.8.
- No new architecture decision is required unless implementation introduces a new managed-file ownership category or framework dependency.

## Change history

- 2026-10-07: created from mailAgent filing-panel UX review and the decision to standardise list editing, agent discovery, manageProject distribution/checking and derivable lint rules across OMP-managed projects.
