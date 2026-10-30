"""Account quota semantics and real stdio protocol composition, without secrets."""

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from organiseMyProjects import agentUsage as usage


@pytest.mark.parametrize(
    "value,meaning,expected",
    [
        (37, "used", 63),
        (37, "remaining", 37),
        (0, "used", 100),
        (100, "used", 0),
        (0, "remaining", 0),
        (100, "remaining", 100),
        (-5, "used", 100),
        (105, "used", 0),
        (-5, "remaining", 0),
        (105, "remaining", 100),
        (None, "used", None),
        (True, "used", None),
        ("37", "used", None),
        (float("nan"), "used", None),
        (float("inf"), "remaining", None),
    ],
)
def testPercentageSemantics(value, meaning, expected):
    assert usage.percentageAvailable(value, meaning=meaning) == expected


def testPercentageMeaningRequired():
    with pytest.raises(ValueError):
        usage.percentageAvailable(20, meaning="unknown")


def testCodexWindowsAndBuckets():
    result = usage.quotaParse(
        "Codex",
        {
            "rateLimits": {"primary": {"usedPercent": 99}},
            "rateLimitsByLimitId": {
                "codex": {
                    "primary": {
                        "usedPercent": 26,
                        "windowDurationMins": 300,
                        "resetsAt": 1793387100,
                    },
                    "secondary": {"usedPercent": 42, "windowDurationMins": 10080},
                },
                "other": {"primary": {"usedPercent": 100}},
            },
        },
    )
    assert [w.available for w in result.windows] == [74, 58, 0]
    assert [w.name for w in result.windows] == [
        "codex 5h",
        "codex weekly",
        "other primary",
    ]
    assert result.windows[0].reset == datetime.fromtimestamp(1793387100, timezone.utc)
    assert result.windows[1].reset is None


def testMixedProviderWindows():
    copilot = usage.quotaParse(
        "Copilot",
        {
            "quotaSnapshots": {
                "premium_interactions": {
                    "remainingPercentage": 0,
                    "resetDate": "2026-11-01T00:00:00Z",
                },
                "chat": {"remainingPercentage": 100},
                "missing": {"usedRequests": 20, "entitlementRequests": 100},
            }
        },
    )
    assert [w.available for w in copilot.windows] == [0, 100, None]
    grok = usage.quotaParse(
        "Grok",
        {
            "config": {
                "creditUsagePercent": 54,
                "currentPeriod": {"end": "2026-11-02T00:00:00+00:00"},
            }
        },
    )
    assert grok.windows[0].available == 46
    lines = "\n".join(
        usage.allowanceLines([copilot, grok, usage.AgentAllowance("Claude")])
    )
    assert "0%" in lines and "100%" in lines and "46%" in lines
    assert "UNKNOWN" in lines
    assert "premium interactions" in lines and "weekly" in lines
    assert grok.windows[0].reset is not None


@pytest.mark.parametrize("agent", ["Claude", "Codex", "Grok", "Copilot"])
@pytest.mark.parametrize(
    "response", [None, [], "bad", {}, {"tokens": 3, "credits": 10}]
)
def testUnknownNeverManufacturesPercentages(agent, response):
    result = usage.quotaParse(agent, response)
    assert result.status == "UNKNOWN"
    assert "%" not in "\n".join(usage.allowanceLines([result]))


@pytest.mark.parametrize(
    "value", [None, True, "bad", "2026-11-01", "2026-11-01T12:00:00", float("inf")]
)
def testInvalidResetRemainsUnknown(value):
    assert usage._resetParse(value) is None


def testFailureIsolation(monkeypatch):
    monkeypatch.setattr(
        usage.shutil, "which", lambda name: None if name == "claude" else name
    )

    async def query(agent, executable):
        if agent == "Codex":
            raise usage.ProtocolError(unauthenticated=True)
        if agent == "Grok":
            raise ValueError("SECRET must not be printed")
        return usage.quotaParse(
            "Copilot", {"quotaSnapshots": {"weekly": {"remainingPercentage": 0}}}
        )

    monkeypatch.setattr(usage, "_providerQuery", query)
    rows = usage.allowanceCollect()
    assert [r.status for r in rows] == [
        "NOT INSTALLED",
        "NOT AUTHENTICATED",
        "UNKNOWN",
        "OK",
    ]
    assert "SECRET" not in "\n".join(usage.allowanceLines(rows))
    assert "0%" in "\n".join(usage.allowanceLines(rows))


