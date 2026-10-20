# 020: Documentation completeness checks

## Status

ToDo

## Outcome

As an OMPR user, I need `manageProject --check` to report living guides missing
from the README Documentation section and project instructions still left as
the scaffold template, so that the README remains the canonical entry point
and agents receive the project's real build and test commands.

## Context

`.github/agent-instructions.md` requires the README to have a near-top
Documentation section that links to every living guide. The 2026-10-20
`mailAgent` review found nine guides in `documentation/` absent from that
section, including `architecture.md`, `tuiStyling.md` and
`uiDesignPrinciples.md`. `manageProject --check` reported nothing.

The same project's `.github/additional-instructions.md` still contained only
the scaffold placeholders ("Record the project's purpose, conventions and
layout exceptions here." and "Document the actual build and test commands for
this repository here."). `manageProject --check` reported nothing.

## Scope

- Report each Markdown guide under `documentation/` that is not linked from
  the README Documentation section.
- Allow OMPR-deployed process guides to be satisfied by one link to a
  documented index or by an explicit, documented exclusion.
- Report a missing Documentation section near the top of the README.
- Warn when `.github/additional-instructions.md` is unchanged from the
  scaffold template or still contains its placeholder sentences.

## Out of scope

- Judging the quality of README or instruction content.
- Writing project documentation automatically.

## Acceptance criteria

1. Given a guide in `documentation/` with no link from the README
   Documentation section, when checked, then a finding names the guide.
2. Given a README without a Documentation section near the top, when checked,
   then a finding is reported.
3. Given an `additional-instructions.md` containing the scaffold placeholder
   sentences, when checked, then a warning is reported.
4. Given a project whose README links every guide and whose instructions are
   completed, when checked, then no finding is reported.

## Dependencies and decisions

- Builds on the README rules of requirement 004 and the existing DOC checks in
  `agentCheck.py`.
- Needs a decision on how OMPR-deployed guides are listed; record it in this
  requirement before implementation.
- No architecture decision is expected.

## Verification

- Fixture tests for each acceptance criterion.
- Run `manageProject --check` against `mailAgent` and confirm the nine missing
  guides and placeholder instructions are reported.

## Change history

- 2026-10-20: created — `mailAgent` review found missing README guide links
  and placeholder project instructions that passed the check; captured for the
  0.9 backlog.
