"""Regression tests for the Bash logging helpers."""

from __future__ import annotations

import subprocess
import re
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
        r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] " r"\[    INFO\] testLogUtils (.*)$"
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
