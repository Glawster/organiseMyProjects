# Requirement 037 implementation prompt

Implement requirement 037 ([Standalone Bash logUtils sourcing](../features/037-standaloneBashLogUtilsSourcing.md)).

## Goal

Give standalone Bash scripts a documented, directory-independent way to source
`logUtils.sh`, and make a failed lookup fail loudly instead of silently.

## Mandatory outcomes

- Document a standalone sourcing form that does not depend on the current
  directory or an activated Conda environment.
- Keep the `${applicationRoot}/ompr/logUtils.sh` form for OMP projects and state
  when each form applies.
- Define Bash fail-fast behaviour and the Bash equivalent of "No fallback
  logging".
- Align the section's wording with the chosen forms.

## Constraints

- Do not change the `logUtils.sh` API.
- Do not rewrite consumer scripts automatically.
- Edit the canonical guidance source, not deployed copies.

## Deliverables

- Updated Bash logging and fallback sections of the managed agent instructions.
- Bash tests covering acceptance criteria 1-3.
