# 035: Project-neutral release guidance deployment

## Status

ToDo

## Outcome

As a managed-project maintainer, I need deployed release guidance to be
project-neutral so that update does not inject organiseMyProjects-specific
release history into consumer repositories.

## Context

The OMPR 0.10 alignment review found deployed `documentation/howToRelease.md`
content included OMPR-internal release history and source paths that do not
apply to consumer repositories.

## Scope

- Define and maintain a project-neutral managed release guide baseline for
  consumer repositories.
- Keep OMPR-specific release history in OMPR-local documentation where
  appropriate.
- Ensure managed deployment selects the correct release-guide variant for
  consumers.

## Out of scope

- Changing consumer-specific local release exceptions documented in each
  project's additional instructions.
- Full rewrite of release process outside project-neutrality concerns.

## Acceptance criteria

1. Given a consumer repository runs update, when managed release guidance is
   deployed, then it omits OMPR-internal release-history references that do not
   apply to consumers.
2. Given OMPR repository documentation is maintained, when release-history
   details are needed, then they remain in OMPR-owned docs rather than consumer
   managed baseline docs.
3. Given check validates managed documentation, when a repository is current,
   then no mismatch is reported due to intentionally project-neutral guide
   content.

## Dependencies and decisions

- Relates to requirements 004 and 020 documentation governance.

## Verification

- Add/update tests and fixtures that confirm neutral release-guide deployment
  for consumers.
- Validate update/check/documentation consistency around the guide content.

## Change history

- 2026-11-25: created from OMPR 0.10 alignment review findings recorded in
  `organiseMyConda/project/reviews/2026-11-25-ompr010Alignment.md`.
