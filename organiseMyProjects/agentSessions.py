"""List and resume local agent sessions; session stores are always read-only."""

import argparse
import curses
import json
import logging
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, TypedDict
from urllib.parse import unquote

from organiseMyProjects.logUtils import getLogger, line, runStart, setApplication
from organiseMyProjects.version import VERSION


class Session(TypedDict):
    """One resumable local session and its latest activity."""

    agent: str
    date: datetime
    directory: str
    session_id: str
    title: str


HOME = Path.home()

# Later Claude title records supersede earlier ones; a user rename outranks generated
# text. Untitled sessions fall back to their opening prompt, which sets the topic.
CLAUDE_TITLES = (
    ("custom-title", "customTitle"),
    ("ai-title", "aiTitle"),
    ("summary", "summary"),
    ("last-prompt", "lastPrompt"),
)


# Each agent's own resume syntax, verified against its installed CLI help.
RESUME_COMMANDS = {
    "Claude": ("claude", "--resume", "{id}"),
    "Codex": ("codex", "resume", "{id}"),
    "Copilot": ("copilot", "--resume={id}"),
    "Grok": ("grok", "--resume", "{id}"),
}

PICKER_HELP = "↑/↓ move · PgUp/PgDn page · Enter resume · q cancel"


UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}$"
)

## command


def main() -> int:
    """Initialise logging, discover sessions and render the requested listing."""
    parser = parserBuild()
    args = parser.parse_args()
    setApplication("agentSessions")
    level = (
        logging.DEBUG
        if args.verbose
        else logging.WARNING if args.quiet else logging.INFO
    )
    if args.all and args.agents:
        parser.error("--all is implied by the agent options")
    if args.usage and (
        args.resume
        or args.all
        or args.agents
        or args.search is not None
        or args.history
        or args.full
    ):
        parser.error(
            "--usage cannot be combined with session listing or resume options"
        )
    if args.resume and not (sys.stdin.isatty() and sys.stdout.isatty()):
        parser.error("--resume needs an interactive terminal")
    # The picker owns the screen, so console logging would corrupt it.
    logger = getLogger(includeConsole=not args.resume, level=level)
    if args.usage:
        from organiseMyProjects.agentUsage import allowanceCollect, allowanceLines

        runStart()
        logger.doing("reading account availability")
        line()
        for text in allowanceLines(allowanceCollect()):
            print(text)
        line()
        logger.done("account availability complete")
        return 0
    rows = sessionsCollect()
    if args.agents:
        rows = sessionsForAgents(rows, args.agents)
    # Agent options always search every directory.
    if not (args.all or args.agents):
        rows = sessionsForDirectory(rows, Path.cwd())
    if args.search is not None:
        rows = sessionsSearch(rows, args.search)
    if not args.history:
        rows = sessionsLatest(rows)
    rows = sessionsSort(rows)
    if args.resume:
        if not rows:
            print("No local agent sessions found.")
            return 0
        selected = sessionPick(rows)
        if selected is None:
            logger.info("resume cancelled")
            return 0
        return sessionResume(selected)
    runStart()
    logger.doing("listing local agent sessions")
    line()
    tablePrint(rows, full_ids=args.full)
    line()
    logger.value("sessions", len(rows))
    logger.done("session listing complete")
    return 0