# This fake external executable exercises actual pipes, notifications, framing,
# lifecycle and CLI wiring. Quota truth is specified here, not copied from output.
SERVER = r"""
import json, sys
agent = sys.argv[0].rsplit("/", 1)[-1]
if agent == "claude":
    print(json.dumps({"loggedIn": False}))
    sys.exit(1)
framed = agent == "copilot"
def send(message):
    data = json.dumps(message).encode()
    sys.stdout.buffer.write((f"Content-Length: {len(data)}\r\n\r\n".encode() + data) if framed else data + b"\n")
    sys.stdout.buffer.flush()
while True:
    line = sys.stdin.buffer.readline()
    if not line: break
    if framed:
        size = int(line.split(b":")[1])
        sys.stdin.buffer.readline()
        line = sys.stdin.buffer.read(size)
    request = json.loads(line)
    if "id" not in request: continue
    method = request["method"]
    if method == "account/read": result = {"account": {"type": "chatgpt"}}
    elif method == "auth.getStatus": result = {"isAuthenticated": True}
    elif method == "account/rateLimits/read":
        result = {"rateLimits": {"primary": {"usedPercent": 26, "windowDurationMins": 300}}}
    elif method == "account.getQuota":
        result = {"quotaSnapshots": {"premium_interactions": {"remainingPercentage": 82}}}
    elif method == "_x.ai/billing":
        result = {"config": {"creditUsagePercent": 54}}
    else: result = {}
    send({"jsonrpc": "2.0", "method": "ignored/notification", "params": {}})
    send({"jsonrpc": "2.0", "id": request["id"], "result": result})
"""


def _providersInstall(folder):
    for name in ("claude", "codex", "grok", "copilot"):
        executable = folder / name
        executable.write_text(f"#!{sys.executable}\n" + SERVER)
        executable.chmod(0o755)


def testProtocolComposition(tmp_path, monkeypatch):
    _providersInstall(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path))
    rows = usage.allowanceCollect()
    assert [r.status for r in rows] == ["NOT AUTHENTICATED", "OK", "OK", "OK"]
    assert [r.windows[0].available for r in rows[1:]] == [74, 46, 82]


def testUsageCliProductionPath(tmp_path):
    import subprocess

    _providersInstall(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "organiseMyProjects.agentSessions",
            "--usage",
            "--quiet",
        ],
        env={
            **os.environ,
            "PATH": str(tmp_path),
            "HOME": str(tmp_path),
            "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
        },
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert all(
        text in result.stdout
        for text in (
            "Claude",
            "NOT AUTHENTICATED",
            "Codex",
            "74%",
            "Grok",
            "46%",
            "Copilot",
            "82%",
        )
    )
    assert "session listing" not in result.stdout


@pytest.mark.parametrize(
    "option", ["--all", "--claude", "--resume", "--history", "--full", "--search=work"]
)
def testUsageRejectsSessionOptions(option, monkeypatch):
    from organiseMyProjects import agentSessions

    monkeypatch.setattr(sys, "argv", ["agentSessions", "--usage", option])
    with pytest.raises(SystemExit) as error:
        agentSessions.main()
    assert error.value.code == 2


def testProviderTimeout(monkeypatch):
    monkeypatch.setattr(usage.shutil, "which", lambda name: name)
    monkeypatch.setattr(usage, "TIMEOUT_SECONDS", 0.01)

    async def stalled(agent, executable):
        await asyncio.sleep(10)

    monkeypatch.setattr(usage, "_providerQuery", stalled)
    assert all(row.status == "UNKNOWN" for row in usage.allowanceCollect())


