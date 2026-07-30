"""Regression tests for the Bash logging helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

LOG_UTILS = Path(__file__).parents[1] / "organiseMyProjects" / "logUtils.sh"


def _runShell(logDir: Path, dryRun: bool, calls: str) -> list[str]:
    """Source logUtils.sh, execute calls, and return messages without timestamps."""
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
    return [line.split("] ", 1)[1] for line in result.stdout.splitlines()[1:]]


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
