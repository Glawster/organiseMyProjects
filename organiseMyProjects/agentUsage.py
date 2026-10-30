"""Read account allowances through provider protocols without handling credentials."""

import asyncio
import json
import math
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

TIMEOUT_SECONDS = 12
MAX_MESSAGE_BYTES = 1024 * 1024


@dataclass(frozen=True)
class QuotaWindow:
    """One independently binding allowance, always expressed as remaining."""

    name: str
    available: float | None
    reset: datetime | None = None


@dataclass(frozen=True)
class AgentAllowance:
    """Account acquisition status, separate from zero and missing quota values."""

    agent: str
    status: str = "UNKNOWN"
    windows: tuple[QuotaWindow, ...] = ()


class ProtocolError(Exception):
    """A safe protocol failure; provider error text is never retained or logged."""

    def __init__(self, unauthenticated: bool = False):
        super().__init__("account quota unavailable")
        self.unauthenticated = unauthenticated


## public


def allowanceCollect() -> list[AgentAllowance]:
    """Query accounts independently with a bounded runtime for each adapter."""
    return asyncio.run(_allowancesCollect())


def allowanceLines(rows: list[AgentAllowance]) -> list[str]:
    """Render aligned quota rows, grouped by agent, with local reset times."""
    records: list[tuple[str, str, str, str]] = []
    for row in rows:
        if not row.windows:
            records.append((row.agent, "—", row.status, "—"))
            continue
        for index, window in enumerate(row.windows):
            available = (
                "UNKNOWN" if window.available is None else f"{window.available:g}%"
            )
            reset = (
                window.reset.astimezone().strftime("%a %d %b %H:%M %Z")
                if window.reset is not None
                else "—"
            )
            # The agent column already supplies this name. Keep distinct model
            # bucket names while removing a redundant default bucket prefix.
            name = window.name.removeprefix(f"{row.agent.lower()} ")
            name = name.replace("_", " ")
            records.append((row.agent if index == 0 else "", name, available, reset))

    headers = ("AGENT", "WINDOW", "AVAILABLE", "RESET (local time)")
    widths = (
        [
            max(len(header), *(len(record[index]) for record in records))
            for index, header in enumerate(headers)
        ]
        if records
        else list(map(len, headers))
    )

    def formatRow(record: tuple[str, str, str, str]) -> str:
        return (
            f"{record[0]:<{widths[0]}}  {record[1]:<{widths[1]}}  "
            f"{record[2]:>{widths[2]}}  {record[3]}"
        )

    lines = [formatRow(headers)]
    for record in records:
        if record[0] and len(lines) > 1:
            lines.append("")
        lines.append(formatRow(record))
    return lines


def percentageAvailable(value: Any, *, meaning: str) -> float | None:
    """Convert an explicitly identified percentage, rejecting non-numeric values."""
    if meaning not in {"used", "remaining"}:
        raise ValueError("percentage meaning must be used or remaining")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value):
        return None
    available = 100 - value if meaning == "used" else value
    return float(max(0, min(100, available)))


def quotaParse(agent: str, response: Any) -> AgentAllowance:
    """Parse only provider fields that explicitly describe account availability."""
    if not isinstance(response, dict):
        return AgentAllowance(agent)
    windows = []
    if agent == "Codex":
        snapshots = response.get("rateLimitsByLimitId")
        if not isinstance(snapshots, dict) or not snapshots:
            snapshots = {"": response.get("rateLimits")}
        # Named buckets may have different model allowances. Do not collapse them
        # or count the legacy aggregate a second time when named buckets exist.
        for bucket, snapshot in snapshots.items():
            if not isinstance(snapshot, dict):
                continue
            for name in ("primary", "secondary"):
                value = snapshot.get(name)
                if not isinstance(value, dict):
                    continue
                duration = value.get("windowDurationMins")
                label = {300: "5h", 10080: "weekly"}.get(duration, name)
                label = f"{_labelClean(bucket)} {label}".strip()
                windows.append(
                    _windowBuild(label, value, "usedPercent", "used", "resetsAt")
                )
    elif agent == "Copilot":
        snapshots = response.get("quotaSnapshots")
        if isinstance(snapshots, dict):
            for name, value in snapshots.items():
                if isinstance(value, dict):
                    windows.append(
                        _windowBuild(
                            _labelClean(name),
                            value,
                            "remainingPercentage",
                            "remaining",
                            "resetDate",
                        )
                    )
    elif agent == "Grok":
        config = response.get("config")
        if isinstance(config, dict):
            period = config.get("currentPeriod")
            reset = period.get("end") if isinstance(period, dict) else None
            windows.append(
                QuotaWindow(
                    "weekly",
                    percentageAvailable(
                        config.get("creditUsagePercent"), meaning="used"
                    ),
                    _resetParse(reset),
                )
            )
    return AgentAllowance(agent, "OK" if windows else "UNKNOWN", tuple(windows))


