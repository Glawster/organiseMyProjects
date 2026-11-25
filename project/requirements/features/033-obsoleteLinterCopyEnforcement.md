# 033: Obsolete local linter copy enforcement

## Status

ToDo

## Outcome

As a maintainer updating managed projects, I need check/update to detect and
guide removal of obsolete local linter copies (including simple wrappers) so
that requirement 010 outcomes are enforced in practice.

## Context

The OMPR 0.10 alignment review found legacy `tests/runLinter.py` wrappers and
local `tests/guiNamingLinter.py` copies remained indefinitely when not
byte-identical to managed templates. Update marked them ambiguous and kept them,
while check did not flag the leftovers.

## Scope

- Extend check to report deterministic findings while obsolete local linter
  wrapper/copy files are present.
- Recognise wrapper forms whose only purpose is invoking installed
  `organiseMyProjects.runLinter` and provide deterministic handling.
- Align update/check messaging with requirement 010 so projects can converge on
  the package-provided linter path.

## Out of scope

- Broad static analysis of arbitrary test helpers unrelated to linter
  de-duplication.
- Automatic rewrite of complex custom linter scripts with project-specific
  behaviour.

## Acceptance criteria

1. Given a project contains `tests/runLinter.py` or
   `tests/guiNamingLinter.py` legacy local copies, when check runs, then it
   reports a deterministic finding.
2. Given a local `tests/runLinter.py` is a simple wrapper to the installed
   linter, when update/check evaluate it, then it is recognised as obsolete
   wrapper behaviour.
3. Given obsolete local copies are removed or migrated to package usage, when
   check reruns, then the related findings clear.

## Dependencies and decisions

- Directly extends requirement 010 policy intent.

## Verification

- Add focused tests for wrapper detection, non-wrapper safety, and check
  findings.
- Validate update/check guidance consistency for obsolete linter-copy cases.

## Change history

- 2026-11-25: created from OMPR 0.10 alignment review findings recorded in
  `organiseMyConda/project/reviews/2026-11-25-ompr010Alignment.md`.