def parserBuild() -> argparse.ArgumentParser:
    """Build the scriptable, read-only listing interface."""
    parser = argparse.ArgumentParser(
        description="List resumable local AI agent sessions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Resume a session (use its full ID, from the session's working directory):
  Codex:    codex resume <id>
  Claude:   claude --resume <id>
  Grok:     grok --resume <id>
  Copilot:  copilot --resume=<id>

List only some agents, from every directory (flags combine):
  agentSessions --claude
  agentSessions --claude --codex --resume

Find a session by title or directory:
  agentSessions --all --search migrateToRaid

Pick from a menu and resume in the session's directory:
  agentSessions --resume
  agentSessions --all --search raid --resume
""",
    )
    parser.add_argument(
        "--usage",
        action="store_true",
        help="show account capacity remaining for every supported agent",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="include sessions from all working directories",
    )
    # Each flag adds its agent, so --claude --grok lists both. They imply --all.
    for agent in RESUME_COMMANDS:
        parser.add_argument(
            f"--{agent.lower()}",
            dest="agents",
            action="append_const",
            const=agent,
            help=f"include {agent} sessions from every directory (combine flags)",
        )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="choose a session from an arrow-key menu and resume it",
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="include older sessions as well as the latest",
    )
    parser.add_argument(
        "--search",
        metavar="TEXT",
        help="keep sessions whose title or directory contains TEXT (any case)",
    )
    parser.add_argument("--full", action="store_true", help="show complete session IDs")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    output = parser.add_mutually_exclusive_group()
    output.add_argument(
        "--verbose", action="store_true", help="enable diagnostic logging"
    )
    output.add_argument(
        "--quiet", action="store_true", help="suppress console lifecycle messages"
    )
    return parser


def sessionsCollect() -> list[Session]:
    """Discover all supported local stores without changing session data."""
    rows: list[Session] = []
    for collect in (_claudeCollect, _codexCollect, _grokCollect, _copilotCollect):
        try:
            collect(rows)
        except OSError as error:
            # A broken store must not hide sessions from the remaining providers.
            _warningReport(f"cannot scan session store: {collect.__name__}: {error}")
    getLogger().debug("scanned all supported session stores")
    return rows


def sessionsForAgents(rows: list[Session], agents: list[str]) -> list[Session]:
    """Keep sessions from the selected agents only."""
    wanted = set(agents)
    return [row for row in rows if row["agent"] in wanted]


def sessionsForDirectory(rows: list[Session], directory: Path) -> list[Session]:
    """Match exact working directories, resolving symlinks and home abbreviations."""
    target = directory.resolve()
    matches = []
    for row in rows:
        if row["directory"] == "?":
            continue
        stored = row["directory"]
        path = _pathExpand(stored)
        try:
            if path.resolve() == target:
                matches.append(row)
        except (OSError, ValueError, RuntimeError) as error:
            _warningReport(f"cannot resolve session directory: {stored}: {error}")
    return matches


def sessionsSearch(rows: list[Session], text: str) -> list[Session]:
    """Match descriptive text before latest selection, so older matches can surface."""
    wanted = text.casefold()
    return [
        row
        for row in rows
        if wanted in row["title"].casefold() or wanted in row["directory"].casefold()
    ]


def sessionsLatest(rows: list[Session]) -> list[Session]:
    """Select the most recent session for each agent and working directory."""
    latest = {}

    for row in rows:
        key = (row["agent"], row["directory"])

        old = latest.get(key)
        if old is None or row["date"] > old["date"]:
            latest[key] = row

    return list(latest.values())


def sessionsSort(rows: list[Session]) -> list[Session]:
    """Group agents alphabetically, then order newest first with stable tie breaks."""
    rows = sorted(rows, key=lambda row: (row["directory"], row["session_id"]))
    rows.sort(key=lambda row: row["date"], reverse=True)
    rows.sort(key=lambda row: row["agent"].casefold())
    return rows


def sessionPick(rows: list[Session]) -> Session | None:
    """Show the listing as an arrow-key menu; None means the user cancelled."""
    # Esc otherwise waits a full second for a possible escape sequence.
    os.environ.setdefault("ESCDELAY", "25")
    index = curses.wrapper(_pickerRun, rows)
    return None if index is None else rows[index]


def sessionResume(row: Session) -> int:
    """Replace this process with the agent's resume command in its directory."""
    logger = getLogger()
    command = resumeCommand(row)
    stored = row["directory"]
    directory = _pathExpand(stored)
    if stored == "?" or not directory.is_dir():
        logger.error(f"cannot resume: working directory not found: {stored}")
        return 1
    print(f"Resuming {row['agent']} session in {stored}: {' '.join(command)}")
    logger.info("resuming %s in %s", " ".join(command), directory)
    try:
        os.chdir(directory)
        os.execvp(command[0], command)
    except OSError as error:
        logger.error(f"cannot resume: {command[0]}: {error}")
        return 1
    return 0


def resumeCommand(row: Session) -> list[str]:
    """Build the agent's resume command for one session."""
    return [part.format(id=row["session_id"]) for part in RESUME_COMMANDS[row["agent"]]]


def tableLines(
    rows: list[Session], full_ids: bool = False, terminal_width: int | None = None
) -> list[str]:
    """Format a header and one line per row, sized to the terminal width."""
    if terminal_width is None:
        terminal_width = shutil.get_terminal_size(fallback=(120, 24)).columns

    rendered = []

    for row in rows:
        sid = row["session_id"]

        if not full_ids and len(sid) > 12:
            sid = sid[:8] + "…"

        rendered.append(
            {
                "agent": row["agent"],
                "date": row["date"].strftime("%Y-%m-%d %H:%M"),
                # Only the folder name is shown; the full path stays on the row
                # so resuming still changes into the right directory.
                "directory": Path(row["directory"]).name or row["directory"],
                "session_id": sid,
                "title": " ".join(row["title"].split()),
            }
        )

    number_width = max(1, len(str(len(rows))))
    agent_width, date_width, session_width, dir_width, title_width = _tableWidths(
        rendered, number_width, terminal_width
    )

    lines = [
        f"{'#':>{number_width}}  "
        f"{'AGENT':<{agent_width}}  "
        f"{'DATE':<{date_width}}  "
        f"{'DIRECTORY':<{dir_width}}  "
        f"{'SESSION ID':<{session_width}}  "
        f"{'TITLE'}"
    ]

    for number, row in enumerate(rendered, start=1):
        directory = _textTruncate(
            row["directory"],
            dir_width,
        )

        lines.append(
            f"{number:>{number_width}}  "
            f"{row['agent']:<{agent_width}}  "
            f"{row['date']:<{date_width}}  "
            f"{directory:<{dir_width}}  "
            f"{row['session_id']:<{session_width}}  "
            f"{_textClip(row['title'], title_width)}"
        )

    return lines


def tablePrint(rows: list[Session], full_ids: bool = False) -> None:
    """Render a terminal-width-aware listing without changing session records."""
    if not rows:
        print("No local agent sessions found.")
        return

    for text in tableLines(sessionsSort(rows), full_ids):
        print(text)


## utilities


def _claudeCollect(rows: list[Session]) -> None:
    root = HOME / ".claude" / "projects"
    if not root.is_dir():
        return

    for path in root.glob("*/*.jsonl"):
        session_id = path.stem

        if not UUID_RE.match(session_id):
            continue

        cwd = next(
            (
                _jsonFind(obj, ("cwd",))
                for obj in _jsonRecords(path)
                if _jsonFind(obj, ("cwd",))
            ),
            None,
        )

        _sessionAppend(
            rows,
            "Claude",
            _fileDate(path),
            cwd,
            session_id,
            _claudeTitle(path),
        )


def _claudeTitle(path: Path) -> str | None:
    """Return the best title, decoding only title records from large transcripts."""
    found: dict[str, str] = {}
    markers = {f'"type":"{kind}"': (kind, key) for kind, key in CLAUDE_TITLES}
    try:
        with path.open("r", encoding="utf-8", errors="replace") as stream:
            for record in stream:
                match = next((m for m in markers if m in record), None)
                if match is None:
                    continue
                kind, key = markers[match]
                try:
                    value = json.loads(record).get(key)
                except (json.JSONDecodeError, AttributeError):
                    continue
                if isinstance(value, str) and value.strip():
                    if kind != "last-prompt" or kind not in found:
                        found[kind] = value
    except OSError as error:
        _warningReport(f"cannot read session title: {path}: {error}")
    return next((found[kind] for kind, _ in CLAUDE_TITLES if kind in found), None)


def _codexCollect(rows: list[Session]) -> None:
    root = HOME / ".codex" / "sessions"
    if not root.is_dir():
        return

    titles = _codexTitles(HOME / ".codex" / "session_index.jsonl")

    for path in root.rglob("rollout-*.jsonl"):
        obj = _jsonFirst(path)
        if not isinstance(obj, dict):
            continue

        payload = obj.get("payload", {})
        if not isinstance(payload, dict):
            continue
        if obj.get("type") != "session_meta":
            continue

        session_id = payload.get("id") or payload.get("session_id")
        cwd = payload.get("cwd")

        _sessionAppend(
            rows,
            "Codex",
            _fileDate(path),
            cwd,
            session_id,
            titles.get(session_id) if isinstance(session_id, str) else None,
        )


def _codexTitles(path: Path) -> dict[str, str]:
    """Map session IDs to thread names; later index entries record renames."""
    titles = {}
    if not path.exists():
        return titles
    for obj in _jsonRecords(path):
        if not isinstance(obj, dict):
            continue
        session_id, name = obj.get("id"), obj.get("thread_name")
        if isinstance(session_id, str) and isinstance(name, str) and name:
            titles[session_id] = name
    return titles


def _copilotCollect(rows: list[Session]) -> None:
    copilot_home = Path(os.environ.get("COPILOT_HOME", HOME / ".copilot")).expanduser()

    root = copilot_home / "session-state"
    if not root.is_dir():
        return

    for session_dir in root.iterdir():
        if not session_dir.is_dir():
            continue

        session_id = session_dir.name

        events = session_dir / "events.jsonl"
        workspace = session_dir / "workspace.yaml"

        # A resumable local session should have its event history.
        if not events.exists():
            continue

        cwd = None
        title = None

        if workspace.exists():
            cwd = _yamlValue(workspace, "cwd")
            title = _yamlValue(workspace, "name")

        # Only session.start is authoritative when the workspace scalar is absent.
        if not cwd:
            cwd = next(
                (
                    _jsonFind(obj, ("cwd", "workingDirectory"))
                    for obj in _jsonRecords(events)
                    if isinstance(obj, dict)
                    and obj.get("type") == "session.start"
                    and _jsonFind(obj, ("cwd", "workingDirectory"))
                ),
                None,
            )

        _sessionAppend(
            rows,
            "Copilot",
            _fileDate(events),
            cwd,
            session_id,
            title,
        )


def _fileDate(path: Path) -> datetime:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime)
    except OSError as error:
        _warningReport(f"cannot read session timestamp: {path}: {error}")
        return datetime.min