## acquisition


async def _allowancesCollect() -> list[AgentAllowance]:
    return list(
        await asyncio.gather(
            *(
                _providerCollect(agent)
                for agent in ("Claude", "Codex", "Grok", "Copilot")
            )
        )
    )


async def _providerCollect(agent: str) -> AgentAllowance:
    executable = shutil.which(agent.lower())
    if executable is None:
        return AgentAllowance(agent, "NOT INSTALLED")
    try:
        return await asyncio.wait_for(
            _providerQuery(agent, executable), TIMEOUT_SECONDS
        )
    except ProtocolError as error:
        return AgentAllowance(
            agent, "NOT AUTHENTICATED" if error.unauthenticated else "UNKNOWN"
        )
    except (
        OSError,
        ValueError,
        TypeError,
        OverflowError,
        asyncio.TimeoutError,
        asyncio.IncompleteReadError,
        asyncio.LimitOverrunError,
    ):
        # Never expose exception messages: provider errors can contain account or
        # authorization details. A failed account must not hide the other rows.
        return AgentAllowance(agent)


async def _providerQuery(agent: str, executable: str) -> AgentAllowance:
    if agent == "Claude":
        # Check supported auth status before opening the user-approved /usage
        # terminal fallback; authentication and credentials remain CLI-owned.
        process = await asyncio.create_subprocess_exec(
            executable,
            "auth",
            "status",
            "--json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            output, _ = await process.communicate()
            status = json.loads(output)
            authenticated = status.get("loggedIn") if isinstance(status, dict) else None
        finally:
            await _processStop(process)
        if authenticated is False:
            return AgentAllowance(agent, "NOT AUTHENTICATED")
        if authenticated is not True:
            return AgentAllowance(agent)
        from organiseMyProjects.claudeUsage import claudeUsageRead

        captured = await claudeUsageRead(executable)
        windows = tuple(
            QuotaWindow(
                window.name,
                percentageAvailable(window.used, meaning="used"),
                window.reset,
            )
            for window in captured
        )
        return AgentAllowance(agent, "OK" if windows else "UNKNOWN", windows)
    commands = {
        "Codex": [executable, "app-server", "--stdio"],
        "Grok": [executable, "agent", "--no-leader", "stdio"],
        "Copilot": [
            executable,
            "--headless",
            "--stdio",
            "--no-auto-update",
            "--log-level",
            "none",
        ],
    }
    process = await asyncio.create_subprocess_exec(
        *commands[agent],
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
        limit=MAX_MESSAGE_BYTES,
    )
    rpc = _QuotaRpc(
        process,
        framed=agent == "Copilot",
        authCodes=(401, -32000) if agent == "Grok" else (401,),
    )
    try:
        if agent == "Codex":
            await rpc.request(
                "initialize", {"clientInfo": {"name": "agentSessions", "version": "1"}}
            )
            await rpc.send({"jsonrpc": "2.0", "method": "initialized"})
            account = await rpc.request("account/read", {"refreshToken": False})
            if account.get("account", "missing") is None:
                status = (
                    "UNKNOWN"
                    if account.get("requiresOpenaiAuth") is False
                    else "NOT AUTHENTICATED"
                )
                return AgentAllowance(agent, status)
            result = await rpc.request("account/rateLimits/read", {})
        elif agent == "Grok":
            await rpc.request(
                "initialize",
                {
                    "protocolVersion": 1,
                    "clientCapabilities": {},
                    "clientInfo": {"name": "agentSessions", "version": "1"},
                },
            )
            result = await rpc.request("_x.ai/billing", {})
        else:
            status = await rpc.request("auth.getStatus", {})
            if status.get("isAuthenticated") is False:
                return AgentAllowance(agent, "NOT AUTHENTICATED")
            result = await rpc.request("account.getQuota", {})
        return quotaParse(agent, result)
    finally:
        await _processStop(process)


async def _processStop(process: asyncio.subprocess.Process) -> None:
    """Reap the short-lived protocol client even on timeout or cancellation."""
    if process.returncode is None:
        try:
            process.terminate()
        except ProcessLookupError:
            pass
        try:
            await asyncio.wait_for(process.communicate(), 1)
        except asyncio.TimeoutError:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            await process.communicate()


class _QuotaRpc:
    """Minimal read-only JSON-RPC client, supporting CLI and SDK stdio framing."""

    def __init__(
        self,
        process: asyncio.subprocess.Process,
        framed: bool = False,
        authCodes: tuple[int, ...] = (401,),
    ):
        self.process = process
        self.framed = framed
        self.sequence = 0
        self.authCodes = authCodes

    async def send(self, message: dict) -> None:
        data = json.dumps(message).encode("utf-8")
        wire = (
            f"Content-Length: {len(data)}\r\n\r\n".encode() + data
            if self.framed
            else data + b"\n"
        )
        self.process.stdin.write(wire)
        await self.process.stdin.drain()

    async def request(self, method: str, params: dict) -> dict:
        self.sequence += 1
        requestId = self.sequence
        await self.send(
            {"jsonrpc": "2.0", "id": requestId, "method": method, "params": params}
        )
        while True:
            message = await self._read()
            # Never run tools or approve a provider request. These processes are
            # used only for account reads and do not create a model session.
            if "method" in message:
                if "id" in message:
                    await self.send(
                        {
                            "jsonrpc": "2.0",
                            "id": message["id"],
                            "error": {
                                "code": -32601,
                                "message": "unsupported client request",
                            },
                        }
                    )
                continue
            if message.get("id") != requestId:
                continue
            if "error" in message:
                error = message["error"]
                code = error.get("code") if isinstance(error, dict) else None
                # JSON-RPC auth-required (ACP) and HTTP authentication statuses.
                raise ProtocolError(unauthenticated=code in self.authCodes)
            result = message.get("result")
            if not isinstance(result, dict):
                raise ProtocolError()
            return result

    async def _read(self) -> dict:
        stream = self.process.stdout
        if self.framed:
            header = await stream.readuntil(b"\r\n\r\n")
            lengths = [
                line.split(b":", 1)[1].strip()
                for line in header.split(b"\r\n")
                if line.lower().startswith(b"content-length:")
            ]
            if len(lengths) != 1:
                raise ProtocolError()
            length = int(lengths[0])
            if length < 0 or length > MAX_MESSAGE_BYTES:
                raise ProtocolError()
            data = await stream.readexactly(length)
        else:
            data = await stream.readline()
        if not data:
            raise ProtocolError()
        message = json.loads(data)
        if not isinstance(message, dict):
            raise ProtocolError()
        return message


## parsing


def _labelClean(value: Any) -> str:
    return "".join(char for char in str(value) if char.isprintable())[:40]


def _resetParse(value: Any) -> datetime | None:
    try:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, timezone.utc)
        if isinstance(value, str):
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            # A timezone-free provider timestamp is ambiguous; don't invent UTC.
            return parsed if parsed.tzinfo is not None else None
    except (ValueError, OverflowError, OSError):
        pass
    return None


def _windowBuild(
    name: str, value: dict, field: str, meaning: str, reset: str
) -> QuotaWindow:
    return QuotaWindow(
        name,
        percentageAvailable(value.get(field), meaning=meaning),
        _resetParse(value.get(reset)),
    )
