# Requirement 033 implementation prompt

Implement requirement 033 ([Obsolete local linter copy enforcement](../features/033-obsoleteLinterCopyEnforcement.md)).

## Goal

Enforce requirement 010 outcomes by detecting obsolete local linter wrappers and
legacy copies in check/update flows.

## Mandatory outcomes

- Add deterministic check findings while obsolete local linter files remain.
- Recognise simple runLinter wrapper scripts that only forward to installed
  package entry points.
- Keep update/check guidance consistent and actionable.

## Constraints

- Do not rewrite arbitrary custom scripts with project-specific behaviour.
- Avoid false positives for unrelated helper scripts.

## Deliverables

- Check/update logic changes for obsolete-copy detection.
- Tests covering wrapper detection, non-wrapper safety, and finding clearance.