def _grokCollect(rows: list[Session]) -> None:
    root = HOME / ".grok" / "sessions"
    if not root.is_dir():
        return

    # Layout:
    # ~/.grok/sessions/<url-encoded-cwd>/<session-id>/
    #
    # Deliberately only inspect direct children so Grok subagent UUIDs
    # are not mistaken for top-level resumable sessions.
    for project_dir in root.iterdir():
        if not project_dir.is_dir():
            continue

        cwd = unquote(project_dir.name)

        for session_dir in project_dir.iterdir():
            if not session_dir.is_dir():
                continue

            session_id = session_dir.name

            if not UUID_RE.match(session_id):
                continue

            # summary.json is a good proxy for last session activity.
            # Fall back to chat history, then directory mtime.
            candidates = [
                session_dir / "summary.json",
                session_dir / "chat_history.jsonl",
                session_dir / "updates.jsonl",
            ]

            date_source = session_dir
            for candidate in candidates:
                if candidate.exists():
                    date_source = candidate
                    break

            summary = session_dir / "summary.json"
            _sessionAppend(
                rows,
                "Grok",
                _fileDate(date_source),
                cwd,
                session_id,
                (
                    _jsonFind(_jsonFirst(summary), ("session_summary",))
                    if summary.exists()
                    else None
                ),
            )


