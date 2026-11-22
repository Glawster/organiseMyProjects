"""Claude /usage text and actual terminal capture, using synthetic screen evidence."""

import asyncio
import importlib
import os
import sys
from datetime import datetime, timezone

import pytest

from organiseMyProjects import agentUsage
from organiseMyProjects.claudeUsage import claudeScreenParse

NOW = datetime(2026, 10, 30, 11, 35, tzinfo=timezone.utc)
SCREEN = """Settings  Status  Config  Usage  Stats
Session
Total cost: $3.96
Prompt cache: 96% of input tokens from cache
Current session
█████                                             10% used
Resets 2:30pm (Europe/London)
Current week (all models)
███████████                                       23% used
Resets Nov 1, 7pm (Europe/London)
What's contributing to your usage?
65% Start fresh when you switch tasks
Usage credits
Esc to cancel
"""


def testScreenshotQuotaMeaningAndResets():
    windows = claudeScreenParse(SCREEN, NOW)
    assert [(w.name, w.used) for w in windows] == [("5h", 10), ("weekly", 23)]
    assert [
        agentUsage.percentageAvailable(w.used, meaning="used") for w in windows
    ] == [90, 77]
    assert windows[0].reset == datetime(2026, 10, 30, 14, 30, tzinfo=timezone.utc)
    assert windows[1].reset == datetime(2026, 11, 1, 19, tzinfo=timezone.utc)


def testAdditionalBindingWindowAndUnknownReset():
    extra = "\nCurrent week (Sonnet only)\n████ 7.5% used\nResets unknown\n"
    windows = claudeScreenParse(SCREEN + extra, NOW)
    assert windows[-1].name == "weekly (Sonnet only)"
    assert windows[-1].used == 7.5
    assert windows[-1].reset is None


@pytest.mark.parametrize(
    "text",
    [
        "Total tokens: 100000\nTotal cost: $10\n96% cached\n",
        "Current session\nLoading…\nCurrent week (all models)\n23% used\n",
        "Current session\n10% used\n",
        SCREEN.replace("23% used", "No account allowance available"),
        SCREEN + "\nCurrent session\n11% used\n",
        SCREEN.replace("10% used", "10% remaining"),
    ],
)
def testIncompleteOrAmbiguousScreenIsUnknown(text):
    assert claudeScreenParse(text, NOW) == []


@pytest.mark.parametrize(
    "reset,now,expected",
    [
        ("12am (Europe/London)", NOW, datetime(2026, 10, 31, 0, tzinfo=timezone.utc)),
        ("12pm (Europe/London)", NOW, datetime(2026, 10, 30, 12, tzinfo=timezone.utc)),
        (
            "2:30pm (America/New_York)",
            NOW,
            datetime(2026, 10, 30, 18, 30, tzinfo=timezone.utc),
        ),
        (
            "Jan 1, 7pm (Europe/London)",
            datetime(2026, 12, 31, 11, tzinfo=timezone.utc),
            datetime(2027, 1, 1, 19, tzinfo=timezone.utc),
        ),
        ("14:30 (Europe/London)", NOW, None),
        ("13pm (Europe/London)", NOW, None),
        ("2:99pm (Europe/London)", NOW, None),
        ("2pm (Invalid/Timezone)", NOW, None),
        ("2pm", NOW, None),
    ],
)
def testResetFormats(reset, now, expected):
    screen = SCREEN.replace("2:30pm (Europe/London)", reset)
    assert claudeScreenParse(screen, now)[0].reset == expected


def _fakeClaudeWrite(tmp_path, body):
    executable = tmp_path / "claude"
    executable.write_text(f"#!{sys.executable}\n" + body)
    executable.chmod(0o755)
    return executable


def testRealPtyCaptureAndRedraw(tmp_path, monkeypatch):
    pytest.importorskip(
        "pyte", reason="pyte is required to verify terminal screen capture"
    )
    if os.name != "posix":
        pytest.skip("POSIX pseudo-terminal capture is unavailable")
    # The fake CLI verifies that auth is read without extracting credentials, the
    # only submitted input is /usage, and terminal redraws overwrite stale bars.
    script = """
import os, sys, tty, time
if sys.argv[1:] == ["auth", "status", "--json"]:
    print('{"loggedIn":true}')
    sys.exit(0)
assert sys.argv[1:] == ["--safe-mode", "--no-chrome"]
assert os.isatty(0) and os.isatty(1)
tty.setraw(0)
os.write(1, "❯ ".encode())
command = b""
while not command.endswith(b"\\r"):
    command += os.read(0, 100)
assert command == b"/usage\\r"
# An initial loading frame must not escape as an account result.
os.write(1, b"\\x1b[2J\\x1b[HCurrent session\\r\\nLoading usage...")
time.sleep(.1)
"""
    script += f"os.write(1, b'\\x1b[2J\\x1b[H' + {SCREEN!r}.replace('\\n', '\\r\\n').encode())\n"
    # A percentage-only repaint must replace 10 with 12, not leave stale 10.
    script += """
time.sleep(.1)
os.write(1, b"\\x1b[6;1H\\x1b[2K12% used\\r\\n")
time.sleep(30)
"""
    executable = _fakeClaudeWrite(tmp_path, script)
    monkeypatch.setattr(agentUsage.shutil, "which", lambda name: str(executable))
    row = asyncio.run(agentUsage._providerCollect("Claude"))
    assert row.status == "OK"
    assert [w.available for w in row.windows] == [88, 77]


@pytest.mark.parametrize(
    "screen",
    [
        "Quick safety check: do you trust this folder?\n❯ Yes",
        "Sign in to Claude\n❯ Continue",
        "Accept the terms\n❯ Yes",
    ],
)
def testNoStartupDialogIsAccepted(tmp_path, screen):
    pytest.importorskip(
        "pyte", reason="pyte is required to verify terminal screen capture"
    )
    if os.name != "posix":
        pytest.skip("POSIX pseudo-terminal capture is unavailable")
    from organiseMyProjects.claudeUsage import claudeUsageRead

    inputFile = tmp_path / "unexpectedInput"
    script = f"""
import os, tty, select
tty.setraw(0)
os.write(1, {screen!r}.encode())
if select.select([0], [], [], 2)[0]:
    open({str(inputFile)!r}, 'wb').write(os.read(0, 100))
"""
    executable = _fakeClaudeWrite(tmp_path, script)
    assert asyncio.run(asyncio.wait_for(claudeUsageRead(str(executable)), 3)) == []
    assert not inputFile.exists()


def testStalledPtyIsReaped(tmp_path, monkeypatch):
    pytest.importorskip(
        "pyte", reason="pyte is required to verify terminal screen capture"
    )
    if os.name != "posix":
        pytest.skip("POSIX pseudo-terminal capture is unavailable")
    from organiseMyProjects.claudeUsage import claudeUsageRead

    pidFile = tmp_path / "pid"
    executable = _fakeClaudeWrite(
        tmp_path,
        f"import os,time\nopen({str(pidFile)!r},'w').write(str(os.getpid()))\ntime.sleep(30)\n",
    )

    async def verify():
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(claudeUsageRead(str(executable)), 0.3)

    asyncio.run(verify())
    with pytest.raises(ProcessLookupError):
        os.kill(int(pidFile.read_text()), 0)


def testUnsupportedPlatformIsUnknown(monkeypatch):
    module = importlib.import_module("organiseMyProjects.claudeUsage")
    monkeypatch.setattr(module.os, "name", "nt")
    assert asyncio.run(module.claudeUsageRead("unused")) == []
