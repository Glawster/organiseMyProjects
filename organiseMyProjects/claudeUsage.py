"""Read Claude's local /usage screen without credentials or model prompts."""

import asyncio
import calendar
import os
import re
import signal
import struct
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

TERMINAL_COLUMNS = 140
TERMINAL_ROWS = 100
MAX_CAPTURE_BYTES = 1024 * 1024

_WINDOW_HEADING = re.compile(
    r"^Current\s+(session|week)(?:\s*\(([^)]+)\))?\s*$", re.IGNORECASE
)
_USED_PERCENT = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s*%\s*used\b", re.IGNORECASE)


@dataclass(frozen=True)
class ClaudeQuota:
    """A provider-labelled used percentage and its independently reported reset."""

    name: str
    used: float
    reset: datetime | None


## public


def claudeScreenParse(text: str, now: datetime | None = None) -> list[ClaudeQuota]:
    """Read quota bars only; costs, cached tokens and contribution shares are ignored."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    windows: dict[str, ClaudeQuota] = {}
    for index, line in enumerate(lines):
        heading = _WINDOW_HEADING.fullmatch(line)
        if heading is None:
            continue
        kind, variant = heading.groups()
        name = "5h" if kind.lower() == "session" else "weekly"
        if variant and variant.casefold() != "all models":
            name += f" ({variant})"
        # The progress bar is immediately below its heading. Never search into
        # other sections or re-use a percentage from a previous redraw.
        if index + 1 >= len(lines):
            return []
        percent = _USED_PERCENT.search(lines[index + 1])
        if percent is None:
            return []
        reset = None
        if index + 2 < len(lines) and lines[index + 2].startswith("Resets"):
            reset = _claudeResetParse(lines[index + 2], now)
        window = ClaudeQuota(name, float(percent.group(1)), reset)
        if name in windows:
            # A duplicate heading indicates an ambiguous screen, not two quotas.
            return []
        windows[name] = window
    # Wait for both account bars, rather than accepting a partial loading frame.
    if "5h" not in windows or "weekly" not in windows:
        return []
    return list(windows.values())


async def claudeUsageRead(executable: str) -> list[ClaudeQuota]:
    """Open a private POSIX terminal, issue only /usage, and discard the screen."""
    if os.name != "posix":
        return []
    try:
        import fcntl
        import pty
        import termios

        import pyte
    except ImportError:
        return []

    master, slave = pty.openpty()
    process = None
    try:
        fcntl.ioctl(
            slave,
            termios.TIOCSWINSZ,
            struct.pack("HHHH", TERMINAL_ROWS, TERMINAL_COLUMNS, 0, 0),
        )
        os.set_blocking(master, False)
        # Safe mode disables project instructions, hooks, MCP servers and plugins.
        # No user task is submitted, and no existing conversation is resumed.
        process = await asyncio.create_subprocess_exec(
            executable,
            "--safe-mode",
            "--no-chrome",
            stdin=slave,
            stdout=slave,
            stderr=slave,
            env={**os.environ, "TERM": "xterm-256color"},
            start_new_session=True,
        )
        os.close(slave)
        slave = -1
        screen = pyte.Screen(TERMINAL_COLUMNS, TERMINAL_ROWS)
        stream = pyte.ByteStream(screen)
        sent = False
        captureBytes = 0
        candidate = None
        stableSince = 0.0
        loop = asyncio.get_running_loop()
        while process.returncode is None:
            try:
                chunk = os.read(master, 65536)
            except BlockingIOError:
                chunk = b""
            except OSError:
                return []
            captureBytes += len(chunk)
            if captureBytes > MAX_CAPTURE_BYTES:
                return []
            if chunk:
                stream.feed(chunk)
            text = "\n".join(screen.display)
            compact = re.sub(r"\s+", "", text).casefold()
            # Do not confirm trust, log in, accept terms or answer startup dialogs.
            if any(
                marker in compact
                for marker in (
                    "doyoutrust",
                    "trustthisfolder",
                    "quicksafetycheck",
                    "signin",
                    "loginto",
                    "accepttheterms",
                )
            ):
                return []
            if not sent:
                if any(line.lstrip().startswith("❯") for line in screen.display):
                    os.write(master, b"/usage")
                    await asyncio.sleep(0.1)
                    os.write(master, b"\r")
                    sent = True
            else:
                windows = claudeScreenParse(text)
                refreshing = any(
                    marker in compact
                    for marker in (
                        "refreshing",
                        "loadingusage",
                        "failedtofetchusage",
                        "unabletoloadusage",
                    )
                )
                if windows and not refreshing:
                    if windows != candidate:
                        candidate = windows
                        stableSince = loop.time()
                    elif loop.time() - stableSince >= 0.4:
                        return windows
                else:
                    candidate = None
            await asyncio.sleep(0.05)
        return []
    finally:
        # The caller's provider deadline cancels this coroutine. Always terminate
        # our own process group and reap it; the user's existing Claude is untouched.
        try:
            if process is not None:
                await _claudeProcessStop(process)
        finally:
            os.close(master)
            if slave != -1:
                os.close(slave)


## utilities


async def _claudeProcessStop(process: asyncio.subprocess.Process) -> None:
    if process.returncode is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        await asyncio.wait_for(process.wait(), 1)
    except asyncio.TimeoutError:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        await process.wait()


def _claudeResetParse(text: str, now: datetime | None) -> datetime | None:
    """Interpret only observed English reset formats with an explicit timezone."""
    match = re.fullmatch(
        r"Resets\s+(?:(\w+)\s+(\d{1,2}),?\s+)?"
        r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)\s*\(([^)]+)\)",
        text,
        re.IGNORECASE,
    )
    if match is None:
        return None
    month, day, hour, minute, meridiem, zone = match.groups()
    try:
        localNow = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo(zone))
        hourValue = int(hour)
        if not 1 <= hourValue <= 12:
            return None
        hourValue = hourValue % 12 + (12 if meridiem.lower() == "pm" else 0)
        reset = localNow.replace(
            hour=hourValue, minute=int(minute or 0), second=0, microsecond=0
        )
        if month:
            months = {
                name.lower(): number
                for number in range(1, 13)
                for name in (calendar.month_abbr[number], calendar.month_name[number])
            }
            reset = reset.replace(month=months[month.lower()], day=int(day))
            if reset < localNow:
                reset = reset.replace(year=reset.year + 1)
        elif reset < localNow:
            reset += timedelta(days=1)
        return reset
    except (ValueError, KeyError, ZoneInfoNotFoundError):
        return None