def _jsonFind(obj: Any, names: tuple[str, ...]) -> str | None:
    """Recursively find the first string value whose key matches."""
    if isinstance(obj, dict):
        for key in names:
            value = obj.get(key)
            if isinstance(value, str) and value:
                return value

        for value in obj.values():
            found = _jsonFind(value, names)
            if found:
                return found

    elif isinstance(obj, list):
        for value in obj:
            found = _jsonFind(value, names)
            if found:
                return found

    return None


def _jsonFirst(path: Path) -> Any:
    return next(_jsonRecords(path), None)


def _jsonRecords(path: Path) -> Iterator[Any]:
    """Stream valid JSON values, tolerating partial writes and reporting I/O failures."""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as stream:
            for record in stream:
                if not record.strip():
                    continue
                try:
                    yield json.loads(record)
                except json.JSONDecodeError:
                    getLogger().debug("skipping malformed session record in %s", path)
    except OSError as error:
        _warningReport(f"cannot read session metadata: {path}: {error}")


def _pickerMove(index: int, key: int, count: int, page: int) -> int:
    """Apply one navigation key, clamping to the list."""
    moves = {
        curses.KEY_UP: -1,
        ord("k"): -1,
        curses.KEY_DOWN: 1,
        ord("j"): 1,
        curses.KEY_PPAGE: -page,
        curses.KEY_NPAGE: page,
    }
    if key == curses.KEY_HOME:
        return 0
    if key == curses.KEY_END:
        return count - 1
    return min(count - 1, max(0, index + moves.get(key, 0)))


