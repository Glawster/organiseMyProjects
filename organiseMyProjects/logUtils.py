from __future__ import annotations

import datetime
import logging
from logging import getLogger as _getLogger
from pathlib import Path
from typing import Optional

# logging guidelines:
# all messages in lowercase
# "doing something..." - major action being taken
# "...something done" - above action completed
# "...message" - general update, doing this, transitory information
# "...message: value" - display some information
# ERROR messages should be in Sentence Case.

_initialized_log_files: set[str] = set()

DRY_RUN_PREFIX = "[DRY RUN] "


def dryRunLog(logger: logging.Logger, message: str, dryRun: bool = False) -> None:
    """
    Log a message with an optional dry-run prefix.

    Args:
        logger: The logger instance to use.
        message: The message to log.
        dryRun: If True, prepends the DRY_RUN_PREFIX to the message.
    """
    prefix = DRY_RUN_PREFIX if dryRun else ""
    logger.info(f"{prefix}{message}")


class DryRunLogger:
    """
    Wraps a logging.Logger and automatically prefixes messages when in dry-run mode.

    Set dryRun once at construction to avoid repeating it on every call.
    """

    DRY_RUN_PREFIX = DRY_RUN_PREFIX  # module-level constant
    LIVE_PREFIX = ""

    def __init__(self, logger: logging.Logger, dryRun: bool = False) -> None:
        self._logger = logger
        self._dryRun = dryRun

    @property
    def prefix(self) -> str:
        """Return the appropriate prefix based on the dry-run state."""
        return self.DRY_RUN_PREFIX if self._dryRun else self.LIVE_PREFIX

    def info(self, message: str) -> None:
        """Log an info message with the dry-run prefix if applicable."""
        self._logger.info(f"{self.prefix}{message}")

    def warning(self, message: str) -> None:
        """Log a warning message with the dry-run prefix if applicable."""
        self._logger.warning(f"{self.prefix}{message}")

    def error(self, message: str) -> None:
        """Log an error message with the dry-run prefix if applicable."""
        self._logger.error(f"{self.prefix}{message}")


def _defaultLogDir() -> Path:
    """
    Default log directory for shared tools.

    Prefer a stable per-user location:
      ~/.local/state/organiseMy/logs

    (This keeps logs out of repos and out of ~/.config)
    """
    return Path.home() / ".local" / "state" / "organiseMy" / "logs"


def setupLogging(
    title: str,
    logDir: Optional[Path] = None,
    level: int = logging.INFO,
    includeConsole: bool = False,
) -> logging.Logger:
    """
    Create/retrieve a logger with a FileHandler.

    - Title spaces are removed (consistent with your existing usage).
    - Log file name: <title>.<YYYYMMDD_HHMM>.log
    - If includeConsole is True, also add a StreamHandler.
    """
    safeTitle = (title or "root").replace(" ", "")
    logger = _getLogger(safeTitle)

    if logger.handlers:
        return logger

    targetDir = (logDir or _defaultLogDir()).expanduser().resolve()
    targetDir.mkdir(parents=True, exist_ok=True)

    logDateTime = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    logFilePath = targetDir / f"{safeTitle}.{logDateTime}.log"

    fileHandler = logging.FileHandler(logFilePath, encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s [%(module)-20s] %(levelname)s %(message)s",
        datefmt="%Y%m%d %H:%M:%S",
    )
    fileHandler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(fileHandler)

    if includeConsole:
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)

    # Separator line once per log file (not per logger call)
    key = str(logFilePath)
    if key not in _initialized_log_files:
        logger.info("\n" + "=" * 80)
        _initialized_log_files.add(key)

    logger.info(f"... logging to file: {logFilePath}")
    return logger


def getLogger(
    name: str = "OrganiseMyTool",
    logDir: Optional[Path] = None,
    level: int = logging.INFO,
    includeConsole: bool = False,
    dryRun: bool = False,
) -> logging.Logger | DryRunLogger:
    """
    Convenience wrapper used by other scripts.

    Pass dryRun=True to receive a DryRunLogger that automatically prefixes
    every info/warning/error call with '[DRY RUN] '.
    """
    logger = setupLogging(name, logDir=logDir, level=level, includeConsole=includeConsole)
    if dryRun:
        return DryRunLogger(logger, dryRun=True)
    return logger


def setLogLevel(level: int, targetLogger: Optional[logging.Logger] = None) -> None:
    """
    Set logging level for the specified logger.
    """
    if targetLogger is None:
        targetLogger = _getLogger()

    targetLogger.setLevel(level)
    levelName = logging.getLevelName(level)
    targetLogger.info(f"...logging level changed to: {levelName}")


def cleanOldLogFiles(logDir: Path, daysToKeep: int) -> tuple[int, list[str]]:
    """
    Remove log files older than specified days.
    Returns (count_removed, list_of_removed_files)
    """
    targetDir = logDir.expanduser().resolve()
    if not targetDir.exists():
        return 0, []

    cutoffDate = datetime.datetime.now() - datetime.timedelta(days=daysToKeep)
    removedCount = 0
    removedFiles: list[str] = []

    for logFile in targetDir.glob("*.log"):
        try:
            fileTime = datetime.datetime.fromtimestamp(logFile.stat().st_mtime)
            if fileTime < cutoffDate:
                logFile.unlink()
                removedCount += 1
                removedFiles.append(logFile.name)
        except (OSError, ValueError):
            # keep going; callers can log if they care
            continue

    return removedCount, removedFiles

# logUtils.py

def drawBox(
    message: str,
    border_char: str = "─",
    corner_char: str = "+",
    side_char: str = "│",
    padding: int = 2,
    logger=None
) -> None:
    """
    Print a nicely formatted ASCII box around a log message.
    
    Useful for making important log entries stand out:
    
    +──────────────────────────────────────────────────────────┐
    │  [ERROR] Database connection failed                      │
    │  Attempted 3 retries. Check credentials and network.     │
    └──────────────────────────────────────────────────────────┘

    Args:
        message: The text to display inside the box (can be multi-line)
        border_char: Character for horizontal lines
        corner_char: Corner characters
        side_char: Vertical bar character
        padding: Spaces between text and sides
        logger: Optional logger instance (e.g. logging.getLogger())
                If provided, uses logger instead of print()
    """

    # Split into lines and calculate content width
    lines = message.splitlines()
    if not lines:
        lines = ["(empty message)"]

    contentWidth = max(len(line) for line in lines)
    innerWidth = contentWidth + padding * 2

    # Build border
    top_bottom = corner_char + border_char * innerWidth + corner_char

    # Header line with level
    header = f"{lines[0]}"
    headerPadding = innerWidth - len(header) - padding
    headerLine = f"{side_char}{' ' * padding}{header}{' ' * headerPadding}{side_char}"

    # Prepare body lines
    bodyLines = []
    for line in lines[1:]:
        padRight = innerWidth - len(line) - padding
        bodyLines.append(f"{side_char}{' ' * padding}{line}{' ' * padRight}{side_char}")

    # Output
    output_lines = [
        top_bottom,
        headerLine,
        *(bodyLines if len(lines) > 1 else []),
        top_bottom
    ]

    if logger is not None:
        for outLine in output_lines:
            logger.info(outLine)
    else:
        for outLine in output_lines:
            print(outLine)