@pytest.mark.parametrize("agent", ["Codex", "Grok", "Copilot"])
@pytest.mark.parametrize("code", [401, -32000, -32601])
def testProtocolErrorsAreSafe(tmp_path, monkeypatch, capsys, caplog, agent, code):
    _providersInstall(tmp_path)
    executable = tmp_path / agent.lower()
    script = executable.read_text().replace(
        '"result": result',
        f'"error": {{"code": {code}, "message": "SECRET_ERROR_DETAIL"}}',
    )
    executable.write_text(script)
    monkeypatch.setenv("PATH", str(tmp_path))
    result = asyncio.run(usage._providerCollect(agent))
    expectedAuth = code == 401 or (code == -32000 and agent == "Grok")
    assert result.status == ("NOT AUTHENTICATED" if expectedAuth else "UNKNOWN")
    assert "SECRET_ERROR_DETAIL" not in capsys.readouterr().out + caplog.text


@pytest.mark.parametrize("agent", ["Codex", "Copilot"])
def testMalformedProtocolIsUnknown(tmp_path, monkeypatch, agent):
    executable = tmp_path / agent.lower()
    executable.write_text(
        f"#!{sys.executable}\nprint('invalid protocol', flush=True)\n"
    )
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    result = asyncio.run(usage._providerCollect(agent))
    assert result.status == "UNKNOWN"


def testMissingGrokPercentagePreservesReset():
    result = usage.quotaParse(
        "Grok",
        {
            "config": {
                "currentPeriod": {"end": "2026-11-04T16:41:00Z"},
                "onDemandUsed": {"val": 10},
                "prepaidBalance": {"val": 100},
            }
        },
    )
    assert result.windows[0].available is None
    assert result.windows[0].reset is not None
    assert "%" not in "\n".join(usage.allowanceLines([result]))


def testTimeoutReapsRealProvider(tmp_path, monkeypatch):
    pidFile = tmp_path / "pid"
    executable = tmp_path / "grok"
    executable.write_text(
        f"#!{sys.executable}\nimport os, time\n"
        f"open({str(pidFile)!r}, 'w').write(str(os.getpid()))\n"
        "time.sleep(30)\n"
    )
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setattr(usage, "TIMEOUT_SECONDS", 0.3)
    assert asyncio.run(usage._providerCollect("Grok")).status == "UNKNOWN"
    with pytest.raises(ProcessLookupError):
        os.kill(int(pidFile.read_text()), 0)


def testReadableQuotaTable():
    rows = [
        usage.AgentAllowance("Claude"),
        usage.AgentAllowance(
            "Codex",
            "OK",
            (
                usage.QuotaWindow("codex 5h", 91),
                usage.QuotaWindow("codex weekly", 96),
            ),
        ),
        usage.AgentAllowance("Grok", "OK", (usage.QuotaWindow("weekly", None),)),
        usage.AgentAllowance(
            "Copilot",
            "OK",
            (
                usage.QuotaWindow("chat", 100),
                usage.QuotaWindow("premium_interactions", 0),
            ),
        ),
    ]
    lines = usage.allowanceLines(rows)
    records = [line for line in lines if line]
    assert len(records) == 7
    assert len(lines) - len(records) == 3
    assert all(len(line) <= 80 for line in lines)
    assert records[0].startswith("AGENT    WINDOW")
    assert "RESET (local time)" in records[0]
    assert records[2].startswith("Codex    5h")
    assert records[3].startswith("         weekly")
    assert "codex 5h" not in "\n".join(lines)
    assert "premium interactions" in records[-1]
    # Right-aligned percentages share a column even for unknown and zero.
    end = records[0].index("AVAILABLE") + len("AVAILABLE")
    for line, expected in zip(
        records[1:], ["UNKNOWN", "91%", "96%", "UNKNOWN", "100%", "0%"]
    ):
        assert line[:end].endswith(expected)
        assert line[end:].strip() == "—"


def testEmptyQuotaTableAndStatusLabels():
    assert len(usage.allowanceLines([])) == 1
    lines = usage.allowanceLines(
        [
            usage.AgentAllowance("Claude", "NOT AUTHENTICATED"),
            usage.AgentAllowance("Grok", "NOT INSTALLED"),
        ]
    )
    assert "NOT AUTHENTICATED" in lines[1]
    assert "NOT INSTALLED" in lines[3]