def _pickerRun(screen: Any, rows: list[Session]) -> int | None:
    """Drive the menu on a curses screen; returns the chosen row index."""
    try:
        curses.curs_set(0)
    except curses.error:
        pass  # Some terminals cannot hide the cursor.
    screen.keypad(True)
    index, top = 0, 0
    while True:
        height, width = screen.getmaxyx()
        # The header, help line and a blank separator leave the rest for rows.
        visible = max(1, height - 3)
        lines = tableLines(rows, terminal_width=width - 1)
        if index < top:
            top = index
        elif index >= top + visible:
            top = index - visible + 1
        screen.erase()
        screen.addnstr(0, 0, lines[0], width - 1, curses.A_BOLD)
        for offset, text in enumerate(lines[1 + top : 1 + top + visible]):
            attribute = curses.A_REVERSE if top + offset == index else curses.A_NORMAL
            screen.addnstr(1 + offset, 0, text, width - 1, attribute)
        if height > 2:
            screen.addnstr(height - 1, 0, PICKER_HELP, width - 1, curses.A_DIM)
        screen.refresh()
        key = screen.getch()
        if key in (curses.KEY_ENTER, 10, 13):
            return index
        if key in (27, ord("q")):
            return None
        index = _pickerMove(index, key, len(rows), visible)


def _pathExpand(stored: str) -> Path:
    """Undo display shortening, which is relative to the discovery home."""
    if stored == "~":
        return HOME
    return HOME / stored[2:] if stored.startswith("~/") else Path(stored)


def _pathShorten(path: str | None) -> str:
    if not isinstance(path, str) or not path or "\0" in path:
        return "?"
    path = os.path.abspath(os.path.expanduser(path))
    home = str(HOME)
    if path == home:
        return "~"
    if path.startswith(home + os.sep):
        return "~" + path[len(home) :]
    return path


def _sessionAppend(
    rows: list[Session],
    agent: str,
    date: datetime,
    directory: str | None,
    session_id: str | None,
    title: str | None = None,
) -> None:
    if not isinstance(session_id, str) or not session_id:
        return

    rows.append(
        {
            "agent": agent,
            "date": date,
            "directory": _pathShorten(directory),
            "session_id": session_id,
            "title": title if isinstance(title, str) else "",
        }
    )


def _tableWidths(
    rendered: list[dict[str, str]], number_width: int, terminal_width: int
) -> tuple[int, int, int, int, int]:
    """Reserve fixed columns and share remaining space between directory and title."""
    agent_width = max(
        len("AGENT"),
        max(len(r["agent"]) for r in rendered),
    )

    date_width = 16

    session_width = max(
        len("SESSION ID"),
        max(len(r["session_id"]) for r in rendered),
    )

    # Reserve the numbered selector and spaces between all six columns.
    fixed_width = number_width + agent_width + date_width + session_width + 10
    remaining = terminal_width - fixed_width

    dir_need = max(len("DIRECTORY"), max(len(r["directory"]) for r in rendered))
    title_need = max(len("TITLE"), max(len(r["title"]) for r in rendered))

    if dir_need + title_need <= remaining:
        return agent_width, date_width, session_width, dir_need, title_need

    # Keep both usable on smaller terminals; titles take what directories leave.
    dir_width = min(dir_need, max(20, remaining // 2))
    title_width = max(20, remaining - dir_width)

    return agent_width, date_width, session_width, dir_width, title_width


def _textClip(text: str, width: int) -> str:
    """Keep the start of descriptive text, which carries most of its meaning."""
    return text if len(text) <= width else text[: max(0, width - 1)] + "…"


def _textTruncate(text: str, width: int) -> str:
    if len(text) <= width:
        return text

    if width <= 3:
        return text[:width]

    left = (width - 1) // 2
    right = width - left - 1

    return text[:left] + "…" + text[-right:]


def _warningReport(message: str) -> None:
    """Report incomplete discovery through the entry point's logging context."""
    getLogger().warning(message)


def _yamlValue(path: Path, wanted: str) -> str | None:
    """
    workspace.yaml only needs a tiny parser here. We deliberately avoid a
    PyYAML dependency because cwd is stored as a simple top-level scalar.
    """
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if ":" not in line:
                    continue

                key, value = line.split(":", 1)

                if key.strip() == wanted:
                    value = value.strip()

                    if (
                        len(value) >= 2
                        and value[0] == value[-1]
                        and value[0] in ("'", '"')
                    ):
                        value = value[1:-1]

                    return value
    except OSError as error:
        _warningReport(f"cannot read session metadata: {path}: {error}")

    return None


def _stdoutClose() -> int:
    """Stop quietly when a downstream reader such as head closes the pipe early."""
    # Redirect so interpreter shutdown cannot flush into the closed pipe again.
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, sys.stdout.fileno())
    return 1


def entryRun() -> int:
    """Console-script entry: a reader closing stdout early ends the run quietly."""
    try:
        return main()
    except BrokenPipeError:
        return _stdoutClose()


if __name__ == "__main__":
    raise SystemExit(entryRun())
