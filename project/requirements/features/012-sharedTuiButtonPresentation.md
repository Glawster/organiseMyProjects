# 012: Shared TUI button presentation

## Status

ToDo — planned for OMP 0.8.

## Outcome

As a maintainer of TUI-based applications, I need a shared button presentation convention so that TUI projects use consistent button dimensions, spacing, and styling without duplicating screen-specific overrides.

## Context

OMP-managed projects increasingly use Textual-based terminal user interfaces. Button presentation has started to diverge between projects and screens, with some applications applying local height, padding, border, foreground, and background overrides.

The shared OMP stylesheet should define the standard button presentation for TUI-based applications so that individual screens do not need to restate the same layout rules. `mailAgent` is the immediate adoption case: execution-screen-specific button height/border overrides should be removed once the shared style provides the required presentation.

`clannEolas` deliberately uses its own stylesheet and is therefore outside the shared-style adoption scope unless a later requirement changes that decision.

## Scope

- Define the shared TUI button convention in the OMP-managed shared stylesheet/guidance.
- Standard TUI buttons must be exactly **one terminal row high**.
- Button styling must avoid vertical padding or borders that cause the button label to be clipped or vertically misaligned.
- Buttons using the shared style must use a consistent foreground/background presentation across the application unless a deliberate semantic variant is defined.
- Adjacent buttons that form one logical control group should use equal sizing where appropriate.
- Adjacent buttons in the same horizontal group should have a **one-column gap** between them.
- Button groups should have **one row of spacing** between the group and surrounding content or frame boundaries.
- Prefer central shared styling over screen-specific button height, border, padding, foreground, or background overrides.
- Update the shared TUI styling documentation so downstream projects can rely on one canonical convention.
- `mailAgent` should remove execution-screen-specific button height/border overrides when adopting the shared convention.
- Preserve application-specific button variants only when they serve a clear semantic purpose and do not break the shared sizing/spacing convention.

## Out of scope

- Reworking `clannEolas` styling. It intentionally uses its own stylesheet and remains exempt from shared OMP TUI styling for this requirement.
- Mandating equal width for every button regardless of context; equal sizing applies where adjacent buttons are intended to read as one control group.
- Changing non-button TUI layout conventions except where one-row spacing is required around a button group.

## Acceptance criteria

1. Given an OMP-managed TUI application using the shared stylesheet, when a standard button is rendered, then the button occupies one terminal row in height and its label is not clipped.
2. Given adjacent buttons in one logical horizontal group, when rendered with the shared style, then they use equal sizing where appropriate and have one column of space between neighbouring buttons.
3. Given a button group inside a panel/frame/content region, when rendered, then there is one row of spacing between the group and surrounding content/frame boundaries.
4. Given the shared stylesheet, when standard buttons are rendered, then foreground/background presentation is consistent across screens unless an explicit semantic variant applies.
5. Given an application screen that currently overrides button height, border, or vertical padding only to obtain the standard presentation, when it adopts the shared convention, then those local overrides can be removed without visual regression.
6. Given `mailAgent`, when the shared button style is adopted, then execution-screen-specific height/border overrides are removed and button presentation is supplied by the shared style.
7. Given `clannEolas`, when this requirement is implemented, then its deliberately separate stylesheet is not modified merely to conform to the OMP shared TUI button style.
8. Given future changes to the button convention, when the shared style is updated, then conforming TUI applications can receive the change without repeating screen-level styling edits.
9. Regression tests or style-level tests cover the shared button height, spacing, and clipping-safe presentation where practical.
10. The shared TUI styling documentation records the one-row height, no clipping-causing vertical padding/border, one-column adjacent gap, one-row surrounding spacing, and equal-group-sizing conventions.

## Dependencies and decisions

- Depends on the OMP-managed shared stylesheet mechanism (`myStyles.css`) used by conforming TUI applications.
- `clannEolas` remains an explicit exception because it deliberately owns a separate stylesheet.

## Verification

- Inspect/render a representative shared-style TUI button group.
- Run project tests for OMP shared styling.
- Run `manageProject update` against a representative TUI project and confirm the shared style is distributed correctly.
- Verify `mailAgent` no longer requires execution-screen-specific height/border overrides after adoption.

## Change history

- 2026-10-14: created from cross-repository TUI button styling discussion; establishes the shared one-row button convention, standard spacing, and `mailAgent` adoption while exempting `clannEolas`.
