# 017: Requirements guide clarifications

## Status

ToDo

## Outcome

As a developer or agent following `documentation/requirementsManagement.md`, I
need the guide to state when a requirement may be renamed, how to refer to a
requirement in prose, and to contain no links to files that do not exist, so
that the guide cannot be read two ways and does not create false link-check
failures in every downstream project.

## Context

The 2026-10-20 `mailAgent` review exposed three gaps in the deployed guide:

- The guide says the identifier is permanent and the filename does not change
  when lifecycle status changes. It does not say whether a name that never
  followed the process may be corrected. The project owner's rule is that
  names are kept unless a correction is needed.
- The guide does not say how to refer to a requirement in prose. `mailAgent`
  used both `REQ-009` and `MA-011` styles.
- The guide's examples are live Markdown links to files that do not exist
  (`features/003-viewManagement.md`, `prompt/003a-viewManagement.md`,
  `../adr/002-viewStorage.md` and others), so a link check of any downstream
  project reports six broken links in a file the project does not own.
- The statement that "repository-specific prefixes may be used in external
  tools" was read as permission for a filename prefix.

## Scope

- State that requirement names and paths are permanent, except that a name
  that does not follow this process may be corrected; the correction keeps the
  number and is recorded in the record's change history.
- Define the prose reference form for a requirement (recommended `REQ-nnn`)
  and use it consistently in the guide.
- Clarify that external-tool prefixes never appear in filenames, headings or
  index Req IDs.
- Present example paths and table rows as code rather than live links.
- Apply the same rules to the template and to `.github/agent-instructions.md`
  where they restate them.

## Out of scope

- Automated detection and correction; see requirements 015 and 016.
- Changing the numbering scheme.

## Acceptance criteria

1. Given the updated guide, when read, then it states the
   rename-for-correction exception and requires a change-history entry.
2. Given the updated guide, when read, then it defines one prose reference
   form and uses it throughout.
3. Given a deployed project, when a relative link check runs over
   `documentation/requirementsManagement.md`, then it reports no broken links.
4. Given the guide's statement on external prefixes, when read, then it says
   explicitly that they are not used in filenames, headings or index IDs.

## Dependencies and decisions

- Supports requirements 015 and 016.
- Deployed documentation changes reach downstream projects through the normal
  update path.
- No architecture decision is expected.

## Verification

- Review the rendered guide.
- Run a relative link check over the deployed documentation set.
- `runLinter --markup` on the changed documentation.

## Change history

- 2026-10-20: created — `mailAgent` review and the project owner's ruling that
  names change only for corrections; captured for the 0.9 backlog.
