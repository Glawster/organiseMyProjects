# Agent sessions

`agentSessions` finds the sessions you have had with Claude, Codex, Copilot and
Grok on this machine and lets you pick one up where you left off. It only reads
the agents' session stores; it never changes or deletes them.

## Getting started

`agentSessions` is installed with organiseMyProjects (`pip install .`, or
`pip install -e .` for development). It needs Python 3.10 or newer.
`python -m organiseMyProjects.agentSessions` runs the same command.

From a project folder, run:

```bash
agentSessions
```

You see the latest session each agent has for this folder:

```text
#  AGENT   DATE              DIRECTORY           SESSION ID  TITLE
1  Claude  2026-10-26 10:41  organiseMyProjects  6605aa7a…   agentSessions user guide
2  Codex   2026-10-24 16:02  organiseMyProjects  0199f3c2…   Requirement board fixes
```

To carry on with one of them:

```bash
agentSessions --resume
```

Choose a session and press Enter. `agentSessions` changes to that session's
folder and starts the agent there with the session reopened.

## Reading the listing

| Column | What it shows |
| --- | --- |
| `#` | The row's position in this listing |
| AGENT | Claude, Codex, Copilot or Grok |
| DATE | When the session was last active |
| DIRECTORY | The name of the folder the session ran in |
| SESSION ID | The agent's session ID, shortened unless you add `--full` |
| TITLE | The agent's own description of the session |

Rows are grouped by agent in alphabetical order, newest first within each
agent. DIRECTORY shows only the folder name; the full path is kept for
resuming. Two different folders with the same name therefore look alike in the
listing. A `?` means the agent did not record a folder.

Titles come from each agent's own records: a Claude rename or generated title
(or the opening prompt when there is neither), the Codex thread name, the Grok
session summary or the Copilot session name. A blank title means the agent has
not recorded one. Long titles are cut short to fit the terminal.

## Choosing which sessions to see

By default you see one session, the latest, per agent for the current folder
only. Each option widens or narrows that:

| Option | Effect |
| --- | --- |
| `--all` | Include sessions from every folder |
| `--history` | Include older sessions, not just the latest per agent and folder |
| `--search TEXT` | Keep sessions whose title or folder contains TEXT, in any case |
| `--claude`, `--codex`, `--copilot`, `--grok` | Keep only those agents' sessions, from every folder |
| `--full` | Show complete session IDs |

Options combine. Some common combinations:

```bash
agentSessions --all                          # latest session per agent in every folder
agentSessions --history                      # every session in this folder
agentSessions --all --history                # everything
agentSessions --claude                       # Claude sessions in every folder
agentSessions --claude --grok                # Claude and Grok sessions in every folder
agentSessions --all --search migrateToRaid   # sessions about migrateToRaid, anywhere
```

The agent options add up: `--claude --grok` shows both agents. They always
search every folder, so `--all` is not needed with them, and combining the two
is refused.

`--search` only looks in the current folder unless you add `--all` or an agent
option. It is applied before the latest session is picked, so you see the newest
*matching* session per agent and folder; add `--history` to see every match.

"This folder" means exactly the folder you are in, after following symlinks.
Sessions started in a subfolder are not included; use `--all` or `--search`
to find them.

## Resuming a session

`--resume` shows the listing you asked for as a menu:

```bash
agentSessions --resume
agentSessions --claude --resume
agentSessions --all --search raid --resume
```

| Key | Action |
| --- | --- |
| ↑ / ↓, or k / j | Move one row |
| PgUp / PgDn | Move one screen |
| Home / End | Jump to the first or last row |
| Enter | Resume the selected session |
| q or Esc | Cancel without resuming |

On Enter, `agentSessions` prints the command it is about to run, changes to the
session's folder and hands the terminal to the agent. When you leave the agent
you return to your shell in the folder you started from.

`--resume` needs an interactive terminal. It stops with an error if the
session's folder no longer exists, its folder was not recorded, or the agent's
command is not installed.

To resume by hand instead, go to the session's folder and use the full ID from
`agentSessions --full`:

```bash
claude --resume <id>
codex resume <id>
copilot --resume=<id>
grok --resume <id>
```

These are also listed in `agentSessions --help`.

## Messages and exit status

| Status | Meaning |
| --- | --- |
| 0 | Listing shown, session resumed, menu cancelled, or nothing to show |
| 1 | A session could not be resumed, or the output was closed early (for example by `\| head`) |
| 2 | Invalid options, `--all` with an agent option, or `--resume` without a terminal |

`No local agent sessions found.` means nothing matched; try `--all` or fewer
filters. `--quiet` hides the start and finish messages and `--verbose` adds
diagnostic detail. Logs are written under `~/.local/state/agentSessions/`.

If an agent's store cannot be read, `agentSessions` warns and still lists the
other agents, so a listing can be incomplete. Check for warnings when you need
every session.

## Where sessions come from

| Agent | Session store |
| --- | --- |
| Claude | `~/.claude/projects/*/<id>.jsonl` |
| Codex | `~/.codex/sessions/**/rollout-*.jsonl` (titles from `~/.codex/session_index.jsonl`) |
| Copilot | `$COPILOT_HOME/session-state`, by default `~/.copilot/session-state` |
| Grok | `~/.grok/sessions/<encoded folder>/<id>`, not counting subagents |

DATE is the modification time of the session's files. A store that does not
exist is skipped silently, and malformed records are ignored. The resume
commands were checked against each agent's CLI help; see the
[Claude Code CLI reference](https://docs.anthropic.com/en/docs/claude-code/cli-usage)
and [Copilot CLI session guide](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/chronicle).

## Verification

```bash
python -m pytest tests/test_agentSessions.py --cov=organiseMyProjects.agentSessions --cov-report=term-missing
python -m black --check organiseMyProjects/agentSessions.py tests/test_agentSessions.py
runLinter organiseMyProjects/agentSessions.py
```

Tests use temporary home folders with synthetic session stores and the real
shared logger. They cover all four agents' stores, titles, filtering, search,
the menu, resuming, malformed input and read failures.
