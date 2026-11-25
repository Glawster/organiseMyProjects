# Requirement 031 implementation prompt

Implement requirement 031 ([Installed managed-content parity](../features/031-installedManagedContentParity.md)).

## Goal

Make installed-wheel execution paths deploy the same managed file set as source
checkout execution, with update/check and sync/update parity for managed files.

## Mandatory outcomes

- Resolve managed files from packaged resources, not repository-relative
  assumptions.
- Ensure install/package data includes every managed file that update and sync
  are expected to deploy.
- Align update and sync managed file lists for each applicable role.
- Remove stale references to non-existent managed template files.
- Add regression coverage for installed-wheel update/check behaviour.

## Constraints

- Preserve existing managed ownership semantics.
- Keep deployment deterministic and idempotent.
- Preserve dry-run behaviour.

## Deliverables

- Implementation updates in managed deployment/sync source resolution paths.
- Packaging/manifest updates as needed for managed resources.
- Tests proving installed-wheel and source-checkout parity.
