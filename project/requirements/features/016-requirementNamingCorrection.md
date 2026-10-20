# 016: Requirement naming correction during update

## Status

Completed

## Outcome

As an OMPR user, I need `manageProject --update` to correct non-conforming
requirement and prompt names deterministically, so that bringing a project in
line with the requirements process is a reviewed dry-run and one confirmed
command rather than a hand-written rename across many files.

## Context

Correcting `mailAgent` on 2026-10-20 required renaming thirteen records and
five prompts, moving prompts from `project/prompts/` to
`project/requirements/prompt/`, normalising headings and `## Status`
sections, rewriting the index, and updating links in the README,
documentation, reviews, configuration examples and code comments. Every step
was mechanical and followed the same mapping.

Requirement 004 already defines no-loss cleanup for legacy index and
per-requirement directory layouts. It does not cover filename prefixes,
hyphenated names or a misplaced prompt directory.

## Scope

- Derive the corrected filename from the existing number and name: drop a
  non-numeric prefix (`MA-011-x` → `011-x`) and convert hyphenated names to
  camelCase (`009-read-inbox-filing` → `009-readInboxFiling`).
- Move prompts from recognised non-canonical locations such as
  `project/prompts/` to `project/requirements/prompt/` with the corrected name.
- Normalise the heading to `# <nnn>: <Title>` and a `Status:` line to a
  `## Status` section.
- Rewrite index Req IDs and links, and update Markdown link destinations to
  renamed files throughout the repository.
- Report non-link mentions of the old ID (for example `MA-012` in prose or code
  comments) for review rather than rewriting them silently.
- Use `git mv` when the file is tracked, so history follows the rename.
- Dry-run by default; `--confirm` applies. Re-running after success changes
  nothing.

## Out of scope

- Renaming a conforming record for any other reason.
- Renumbering records or reusing identifiers.
- Rewriting historical examples or quoted text that mentions an old filename.

## Acceptance criteria

1. Given `features/MA-012-rolling-imap-retention.md`, when update runs without
   `--confirm`, then it reports the rename to `012-rollingImapRetention.md`
   and the links it would change, and changes nothing.
2. Given the same repository with `--confirm`, then the file is renamed (with
   `git mv` when tracked), its heading and status section are normalised, and
   every Markdown link to the old path resolves to the new path.
3. Given prompts in `project/prompts/`, when update is confirmed, then they are
   moved to `project/requirements/prompt/` with names matching their
   requirements and the empty legacy directory is removed.
4. Given a corrected name that already exists with different content, then the
   collision is reported and neither file is changed.
5. Given prose or code that mentions an old ID, then update lists it for review
   and does not rewrite it automatically.
6. Given a repository already corrected, when update runs again, then it reports
   no changes.
7. Given a confirmed correction, then each renamed record gains a change-history
   entry recording the correction.

## Dependencies and decisions

- Uses the findings defined by requirement 015.
- Extends the requirement 004 cleanup rules and their no-loss safeguards.
- The rename-for-correction policy is documented by requirement 017.
- No architecture decision is expected.

## Verification

- Fixture tests reproducing the `mailAgent` layout before commit `ff5cb72`,
  comparing the result with that commit.
- Collision, idempotency and untracked-file tests.
- Dry-run test proving no filesystem change.

## Change history

- 2026-10-20: created — the manual `mailAgent` naming correction showed the
  work is deterministic; captured for the 0.9 backlog.
- 2026-10-20: Completed — `requirementNaming.requirementNamesCorrect` runs from
  `manageProject --update` after layout migration; 8 tests, 456 passed in
  `ompr`. On the pre-correction `mailAgent` tree (`922573d`) it made 16 renames
  and 18 edits matching commit `ff5cb72` apart from reported prose mentions,
  took `--check` from 38 failures to 0, and a second run changed nothing.
