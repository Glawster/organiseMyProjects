"""Exercise session discovery with synthetic stores and the real logging dependency."""

import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import quote

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "agentSessions"
COMMAND = [sys.executable, "-m", "organiseMyProjects.agentSessions"]
SESSION_ID = "12345678-1234-1234-1234-123456789abc"


@pytest.fixture
def sessions(tmp_path, monkeypatch):
    """Load the command module against an isolated home."""
    module = importlib.import_module("organiseMyProjects.agentSessions")
    monkeypatch.setattr(module, "HOME", tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("COPILOT_HOME", str(tmp_path / ".copilot"))
    module.setApplication("agentSessions", logDir=tmp_path / "logs")
    return module


def _fixtureWrite(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def teststoresCompose(sessions, tmp_path, capsys):
    """Real parsers compose into the listing and never rewrite source evidence."""
    cwd = str(tmp_path / "work")
    codex = _fixtureWrite(
        tmp_path / ".codex/sessions/2026/rollout-one.jsonl",
        "broken\n"
        + json.dumps(
            {"type": "session_meta", "payload": {"id": SESSION_ID, "cwd": cwd}}
        ),
    )
    claude = _fixtureWrite(
        tmp_path / f".claude/projects/work/{SESSION_ID}.jsonl", json.dumps({"cwd": cwd})
    )
    grok = _fixtureWrite(
        tmp_path / f".grok/sessions/{quote(cwd, safe='')}/{SESSION_ID}/summary.json",
        "{}",
    )
    copilot = _fixtureWrite(
        tmp_path / f".copilot/session-state/{SESSION_ID}/events.jsonl",
        json.dumps({"type": "session.start", "data": {"context": {"cwd": cwd}}}),
    )
    _fixtureWrite(copilot.parent / "workspace.yaml", f'cwd: "{cwd}"\n')
    _fixtureWrite(grok.parent / f"subagents/{SESSION_ID}/summary.json", "{}")
    before = {
        p: p.read_bytes()
        for p in tmp_path.rglob("*")
        if p.is_file() and "logs" not in p.parts
    }

    rows = sessions.sessionsCollect()
    sessions.tablePrint(rows, full_ids=True)

    assert {r["agent"] for r in rows} == {"Codex", "Claude", "Grok", "Copilot"}
    assert len(rows) == 4
    assert all(
        r["directory"] == "~/work" and r["session_id"] == SESSION_ID for r in rows
    )
    assert SESSION_ID in capsys.readouterr().out
    assert all(p.read_bytes() == content for p, content in before.items())


def testmalformedAndFallback(sessions, tmp_path):
    _fixtureWrite(tmp_path / ".codex/sessions/rollout-array.jsonl", "[]")
    _fixtureWrite(
        tmp_path / ".codex/sessions/rollout-null.jsonl",
        '{"type":"session_meta","payload":null}',
    )
    _fixtureWrite(
        tmp_path / ".codex/sessions/rollout-number.jsonl",
        '{"type":"session_meta","payload":{"id":12}}',
    )
    _fixtureWrite(tmp_path / ".claude/projects/work/not-a-session.jsonl", "{}")
    _fixtureWrite(
        tmp_path / ".copilot/session-state/empty/workspace.yaml", "cwd: /unused"
    )
    _fixtureWrite(
        tmp_path / f".copilot/session-state/{SESSION_ID}/events.jsonl",
        "bad\n[]\n"
        + json.dumps(
            {"type": "session.start", "data": {"workingDirectory": "/fallback"}}
        ),
    )
    rows = sessions.sessionsCollect()
    assert len(rows) == 1
    assert rows[0]["directory"] == "/fallback"


def testlatestAndRendering(sessions, tmp_path, capsys):
    path = _fixtureWrite(tmp_path / "stamp", "")
    older = {
        "agent": "Codex",
        "directory": "/work",
        "session_id": "old",
        "date": sessions.datetime.min,
        "title": "",
    }
    newer = {**older, "session_id": SESSION_ID, "date": sessions._fileDate(path)}
    assert sessions.sessionsLatest([older, newer, older]) == [newer]
    rows = [older, newer]
    sessions.tablePrint(rows)
    assert rows == [older, newer]
    assert "12345678…" in capsys.readouterr().out
    assert sessions._textTruncate("abcdefghijk", 7) == "abc…ijk"
    assert sessions._textTruncate("abcdef", 3) == "abc"
    assert sessions._pathShorten(str(tmp_path)) == "~"
    assert sessions._pathShorten(None) == "?"
    assert sessions._pathShorten("bad\0path") == "?"


def testioFailureReports(sessions, tmp_path, caplog):
    assert sessions._jsonFirst(tmp_path / "missing") is None
    assert sessions._fileDate(tmp_path / "missing") == sessions.datetime.min
    assert sessions._yamlValue(tmp_path / "missing", "cwd") is None
    assert "cannot read session" in caplog.text


@pytest.mark.parametrize(
    "options",
    [[], ["--all", "--full"], ["--quiet"], ["--verbose"], ["--help"], ["--version"]],
)
def testcommandProductionPath(tmp_path, options):
    """Run the entry point with real logging and an empty isolated home."""
    env = {
        **os.environ,
        "HOME": str(tmp_path),
        "PYTHONPATH": str(REPO_ROOT),
        "COPILOT_HOME": str(tmp_path / ".copilot"),
    }
    result = subprocess.run(
        [*COMMAND, *options], env=env, text=True, capture_output=True
    )
    assert result.returncode == 0, result.stderr
    if "--help" not in options and "--version" not in options:
        assert "No local agent sessions found." in result.stdout
        assert list((tmp_path / ".local/state/agentSessions").glob("*.log"))


def testClosedPipeIsQuiet(tmp_path):
    """A reader closing stdout early, as head does, must not produce a traceback."""
    env = {
        **os.environ,
        "HOME": str(tmp_path),
        "PYTHONPATH": str(REPO_ROOT),
        "COPILOT_HOME": str(tmp_path / ".copilot"),
    }
    process = subprocess.Popen(
        [*COMMAND, "--all", "--history"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    process.stdout.close()
    stderr = process.stderr.read().decode()
    process.stderr.close()
    assert process.wait() == 1
    assert "Traceback" not in stderr and "BrokenPipeError" not in stderr


def testEntryPointComposition(sessions, tmp_path, monkeypatch, capsys):
    path = tmp_path / ".codex/sessions/rollout-real.jsonl"
    _fixtureWrite(
        path,
        json.dumps(
            {
                "type": "session_meta",
                "payload": {"id": SESSION_ID, "cwd": str(tmp_path)},
            }
        ),
    )
    for options in (["--all", "--full"], [], ["--verbose"], ["--quiet"]):
        monkeypatch.setattr(sys, "argv", [SCRIPT, *options])
        assert sessions.main() == 0
        assert "Codex" in capsys.readouterr().out


def testMissingStoresAndNestedValues(sessions, tmp_path, capsys):
    assert sessions.sessionsCollect() == []
    sessions.tablePrint([])
    assert "No local agent sessions" in capsys.readouterr().out
    assert (
        sessions._jsonFind([None, {"nested": [{"cwd": "/nested"}]}], ("cwd",))
        == "/nested"
    )
    assert sessions._jsonFind({"cwd": 42}, ("cwd",)) is None
    assert (
        sessions._yamlValue(
            _fixtureWrite(tmp_path / "workspace.yaml", "comment\nother: yes\n"), "cwd"
        )
        is None
    )
    assert (
        sessions._jsonFirst(_fixtureWrite(tmp_path / "empty.jsonl", "\ninvalid\n"))
        is None
    )


def testStoreFailureIsolated(sessions, monkeypatch, caplog):
    def fail(rows):
        raise PermissionError("synthetic inaccessible store")

    monkeypatch.setattr(sessions, "_claudeCollect", fail)
    assert sessions.sessionsCollect() == []
    assert "cannot scan session store" in caplog.text


def testAgentOrderAndSelectors(sessions, tmp_path, monkeypatch, capsys):
    """Numbered output and clean ID extraction agree across real provider stores."""
    _fixtureWrite(
        tmp_path / f".claude/projects/work/{SESSION_ID}.jsonl",
        json.dumps({"cwd": str(tmp_path)}),
    )
    for name, stamp in (("older", 100), ("newer", 200)):
        path = _fixtureWrite(
            tmp_path / f".codex/sessions/rollout-{name}.jsonl",
            json.dumps(
                {
                    "type": "session_meta",
                    "payload": {"id": name + "-full-resume-id", "cwd": str(tmp_path)},
                }
            ),
        )
        os.utime(path, (stamp, stamp))
    monkeypatch.setattr(sys, "argv", [SCRIPT, "--history", "--full"])
    assert sessions.main() == 0
    output = capsys.readouterr().out
    assert (
        output.index("Claude")
        < output.index("newer-full-resume-id")
        < output.index("older-full-resume-id")
    )


@pytest.mark.parametrize("row", ["0", "-1", "100", "invalid"])
def testInvalidSelector(sessions, monkeypatch, capsys, row):
    monkeypatch.setattr(sys, "argv", [SCRIPT, "--id", row])
    with pytest.raises(SystemExit) as error:
        sessions.main()
    assert error.value.code == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "error:" in output.err


def testCurrentDirectoryAndAll(sessions, tmp_path, monkeypatch, capsys):
    """CLI scopes listings to cwd unless explicitly expanded."""
    for name, cwd in (("here", tmp_path), ("elsewhere", tmp_path / "other")):
        _fixtureWrite(
            tmp_path / f".codex/sessions/rollout-{name}.jsonl",
            json.dumps(
                {
                    "type": "session_meta",
                    "payload": {"id": name + "-resume-id", "cwd": str(cwd)},
                }
            ),
        )
    monkeypatch.setattr(sys, "argv", [SCRIPT, "--full"])
    assert sessions.main() == 0
    output = capsys.readouterr().out
    assert "here-resume-id" in output
    assert "elsewhere-resume-id" not in output
    resumed = []
    monkeypatch.setattr(sys, "argv", [SCRIPT, "--id", "1"])
    monkeypatch.setattr(sessions, "sessionResume", lambda row: resumed.append(row) or 0)
    assert sessions.main() == 0
    assert [row["session_id"] for row in resumed] == ["here-resume-id"]
    monkeypatch.setattr(sys, "argv", [SCRIPT, "--all", "--full"])
    assert sessions.main() == 0
    output = capsys.readouterr().out
    assert "here-resume-id" in output and "elsewhere-resume-id" in output


def testTitlesFromEachStore(sessions, tmp_path, monkeypatch, capsys):
    """Each provider's descriptive text reaches the listing with its precedence rules."""
    cwd = str(tmp_path)
    _fixtureWrite(
        tmp_path / ".codex/sessions/rollout-titled.jsonl",
        json.dumps({"type": "session_meta", "payload": {"id": "codex-id", "cwd": cwd}}),
    )
    _fixtureWrite(
        tmp_path / ".codex/session_index.jsonl",
        "broken\n"
        + "\n".join(
            json.dumps({"id": "codex-id", "thread_name": name})
            for name in ("Original thread", "Renamed thread")
        ),
    )
    claude_records = [
        {"cwd": cwd},
        {"type": "last-prompt", "lastPrompt": "Opening prompt"},
        {"type": "custom-title", "customTitle": "User rename"},
        {"type": "ai-title", "aiTitle": "Generated title"},
        {"type": "last-prompt", "lastPrompt": "ok"},
    ]
    _fixtureWrite(
        tmp_path / f".claude/projects/work/{SESSION_ID}.jsonl",
        "\n".join(json.dumps(r, separators=(",", ":")) for r in claude_records),
    )
    untitled = "87654321-1234-1234-1234-123456789abc"
    _fixtureWrite(
        tmp_path / f".claude/projects/work/{untitled}.jsonl",
        "\n".join(
            json.dumps(r, separators=(",", ":"))
            for r in [claude_records[0], claude_records[1], claude_records[4]]
        ),
    )
    _fixtureWrite(
        tmp_path / f".grok/sessions/{quote(cwd, safe='')}/{SESSION_ID}/summary.json",
        json.dumps({"session_summary": "Grok summary"}),
    )
    copilot = tmp_path / f".copilot/session-state/{SESSION_ID}"
    _fixtureWrite(copilot / "events.jsonl", "")
    _fixtureWrite(copilot / "workspace.yaml", f"cwd: {cwd}\nname: 'Copilot name'\n")

    titles = {
        (r["agent"], r["session_id"]): r["title"] for r in sessions.sessionsCollect()
    }
    assert titles == {
        ("Codex", "codex-id"): "Renamed thread",
        ("Claude", SESSION_ID): "User rename",
        ("Claude", untitled): "Opening prompt",
        ("Grok", SESSION_ID): "Grok summary",
        ("Copilot", SESSION_ID): "Copilot name",
    }
    monkeypatch.setattr(sys, "argv", [SCRIPT, "--history"])
    assert sessions.main() == 0
    output = capsys.readouterr().out
    assert "TITLE" in output and "Grok summary" in output


def testTitleLayout(sessions, monkeypatch, capsys):
    row = {
        "agent": "Codex",
        "directory": "/work",
        "session_id": SESSION_ID,
        "date": sessions.datetime.min,
        "title": "multi\nline   " + "x" * 200,
    }
    monkeypatch.setattr(
        sessions.shutil,
        "get_terminal_size",
        lambda fallback: os.terminal_size((80, 24)),
    )
    sessions.tablePrint([row])
    lines = capsys.readouterr().out.splitlines()
    assert lines[1].endswith("…") and "multi line x" in lines[1]
    assert len(lines[1]) <= 80
    assert sessions._textClip("abcdef", 4) == "abc…"
    assert sessions._claudeTitle(Path("/nonexistent/session.jsonl")) is None


def testSearchSelectsMatches(sessions, tmp_path, monkeypatch, capsys):
    """Search filters by title or directory before latest selection and --id."""
    names = (
        ("older-match", 100, "MigrateToRaid destinations", tmp_path),
        ("newest-other", 300, "Unrelated work", tmp_path / "migrateToRaid"),
        ("newer-match", 200, "migratetoraid mapping", tmp_path),
    )
    index = []
    for name, stamp, title, cwd in names:
        path = _fixtureWrite(
            tmp_path / f".codex/sessions/rollout-{name}.jsonl",
            json.dumps(
                {"type": "session_meta", "payload": {"id": name, "cwd": str(cwd)}}
            ),
        )
        os.utime(path, (stamp, stamp))
        index.append(json.dumps({"id": name, "thread_name": title}))
    _fixtureWrite(tmp_path / ".codex/session_index.jsonl", "\n".join(index))

    for options, expected in (
        (["--search", "MIGRATETORAID", "--id", "1"], "newer-match"),
        (
            ["--search", "migrateToRaid", "--history", "--id", "2"],
            "older-match",
        ),
        (
            ["--all", "--search", "migrateToRaid", "--id", "1"],
            "newest-other",
        ),
    ):
        monkeypatch.setattr(sys, "argv", [SCRIPT, *options])
        resumed = []
        monkeypatch.setattr(
            sessions, "sessionResume", lambda row: resumed.append(row) or 0
        )
        assert sessions.main() == 0
        assert [row["session_id"] for row in resumed] == [expected]
    monkeypatch.setattr(sys, "argv", [SCRIPT, "--search", "absent"])
    assert sessions.main() == 0
    assert "No local agent sessions found." in capsys.readouterr().out


class FakeScreen:
    """Minimal curses screen: scripted keys in, drawn text and highlights out."""

    def __init__(self, sessions, keys, height=6, width=100):
        self.curses = sessions.curses
        self.keys = list(keys)
        self.size = (height, width)
        self.drawn = []

    def getmaxyx(self):
        return self.size

    def keypad(self, enabled):
        pass

    def erase(self):
        self.drawn = []

    def addnstr(self, y, x, text, width, attribute):
        assert len(text[:width]) < self.size[1]
        self.drawn.append((y, text[:width], attribute))

    def refresh(self):
        pass

    def getch(self):
        return self.keys.pop(0)

    def highlighted(self):
        return [text for _, text, attr in self.drawn if attr == self.curses.A_REVERSE]


def _pickerRows(sessions, count):
    return [
        {
            "agent": "Claude",
            "directory": "~",
            "session_id": f"{n:08d}-1234-1234-1234-123456789abc",
            "date": sessions.datetime(2026, 1, 1, 0, count - n),
            "title": f"Title {n}",
        }
        for n in range(count)
    ]


def testPickerNavigation(sessions, monkeypatch):
    """Arrow, vi, paging and end keys move and scroll a highlight that Enter returns."""
    curses = sessions.curses

    def noCursor(visibility):
        raise curses.error("synthetic terminal without cursor control")

    monkeypatch.setattr(curses, "curs_set", noCursor)
    rows = _pickerRows(sessions, 10)
    for keys, expected in (
        ([10], 0),
        ([curses.KEY_DOWN, ord("j"), curses.KEY_UP, 13], 1),
        ([curses.KEY_UP, curses.KEY_ENTER], 0),
        ([curses.KEY_NPAGE, curses.KEY_NPAGE, 10], 6),
        ([curses.KEY_END, ord("k"), curses.KEY_PPAGE, 10], 5),
        ([curses.KEY_END, ord("x"), curses.KEY_HOME, 10], 0),
    ):
        assert sessions._pickerRun(FakeScreen(sessions, keys), rows) == expected
    screen = FakeScreen(sessions, [curses.KEY_END, ord("q")])
    assert sessions._pickerRun(screen, rows) is None
    # The last row stays visible after scrolling, with the help line kept.
    assert screen.highlighted() == [screen.drawn[-2][1]]
    assert "Title 9" in screen.highlighted()[0]
    assert "q cancel" in screen.drawn[-1][1]
    assert sessions._pickerRun(FakeScreen(sessions, [27]), rows) is None


def testResumeCommands(sessions, tmp_path, monkeypatch, caplog):
    """Each agent resumes with its own syntax from the session's directory."""
    row = _pickerRows(sessions, 1)[0]
    expected = {
        "Claude": ["claude", "--resume", row["session_id"]],
        "Codex": ["codex", "resume", row["session_id"]],
        "Copilot": ["copilot", f"--resume={row['session_id']}"],
        "Grok": ["grok", "--resume", row["session_id"]],
    }
    for agent, command in expected.items():
        assert sessions.resumeCommand({**row, "agent": agent}) == command

    calls = []
    monkeypatch.setattr(sessions.os, "chdir", lambda path: calls.append(path))
    monkeypatch.setattr(
        sessions.os, "execvp", lambda name, args: calls.append((name, args))
    )
    (tmp_path / "work").mkdir()
    assert sessions.sessionResume({**row, "directory": "~/work"}) == 0
    assert calls == [tmp_path / "work", ("claude", expected["Claude"])]

    assert sessions.sessionResume({**row, "directory": "?"}) == 1
    assert sessions.sessionResume({**row, "directory": "~/gone"}) == 1
    assert "working directory not found" in caplog.text

    def missing(name, args):
        raise FileNotFoundError(2, "No such file or directory")

    monkeypatch.setattr(sessions.os, "execvp", missing)
    assert sessions.sessionResume(row) == 1
    assert "cannot resume: claude" in caplog.text


def testResumeOption(sessions, tmp_path, monkeypatch, capsys):
    """--resume picks from the filtered listing and hands the choice to resume."""
    monkeypatch.setattr(sys, "argv", [SCRIPT, "--resume"])
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    assert sessions.main() == 0
    assert capsys.readouterr().out == "No local agent sessions found.\n"

    _fixtureWrite(
        tmp_path / ".codex/sessions/rollout-pick.jsonl",
        json.dumps(
            {"type": "session_meta", "payload": {"id": "pick-id", "cwd": str(tmp_path)}}
        ),
    )
    offered, resumed = [], []

    def pick(rows):
        offered.extend(rows)
        return rows[0]

    monkeypatch.setattr(sessions, "sessionPick", pick)
    monkeypatch.setattr(sessions, "sessionResume", lambda row: resumed.append(row) or 7)
    assert sessions.main() == 7
    assert [r["session_id"] for r in offered] == ["pick-id"] and resumed == offered
    monkeypatch.setattr(sessions, "sessionPick", lambda rows: None)
    assert sessions.main() == 0
    assert capsys.readouterr().out == ""


def testIdOptionResumesNumberedRow(sessions, tmp_path, monkeypatch):
    """--id bypasses the picker and resumes the numbered filtered row."""
    _fixtureWrite(
        tmp_path / ".codex/sessions/rollout-direct.jsonl",
        json.dumps(
            {
                "type": "session_meta",
                "payload": {"id": "direct-id", "cwd": str(tmp_path)},
            }
        ),
    )
    resumed = []
    monkeypatch.setattr(sys, "argv", [SCRIPT, "--id", "1"])
    monkeypatch.setattr(sessions, "sessionResume", lambda row: resumed.append(row) or 7)
    assert sessions.main() == 7
    assert [row["session_id"] for row in resumed] == ["direct-id"]


@pytest.mark.parametrize("options", [["--resume"], ["--resume", "--id", "1"]])
def testResumeNeedsTerminal(tmp_path, options):
    env = {**os.environ, "HOME": str(tmp_path), "PYTHONPATH": str(REPO_ROOT)}
    result = subprocess.run(
        [*COMMAND, *options],
        env=env,
        text=True,
        capture_output=True,
        stdin=subprocess.DEVNULL,
    )
    assert result.returncode == 2
    assert result.stdout == "" and "error:" in result.stderr


def testDirectoryIdentity(sessions, tmp_path):
    alias = tmp_path / "alias"
    alias.symlink_to(tmp_path, target_is_directory=True)
    rows = [
        {"directory": "~"},
        {"directory": "~/alias"},
        {"directory": "~/child"},
        {"directory": "?"},
        {"directory": str(tmp_path) + "-other"},
    ]
    assert sessions.sessionsForDirectory(rows, tmp_path) == rows[:2]


def testDirectoryShowsFolderName(sessions):
    """The listing shows only the folder name; the row keeps the full path."""
    row = {
        "agent": "Codex",
        "directory": "~/Source/organiseMyProjects",
        "session_id": SESSION_ID,
        "date": sessions.datetime.min,
        "title": "",
    }
    lines = sessions.tableLines([row, {**row, "directory": "~"}], terminal_width=120)
    assert "organiseMyProjects" in lines[1] and "Source" not in lines[1]
    assert "  ~  " in lines[2]
    assert row["directory"] == "~/Source/organiseMyProjects"
