# 031: Installed managed-content parity

## Status

ToDo

## Outcome

As a maintainer using an installed OMPR release, I need `manageProject update`
and sync to deploy the same managed files as the source checkout so that update
followed by check never reports missing managed files that update should have
installed.

## Context

The OMPR 0.10 alignment review in organiseMyConda found that installed
`manageProject update` resolved managed sources from an incomplete
`site-packages` layout. Agent entry points and some documentation files were
missing from the installed record, while local source-driven update deployed
them. Remote sync file lists also differed from local update, creating
inconsistent managed outcomes across update paths.

## Scope

- Load managed source files from package data (for example `importlib.resources`)
  rather than assumptions about parent directories.
- Ensure install manifests include every managed file update and sync are
  expected to deploy, including agent entry-point files and managed docs.
- Remove stale references to non-existent managed template files.
- Align update and remote sync so they deploy the same managed file set for a
  given project role.
- Add regression coverage that exercises update/check from an installed wheel,
  not only a source checkout.

## Out of scope

- Redesigning managed ownership policy.
- Adding new managed-document categories beyond parity with current intended
  deployment.

## Acceptance criteria

1. Given OMPR is installed from a wheel, when `manageProject update` runs on a
   managed repository, then all required managed agent and documentation files
   are deployed the same as from a source checkout.
2. Given update completed successfully, when `manageProject check` runs, then
   it does not report deficiencies update itself was responsible for fixing.
3. Given repository or batch sync is run, when managed files are deployed, then
   the deployed file set matches local update for the same role.
4. Given package build/install validation runs, when managed templates are
   resolved, then no non-existent managed file reference is used.

## Dependencies and decisions

- Builds on requirement 002 runtime deployment ownership and update/check
  consistency commitments.

## Verification

- Add/update tests that validate managed deployment parity between source and
  installed-wheel execution paths.
- Verify update/check consistency and sync/update file-list parity.

## Change history

- 2026-11-25: created from OMPR 0.10 alignment review findings recorded in
  `organiseMyConda/project/reviews/2026-11-25-ompr010Alignment.md`.
