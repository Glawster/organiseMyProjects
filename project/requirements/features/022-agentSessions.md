# 022: Agent session listing

## Status

InReview

## Outcome

As a developer using several AI coding agents, I need one agentSessions command
that lists and resumes my local Codex, Claude, Grok and Copilot sessions, so that
I can find and continue work without searching each agent's store, and so that
it is maintained and installed with the other OMP developer tools.

## Context

agentSessions began as a standalone script in Glawster/linuxMigration
(requirement 003 on its feature/agentSessions-process branch). It is a developer
tool rather than machine configuration and already depends on OMP logging, so it
moves into the OMP package as the `agentSessions` console script. The
linuxMigration requirement 003 is closed as moved here.

## Scope

- Show latest sessions for the current directory by default; --all includes all directories.
- Use --history for older sessions and --full for complete IDs.
- Group rows by agent, newest first, and provide numbered full-ID extraction.
- Show each agent's recorded session title alongside its row.
- Filter sessions by title or directory text with --search.
- Choose a session from an arrow-key menu and resume it with --resume.
- Apply shared logging, domainAction naming, types and focused helpers.
- Handle missing stores, malformed records and I/O failures without editing sessions.
- Add automated acceptance evidence and a maintained usage guide.

## Out of scope

Session deletion, agent-format redesign, custom resume options per agent,
deploying agentSessions into downstream projects, and changes to unrelated
utilities or managed guidance.

## Acceptance criteria

1. Representative stores for all four agents yield the correct agent, ID and directory.
2. Default listing selects the latest session per agent for the exact resolved cwd; --all includes all directories, --history includes older sessions and --full shows full IDs.
3. Missing stores and malformed JSON do not crash discovery; I/O failures produce contextual warnings.
4. Session data remains unchanged; only shared application logs are written.
5. The CLI exposes help, version, verbose and quiet options, documents resume syntax for all four agents in help, and initialises shared logging at entry.
6. Production-path tests, Black and targeted OMP lint pass; verification limitations are reported.

7. Rows are grouped alphabetically by agent, newest first within each group; numbered selectors match this ordering.
8. --id ROW prints only the selected full resume ID to stdout; invalid selectors fail with status 2 and a stderr error.
9. Each row shows the agent's stored title (Codex thread name, Claude rename/AI title or opening prompt, Grok summary, Copilot name), blank when absent and clipped to the terminal width.
10. --search TEXT keeps rows whose title or directory contains TEXT case-insensitively, applied within the directory scope and before latest selection; --id numbering follows the filtered listing.
11. --resume shows the selected listing as an arrow-key menu; Enter runs the agent's own resume command in the session's working directory, q/Esc cancels with status 0, a missing directory or agent command fails with status 1 and a non-interactive terminal or --id combination fails with status 2.

## Dependencies and decisions

- organiseMyProjects.logUtils provides logging; the command reports the OMP package version.
- The menu uses the standard-library curses module; no new dependency.
- No ADR required: a console script in the existing OMP package, like myBoard.

## Verification

- tests/test_agentSessions.py: real parsers, synthetic on-disk stores, CLI subprocesses and shared logging.
- Black check and runLinter on organiseMyProjects/agentSessions.py.
- Independent review and human acceptance before completion/merge.

## Change history

- 2026-10-23: created in linuxMigration (requirement 003) from the request to align agentSessions with .github coding process.
- 2026-10-23: added agent grouping and numbered resume-ID extraction at user request.
- 2026-10-23: default to cwd; --all expands directories and --history includes older sessions.
- 2026-10-23: included verified per-agent resume commands in CLI help.
- 2026-10-23: added TITLE column from each agent's stored session description at user request.
- 2026-10-23: added --search over titles and directories at user request.
- 2026-10-23: closed output pipes end quietly with status 1 instead of a traceback.
- 2026-10-23: added --resume arrow-key menu and agent launch at user request, moving resumption into scope.
- 2026-10-25: moved from linuxMigration into OMP as requirement 022 and the
  `agentSessions` console script at the owner's request; history above is kept.
