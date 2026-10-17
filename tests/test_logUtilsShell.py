"""Regression tests for the Bash logging helpers."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

LOG_UTILS = Path(__file__).parents[1] / "organiseMyProjects" / "logUtils.sh"


def _runShell(logDir: Path, dryRun: bool, calls: str) -> list[str]:
    """Source logUtils.sh, execute calls, and return semantic messages."""
    dryRunValue = "1" if dryRun else ""
    script = f"""
source "{LOG_UTILS}"
setApplication testLogUtils "{logDir}"
dryRun="{dryRunValue}"
{calls}
"""
    result = subprocess.run(
        ["bash", "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )
    outputLines = result.stdout.splitlines()[1:]
    pattern = re.compile(
        r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] " r"\[INFO\] testLogUtils (.*)$"
    )
    matches = [pattern.fullmatch(line) for line in outputLines]
    assert all(matches), outputLines
    return [match.group(1) for match in matches if match is not None]


def testLogLineUsesAlignedLevelAndExtensionlessSource(tmp_path):
    """Emit the common timestamp, aligned level, source and message shape."""
    messages = _runShell(tmp_path, False, 'log_info "message"')
    assert messages == ["...message"]


def testProgressMethodsMarkDryRunAndUseAlternateMessages(tmp_path):
    messages = _runShell(
        tmp_path,
        True,
        """
log_doing "processing" "would process"
log_action "copy file" "would copy file"
log_done "processed" "processing simulated"
""",
    )

    assert messages == [
        "[] would process...",
        "...[] would copy file",
        "...[] processing simulated",
    ]


def testProgressMethodsRemainBackwardCompatible(tmp_path):
    messages = _runShell(
        tmp_path,
        False,
        """
log_doing "processing"
log_action "copy file"
log_done "processed"
""",
    )

    assert messages == ["processing...", "...copy file", "...processed"]


def testRunStartWritesPlainMarkerWithoutLogging(tmp_path):
    """The Bash run marker matches Python, preserves history and bypasses _log."""
    result = subprocess.run(
        [
            "bash",
            "-c",
            "\n".join(
                [
                    "set -euo pipefail",
                    'source "$1"',
                    'setApplication runTest "$2" > /dev/null',
                    'printf "previous run\\n" > "$logFile"',
                    "_log() { return 97; }",
                    "_log_to_file() { return 98; }",
                    "runStart",
                    "runStart",
                ]
            ),
            "bash",
            str(LOG_UTILS),
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    expected = ("\n>" + "-" * 80 + "<\n\n") * 2
    assert result.stdout == expected
    assert result.stderr == ""
    assert next(tmp_path.glob("*.log")).read_text() == "previous run\n" + expected


def testRunStartRequiresApplicationContext():
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; thisApplication=""; runStart',
            "bash",
            str(LOG_UTILS),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert result.stdout == ""
    assert "Call setApplication first" in result.stderr


def testLineWritesPlainSeparatorWithoutLogging(tmp_path):
    result = subprocess.run(
        [
            "bash",
            "-c",
            "\n".join(
                [
                    "set -euo pipefail",
                    'source "$1"',
                    'setApplication lineTest "$2" > /dev/null',
                    'printf "previous entry\\n" > "$logFile"',
                    "_log() { return 97; }",
                    "_log_to_file() { return 98; }",
                    "line",
                    "line",
                ]
            ),
            "bash",
            str(LOG_UTILS),
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    expected = ("-" * 80 + "\n") * 2
    assert result.stdout == expected
    assert result.stderr == ""
    assert next(tmp_path.glob("*.log")).read_text() == "previous entry\n" + expected
