# 015: Requirement record conformance checks

## Status

ToDo

## Outcome

As an OMPR user, I need `manageProject --check` to report requirement records,
prompts and index rows that do not follow `documentation/requirementsManagement.md`,
so that naming and structure drift is caught when it first appears rather than
after many records have copied it.

## Context

A 2026-10-20 review of `mailAgent` found fourteen requirement records that had
drifted from the shared process while `manageProject --check` reported zero
failures and zero warnings:

- five records used a local `MA-` filename prefix (`MA-011-…` to `MA-015-…`);
- eight used hyphenated rather than camelCase names (`009-read-inbox-filing.md`);
- headings mixed `# REQ-004 - …`, `# MA-011 …` and `# MA-013: …`;
- two records used a `Status:` line instead of a `## Status` section;
- prompts lived in `project/prompts/` and were linked as `../prompts/…`;
- the index preamble said "New requirement records use the stable project
  prefix `MA`", contradicting the shared guide.

The existing `REQ-*` checks in `agentCheck._checkRequirementsAndAdrs` did not
fail; they silently skipped what they could not parse:

- REQ-002 matches index rows with `\|\s*\d+\s*\|`, so `MA-011` rows were never
  compared;
- REQ-002 reads status only from `## Status`, so `Status:` records were never
  compared;
- REQ-005 inspects only `](prompt/…)` links, so `../prompts/` links were never
  checked.

## Scope

- Report a requirement file whose name does not match
  `<nnn>-<camelCaseName>.md`.
- Report a record whose first line is not `# <nnn>: <Title>` with `<nnn>`
  equal to the filename number.
- Report a record missing any required template section (`Status`, `Outcome`,
  `Context`, `Scope`, `Out of scope`, `Acceptance criteria`,
  `Dependencies and decisions`, `Verification`, `Change history`).
- Report an index row whose Req ID is not the three-digit number of the file
  it links, or that cannot be parsed, instead of skipping it.
- Report a record whose status cannot be read, instead of skipping REQ-002.
- Report prompt links that point outside `project/requirements/prompt/`, and
  prompt files found anywhere else under `project/`.
- Report index text that declares a filename prefix or other convention that
  contradicts the shared guide.
- Give each new finding a stable rule ID and a message naming the expected form.

## Out of scope

- Fixing the findings automatically; see requirement 016.
- Judging the quality of requirement content.
- Checking requirement records in repositories that do not use the OMP
  `project/requirements/` layout.

## Acceptance criteria

1. Given `features/MA-011-sessionCredentialCache.md` or
   `features/009-read-inbox-filing.md`, when `manageProject --check` runs, then
   a failure names the file and the expected `nnn-camelCaseName.md` form.
2. Given a record headed `# REQ-004 - Title` or `# MA-011 Title`, when checked,
   then a failure names the expected `# 004: Title` heading.
3. Given a record with `Status: InProgress` and no `## Status` section, when
   checked, then a failure reports the missing section rather than skipping the
   status comparison.
4. Given an index row whose Req ID is `MA-011` while it links
   `features/011-sessionCredentialCache.md`, when checked, then a failure
   reports the Req ID mismatch rather than skipping the row.
5. Given a prompt linked as `../prompts/013-x.md` or stored in
   `project/prompts/`, when checked, then a failure names the canonical
   `project/requirements/prompt/013-x.md` location.
6. Given an index preamble declaring a project filename prefix, when checked,
   then a warning cites the conflicting shared rule.
7. Given a repository that already conforms, when checked, then no new
   findings are reported.

## Dependencies and decisions

- Builds on requirement 004 (canonical requirement and prompt layout) and the
  existing REQ-001 to REQ-005 checks in `agentCheck.py`.
- Requirement 016 consumes these findings to perform corrections.
- No architecture decision is expected.

## Verification

- Unit tests with fixture repositories reproducing each `mailAgent` drift case.
- A conforming fixture produces no new findings.
- Run `manageProject --check` against `mailAgent` before and after its
  2026-10-20 naming correction (commit `ff5cb72`).

## Change history

- 2026-10-20: created — `mailAgent` review found fourteen non-conforming
  records that `manageProject --check` passed; captured for the 0.9 backlog.
