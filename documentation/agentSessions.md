# Agent sessions

agentSessions lists resumable local AI agent sessions without editing their stores.
By default it shows the most recently active session per agent for the current
working directory,
grouped alphabetically by agent, with newest sessions first within each agent. With --resume it offers the listing as an arrow-key menu and resumes the chosen
session with that agent's own command. `--id ROW` resumes a numbered row
directly.

## Runtime

agentSessions is an organiseMyProjects console script. Installing OMP
(`pip install .`, or `pip install -e .` for development) puts `agentSessions`
on PATH; `python -m organiseMyProjects.agentSessions` runs the same command.
It needs Python 3.10 or newer and only the standard library beyond OMP's own
logging. Dependencies are never installed by the command itself.

## Usage

```bash
agentSessions
agentSessions --all --full
agentSessions --history
agentSessions --claude
agentSessions --all --claude --codex
agentSessions --id 2
agentSessions --all --search migrateToRaid
agentSessions --resume
agentSessions --verbose
agentSessions --quiet
agentSessions --help
agentSessions --version
```

--all includes sessions from all working directories. --history includes older
sessions within the selected directory scope. Combine --all --history to see everything.
--claude, --codex, --copilot and --grok list only those agents' sessions; the
flags combine, so `--claude --grok` lists both, and with none every agent is
listed. --full displays complete IDs. --verbose enables
parser diagnostics; --quiet suppresses lifecycle messages. Shared run/section
separators and the listing remain visible. agentSessions never edits session
stores itself, so it has no --confirm option; a resumed agent manages its own store.

## Finding a session

--search TEXT keeps sessions whose title or directory contains TEXT, ignoring case.
It is applied before latest-session selection, so the default view shows the newest
matching session per agent and directory; add --history for every match. It
respects the directory scope, so add --all to search other projects:

```bash
agentSessions --all --search migrateToRaid
agentSessions --all --search migrateToRaid --history
agentSessions --all --search migrateToRaid --id 1
```

## Resuming a numbered row

Each table row has a number in the `#` column. Resume the matching agent session
directly, from its recorded working directory:

```bash
agentSessions --id 2
agentSessions --all --search migrateToRaid --id 1
```

`--id` changes to the stored directory and replaces `agentSessions` with the
selected agent's own resume command. Invalid row numbers return exit status 2
with an error on stderr. Use the same listing options: after
`agentSessions --all`, use `agentSessions --all --id 2`; include --history and
--search too when used for the listing. Row numbers refer to the current scan
and can change when sessions are added or updated.

Current-directory matching uses the exact resolved directory, including symlink
aliases. It excludes child directories and sessions with unknown working directories.
Use --all to include those sessions and other projects.

## Resuming a session

The easiest route is the interactive menu:

```bash
agentSessions --resume
agentSessions --all --search raid --resume
agentSessions --all --history --resume
```

It shows the same rows as the listing would for those options. Use ↑/↓ (or j/k),
PgUp/PgDn and Home/End to move, Enter to resume and q or Esc to cancel (exit 0).
On Enter, agentSessions changes to the session's working directory, prints the
command it is running and replaces itself with the agent. It refuses with status 1
when the directory is unknown or no longer exists, or the agent command is not
installed. --resume needs an interactive terminal (status 2 otherwise) and cannot
be combined with --id. With no matching sessions it reports that and exits 0.

To resume manually, run the matching agent command from the session's working
directory with the full ID:

```bash
codex resume <id>
claude --resume <id>
grok --resume <id>
copilot --resume=<id>
```

These examples are also included in `agentSessions --help` and were checked
against the installed agents' CLI help. For Claude and Copilot, see their
[CLI reference](https://docs.anthropic.com/en/docs/claude-code/cli-usage) and
[session guide](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/chronicle).

## Discovery and output

| Agent | Local source |
| --- | --- |
| Codex | ~/.codex/sessions/**/rollout-*.jsonl session_meta records |
| Claude | ~/.claude/projects/*/UUID.jsonl working-directory metadata |
| Grok | ~/.grok/sessions/encoded-directory/UUID, excluding nested subagents |
| Copilot | $COPILOT_HOME/session-state, defaulting to ~/.copilot/session-state |

Copilot requires events.jsonl and reads the simple cwd scalar from workspace.yaml,
falling back to session.start metadata. The workspace reader supports bare and
single/double-quoted scalar paths, rather than general YAML syntax.
Activity dates use local filesystem modification times. Grok prefers summary.json,
then chat_history.jsonl, updates.jsonl and finally the session directory timestamp.
Working directories need not still exist; missing metadata is shown as `?`.
Long paths and IDs are shortened for terminal display.

The TITLE column shows each agent's own description of the session:

| Agent | Title source |
| --- | --- |
| Codex | latest thread_name for the ID in ~/.codex/session_index.jsonl |
| Claude | custom-title (rename), then ai-title, then summary records; otherwise the opening prompt |
| Grok | session_summary in summary.json |
| Copilot | name scalar in workspace.yaml |

Titles are blank when the agent has not recorded one. Long titles are clipped at
the end; directory and title share the space left after the fixed columns.
Claude transcripts are only JSON-decoded on lines carrying a title record.

Missing stores are normal. Malformed JSON lines are skipped with debug diagnostics;
I/O failures are logged with context and other agent stores are still scanned.
If the output reader closes early (for example `| head`), the command stops
without a traceback and exits with status 1.
A successful listing may therefore be partial; inspect warnings when completeness
matters. Application logs are written under ~/.local/state/agentSessions/.

## Verification

```bash
python -m pytest tests/test_agentSessions.py --cov=organiseMyProjects.agentSessions --cov-report=term-missing
python -m black --check organiseMyProjects/agentSessions.py tests/test_agentSessions.py
runLinter organiseMyProjects/agentSessions.py
```

Tests use temporary homes and synthetic session metadata with the real shared
logger. They cover all four parsers, fallback metadata, latest-session selection,
rendering, titles, search, malformed input, I/O failures, source preservation and CLI execution.
