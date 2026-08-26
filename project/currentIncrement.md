# Current Development Increment

## Increment

0.5 — Release compliance

## Status

Active

## Requirement

OMP 0.5 release preparation.

## Objective

Bring OMP itself into compliance with its managed Python, packaging,
environment, testing, documentation and release standards.

## Scope

- Align Python 3.10 package metadata, Conda environment and CI.
- Make Black, Ruff, OMP Python lint and markup checks pass repository-wide.
- Remove stale product-specific and duplicate template implementations.
- Ensure `manageProject --update` is a no-op for the canonical OMP repository.
- Validate tests, agent readiness and package artifacts.

## Verification

- [ ] Full test suite
- [ ] Black and Ruff
- [ ] OMP Python and markup lint
- [ ] `python3 -m organiseMyProjects.manageProjectCli --check`
- [ ] Wheel build and metadata inspection

## Next

Complete final release validation and review the uncommitted compliance diff.
