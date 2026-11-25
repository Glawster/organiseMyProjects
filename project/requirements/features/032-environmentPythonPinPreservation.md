# 032: Environment Python pin preservation

## Status

ToDo

## Outcome

As a project maintainer with an explicit interpreter policy, I need managed
environment merging to preserve or safely reconcile stricter Python pins so
that update does not silently widen interpreter constraints.

## Context

The OMPR 0.10 alignment review showed update removed `python=3.12` and appended
managed `python>=3.10`, effectively widening a stricter project policy. Because
the stricter pin lived outside the managed block, repeated updates could not
retain it.

## Scope

- Detect existing Python dependency entries during environment merge.
- Replace or reconcile interpreter pins in place without widening stricter
  constraints.
- Define deterministic precedence rules between managed baseline and
  project-specific stricter interpreter requirements.
- Document supported interpreter pin customisation semantics for managed
  environment files.

## Out of scope

- General redesign of environment merge for unrelated dependency classes.
- Managing multiple Python constraint lines with incompatible intent.

## Acceptance criteria

1. Given a managed environment file contains a stricter Python pin, when update
   runs, then the resulting interpreter constraint is not widened.
2. Given update runs repeatedly, when environment merge applies, then Python
   constraint output is stable and idempotent.
3. Given interpreter ownership rules are documented, when maintainers follow
   them, then update behaviour matches that documentation.

## Dependencies and decisions

- Builds on requirement 019 environment consistency intent.

## Verification

- Add regression tests for stricter-pin preservation and idempotent re-run
  behaviour.
- Add/update documentation assertions for interpreter-ownership rules.

## Change history

- 2026-11-25: created from OMPR 0.10 alignment review findings recorded in
  `organiseMyConda/project/reviews/2026-11-25-ompr010Alignment.md`.
