# Requirement 032 implementation prompt

Implement requirement 032 ([Environment Python pin preservation](../features/032-environmentPythonPinPreservation.md)).

## Goal

Ensure managed environment merges do not widen stricter project Python pins and
remain idempotent.

## Mandatory outcomes

- Detect and reconcile existing Python constraints during merge.
- Preserve stricter interpreter pins instead of replacing with broader managed
  defaults.
- Keep merge output stable across repeated updates.
- Document the interpreter ownership/precedence rule.

## Constraints

- Keep broader dependency merge behaviour unchanged unless required.
- Maintain deterministic merge output.

## Deliverables

- Environment merge logic updates.
- Focused tests for strict-pin retention and re-run stability.
- Documentation updates describing supported pin behaviour.
