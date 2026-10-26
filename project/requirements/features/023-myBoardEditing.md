# 023: Requirement board editing

## Status

InProgress

## Outcome

As a developer maintaining project requirements, I need to edit a requirement's
metadata and prose through myBoard so that its authoritative record stays
accurate without manually coordinating related documents.

## Context

Requirement 021 can create and move requirements but deliberately excludes
editing their prose. Changing a title currently risks leaving the feature
record, requirements index and current increment inconsistent.

## Scope

- Add a scriptable `myBoard edit NUMBER` command for selected requirement
  metadata and prose sections.
- Support replacement of the title, index description, Outcome, Context,
  Scope, Out of scope, Acceptance criteria, Dependencies and decisions, and
  Verification sections.
- Default to a dry-run and require `--confirm` before writing.
- Keep the feature record, requirements index and existing increment or
  backlog bullet aligned when a title or description changes.
- Preserve the permanent requirement ID and lifecycle status, and add a
  dated change-history entry to a changed record.

## Out of scope

- Editing Status or moving cards; use the existing `myBoard move` workflow.
- Renaming requirement files or changing requirement IDs.
- A Textual form for editing prose inside the board.
- Editing prompts, ADRs, pull requests or Git history.

## Acceptance criteria

1. Given an existing requirement, when `myBoard edit` supplies one or more
   editable fields with `--confirm`, then its record contains the replacements
   and a dated change-history entry.
2. Given an edited title or description, when the command is confirmed, then
   the matching requirements-index row is updated and an existing increment or
   backlog bullet uses the new title.
3. Given an edit without `--confirm`, when the command completes, then it
   reports the planned files and leaves every file unchanged.
4. Given no editable fields, blank values, or an index-unsafe title or
   description, when editing is requested, then the command fails with a
   clear error and leaves files unchanged.
5. Given an edit, when it is confirmed, then the requirement ID and Status
   remain unchanged.

## Dependencies and decisions

- Builds on requirement 021's `requirementBoard` plan/apply change boundary.
- No ADR required.

## Verification

- pytest tests/test_myBoard.py
- runLinter on organiseMyProjects/requirementBoard.py and
  organiseMyProjects/myBoard.py
- `myBoard edit 023 --outcome "As a ..."`, both with and without `--confirm`

## Change history

- 2026-10-25: created — follow-up requirement for myBoard editing.
