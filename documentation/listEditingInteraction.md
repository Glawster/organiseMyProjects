# List Editing Interaction Standard

## Purpose

This guide defines the default interaction model for applications that present and edit structured data as lists or tables.

The standard is intended for Textual/TUI applications first, but the interaction principles also apply to desktop and other list-driven interfaces where appropriate.

The goals are to:

- keep list screens compact and readable;
- minimise unnecessary typing;
- make common actions keyboard-efficient;
- prefer existing values over free-text entry;
- keep editing focused on the selected item;
- provide consistent controls across OMP-managed applications.

## List-first design

A list or table is the primary view of the data.

Users should be able to understand the current state by scanning the list without first opening an edit form.

The current row represents the active item. Editing controls should normally appear only when the user asks to add or modify an item.

Avoid permanently stacking large edit forms beneath a table when the same screen can instead use a compact contextual editor.

## Standard keyboard actions

Where the action is applicable, use these single-key bindings consistently:

```text
↑ / ↓    navigate rows
Enter    open, select or confirm the current item
Esc      cancel the current edit or return
Space    toggle the current boolean or selection

a        add
e        edit
d        delete or remove
```

Single-key actions should be preferred for common list operations when they do not conflict with normal text entry.

The footer or local help area should show the actions that are valid in the current context, for example:

```text
↑↓ Navigate   a Add   e Edit   d Delete   Enter Select   q Quit
```

Do not advertise actions that are unavailable in the current panel.

## Add workflow

Pressing `a` should start an add operation using the minimum fields required to create the new item.

The add editor should:

- use known context from the selected row or current panel;
- pre-fill safe inferred or suggested values;
- use dropdowns/selects for values already known to the application;
- request free text only for genuinely new values;
- keep the user in the current workflow rather than opening an unrelated screen;
- return to the list after a successful save.

For example, when adding a filing rule from an already selected domain, the domain should be supplied from the selected row rather than typed again.

## Edit workflow

Pressing `e` should edit the currently selected row.

The editor should be compact and contextual. It should display only the fields relevant to the selected item.

Prefer a short editing area such as:

```text
Parent:  [ Shopping ▼ ]     Folder: [ DPD          ]
Status:  Proposed

[ Save ]  [ Cancel ]
```

rather than a permanent full-screen form.

`Enter` should save or confirm when doing so is unambiguous. `Esc` should cancel without changing the stored value.

## Prefer selection over typing

If the application already knows the valid values, present them as a dropdown, select list, cycle control or similar constrained choice.

Examples include:

- folders;
- categories;
- mailboxes;
- roles;
- statuses;
- known destinations;
- existing parent groups;
- predefined policy values.

Do not require users to type an existing value exactly when it can be selected.

Free-text input should mainly be reserved for genuinely new values such as a new category name, folder name, label or identifier.

When a suitable value can be inferred safely, pre-fill it and allow the user to accept or modify it.

## Add-new values from a selector

When a selection control represents existing values but the user may create a new value, include an explicit `Add...` choice or equivalent action.

Selecting `Add...` should reveal only the input needed for the new value.

Creating the value should not cause unrelated side effects unless the workflow explicitly says it will. For planning or configuration screens, adding a proposed value should remain a configuration change until execution is separately approved.

## Cycling small value sets

For small ordered value sets, left/right arrow editing may be used instead of a dropdown when it is faster and clearer.

Examples:

```text
Out ← Auto → In
No  ← Auto → Yes
```

Direction must be consistent within the application. A positive or more-inclusive value should normally be reached in one direction and the negative or more-exclusive value in the other.

The current value must remain visible while cycling.

## Delete and remove actions

Pressing `d` should target the selected item only.

For destructive or difficult-to-reverse operations, require confirmation before applying the change.

A concise confirmation is preferred, for example:

```text
Delete rule for dpd.co.uk? [y/N]
```

Configuration-only removals may use lighter confirmation when the action is clearly reversible, but accidental deletion must still be difficult.

## Context-sensitive controls

Do not show fields that are irrelevant to the selected item.

For example, if an organisation domain has already been determined safely, show it as read-only text. Only display an organisation-domain input when clarification is actually required.

Similarly, uncommon operations such as exact-sender overrides should not dominate the normal editing workflow. They may be exposed as a secondary action, sub-panel or contextual editor.

## Layout guidance

The list should normally retain most of the available space.

The contextual editor should be compact and should not cause the table to become unusably small.

For terminal interfaces:

- tables should scroll internally;
- the cursor must remain visible while navigating;
- columns must have deliberate widths or truncation behaviour;
- long values must not bleed into adjacent controls or outside the panel;
- related action buttons should use consistent widths and alignment;
- explanatory prose should be concise and should not consume rows unnecessarily.

If a list plus editor does not fit comfortably, prefer a modal, dialog, dedicated edit pane or secondary screen over compressing both until neither is readable.

## Button consistency

Buttons representing peer actions should have consistent width and visual weight.

For example:

```text
[ Add Parent ]  [ Save Domain ]  [ Save Sender ]
```

Do not allow label length alone to produce visibly inconsistent button sizing when the buttons are part of the same action group.

The primary action may be visually distinguished, but layout should remain aligned.

## Status and feedback

The current item and edit state should be obvious.

Use concise status text near the editor, for example:

```text
Editing: dpd.co.uk · kathyMail · 2 messages
Status: Needs choice
```

After an action, give a short confirmation that describes what changed.

For planning-only operations, explicitly state that no underlying data or folders were changed when that distinction is important.

Avoid repeating the same safety explanation in multiple large blocks of text on the same screen.

## Validation

Validate user input as close as possible to the editing control.

When a value is invalid:

- keep the editor open;
- preserve the user's entered values;
- explain the specific problem;
- avoid clearing unrelated fields;
- do not partially apply the change.

## Accessibility and discoverability

Keyboard shortcuts must not be the only way to discover an action.

Expose the active bindings through a footer, help view, command palette or equivalent discoverable mechanism.

Applications should remain usable without requiring the user to memorise keys before first use.

## Scope and exceptions

This standard applies by default to list- and table-driven editing interfaces in OMP-managed projects.

A project may use a different interaction pattern when the task genuinely requires a form, wizard, graphical canvas or other specialised interface.

Any exception should be deliberate and should preserve the same goals: minimise typing, make actions discoverable, keep edits contextual and avoid unnecessary permanent forms.
