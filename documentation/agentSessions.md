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

## Account capacity remaining

Run `agentSessions --usage` to compare account allowances without listing or
resuming sessions. Use `--quiet` to suppress lifecycle messages or `--verbose`
for the existing logging mode. Session options such as `--all`, `--history`,
`--search`, agent filters and `--resume` cannot be combined with `--usage`.

Every percentage means **available/remaining**, including `0%` for an exhausted
allowance. Used percentages are converted with `100 - used`; remaining
percentages are retained, with results clamped to 0–100. Rows are grouped by agent, with one allowance per line and aligned
window, available-capacity and reset columns. Independent quota windows keep
their own reset times in local time. Missing reset times appear as `—`.

- `NOT INSTALLED`: the agent executable is absent from PATH.
- `NOT AUTHENTICATED`: a supported status response or explicit authentication
  error says that the account is not authenticated.
- `UNKNOWN`: the provider did not supply a trustworthy account percentage,
  does not support the account method, failed, or timed out. Authentication
  failures that cannot be reliably identified also remain unknown.

Provider adapters use short-lived local protocol clients, query accounts
independently, and apply a twelve-second deadline per provider. They do not
submit model tasks, read OAuth credential files, or
print/log raw protocol responses and provider errors. The provider CLIs own
credential access and may update their own normal runtime state.

### Provider interfaces and limitations

- **Claude:** `claude auth status --json` distinguishes an unauthenticated
  account. On POSIX systems the user-approved fallback launches a separate
  `claude --safe-mode --no-chrome` terminal and submits only the built-in `/usage`
  command. The `pyte` dependency interprets cursor movement and redraws in memory,
  so overwritten percentages are not read as current values. The adapter reads
  the current session and all-model weekly bars, plus additional weekly bars
  when present, and converts their explicitly labelled used percentages.
  Resets are parsed with the timezone shown by Claude. A time-only reset denotes
  its next occurrence; a dated reset uses the current year, rolling into the
  next year when required. Unrecognised reset formats remain `—`.
  Terminal frames are never saved or logged. Trust, login and terms dialogs
  are not accepted automatically. The child process group is terminated and
  reaped after capture, failure or timeout. Screen-format changes, missing quota
  bars, unsupported platforms, or unavailable terminal support produce `UNKNOWN`.
  This fallback was verified with Claude Code 2.1.314. UI scraping is less stable
  than an account protocol; direct OAuth extraction and undocumented usage
  endpoints remain excluded.
- **Codex:** the app-server `account/read` and `account/rateLimits/read`
  methods provide authentication and quota snapshots. Primary/secondary windows
  remain separate, named buckets are preserved, and `usedPercent` is converted.
  Known five-hour and seven-day durations are labelled `5h` and `weekly`.
- **Grok:** `grok agent --no-leader stdio` exposes the `_x.ai/billing` ACP
  extension. Only `config.creditUsagePercent` is interpreted as used capacity;
  `config.currentPeriod.end` provides its reset. The installed 1.0.70 CLI
  returned the period but omitted that percentage during verification, so it
  shows `weekly: UNKNOWN` with the supplied reset. Financial balances and
  per-session token/cost statistics are never substituted for availability.
- **Copilot:** the headless SDK stdio protocol exposes `auth.getStatus` and
  `account.getQuota`. Each `quotaSnapshots` entry retains its provider name,
  `remainingPercentage`, and `resetDate`. Account windows need not be weekly;
  chat, completions and premium interactions can have different entitlements.

The interface basis is the
[Codex app-server protocol](https://github.com/openai/codex/tree/main/codex-rs/app-server),
[Copilot SDK account quota documentation](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/usage-and-billing),
[pyte's terminal-emulation API](https://pyte.readthedocs.io/en/latest/api.html),
and live read-only probes of the installed CLIs. Grok's extension was verified
locally; it may change across versions. Unsupported or changed response shapes
remain `UNKNOWN` rather than being inferred from unrelated values.

Run the focused regression suite with:

```bash
python -m pytest tests/test_agentUsage.py tests/test_claudeUsage.py tests/test_agentSessions.py
```

The tests compose actual stdio subprocesses and pseudo-terminals using synthetic
account responses and terminal redraws;
live account values are not committed as fixtures. This is an OMPR developer
command; OMS, OMV and OMP need no code or runtime changes.
