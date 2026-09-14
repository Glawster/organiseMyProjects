# 008: Existing project scaffold consistency

## Status

Completed

## Outcome

Existing repositories can onboard through update without missing OMP-standard
files being reported immediately by check.

## Context

Reported for niwffWebsite: update succeeded but ENT-003, DOC-001 and INC-001
reported missing context files. Create requires a new directory.

## Scope

Seed missing README, project-specific instructions and idle increment context.
Explain project-owned setup and verification work. Apply missing-only ownership
and dry-run protection across detected project roles.

## Out of scope

Changing create to accept existing directories, inferring application code or
inventing project-specific test commands.

## Acceptance criteria

1. Git init, confirmed update and check produce no missing standard-file findings.
2. Existing context files are preserved byte-for-byte and reruns are idempotent.
3. Dry-run reports additions without writing files.
4. Successful update followed by check reports no deficiency update is responsible
   for correcting; remaining project-owned work is explicitly explained.

## Dependencies and decisions

- [File ownership policies](../../adr/001-fileOwnershipPolicies.md).

## Verification

`tests/test_updateScaffold.py` exercises real update/check composition across
empty, Node-marked, Python package and standalone repositories, preservation,
idempotence and dry-run behaviour.

## Change history

- 2026-09-14: Created from the OMP 0.8 onboarding consistency request.
