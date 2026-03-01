from __future__ import annotations

import datetime
import logging
from logging import getLogger as _getLogger
from pathlib import Path
from typing import Any, MutableMapping, Optional

# logging guidelines:
# all messages in lowercase
# "doing something..." - major action being taken
# "...something done" - above action completed
# "...message" - general update, doing this, transitory information
# "...message: value" - display some information
# ERROR messages should be in Sentence Case.

_initialized_log_files: set[str] = set()

_DRY_RUN_PREFIX = "[] "


class _OrganiseLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter providing semantic log methods with optional dry-run prefixing."""

    def __init__(self, logger: logging.Logger, dryRun: bool = False):
        super().__init__(logger, {})
        self._dryRun = dryRun
        self._prefix = _DRY_RUN_PREFIX if dryRun else ""

    def process(self, msg: str, kwargs: MutableMapping[str, Any]) -> tuple[str, MutableMapping[str, Any]]:
        """For non-semantic calls (warning, error, debug), add dryRun prefix."""
        if self._dryRun:
            return f"{_DRY_RUN_PREFIX}{msg}", kwargs
        return msg, kwargs

    def info(self, message: str, *args, **kwargs) -> None:
        """Log general information: '...{prefix}message'"""
        self.logger.info(f"...{self._prefix}{message}", *args, **kwargs)

    def doing(self, message: str) -> None:
        """Log a major action being taken: '{prefix}message...'"""
        self.logger.info(f"{self._prefix}{message}...")

    def done(self, message: str) -> None:
        """Log a completed action: '...{prefix}message'"""
        self.logger.info(f"...{self._prefix}{message}")

    def value(self, message: str, variable) -> None:
        """Log a name-value pair: '...{prefix}message: variable'"""
        self.logger.info(f"...{self._prefix}{message}: {variable}")


def _defaultLogDir() -> Path:
    """
    Default log directory for shared tools.

    Prefer a stable per-user location:
      ~/.local/state/organiseMy/logs

    (This keeps logs out of repos and out of ~/.config)
    """
    return Path.home() / ".local" / "state" / "organiseMy" / "logs"

def _setupLogging(
    name: str,
    logDir: Optional[Path] = None,
    level: int = logging.INFO,
    includeConsole: bool = False
) -> logging.Logger:
    """
    Internal helper to set up logging with file and optional console handlers.
    """
    logger = _getLogger(name)
    logger.setLevel(level)

    if logDir is None:
        logDir = _defaultLogDir()

    logDir.mkdir(parents=True, exist_ok=True)
    logFile = logDir / f"{name}.log"

    if str(logFile) not in _initialized_log_files:
        fileHandler = logging.FileHandler(logFile, encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fileHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)
        _initialized_log_files.add(str(logFile))

    if includeConsole and not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        consoleHandler = logging.StreamHandler()
        consoleFormatter = logging.Formatter("%(levelname)s - %(message)s")
        consoleHandler.setFormatter(consoleFormatter)
        logger.addHandler(consoleHandler)

    return logger

def getLogger(
    name: str = "OrganiseMyTool",
    logDir: Optional[Path] = None,
    level: int = logging.INFO,
    includeConsole: bool = False,
    dryRun: bool = False,
) -> _OrganiseLoggerAdapter:
    """
    Convenience wrapper used by other scripts.

    Returns an _OrganiseLoggerAdapter with semantic log methods:
      doing(message)           – logs '{prefix}message...'
      done(message)            – logs '...{prefix}message'
      info(message)            – logs '...{prefix}message'
      value(message, variable) – logs '...{prefix}message: variable'

    Pass dryRun=True to insert '[] ' into every formatted message.
    """
    logger = _setupLogging(name, logDir=logDir, level=level, includeConsole=includeConsole)
    return _OrganiseLoggerAdapter(logger, dryRun=dryRun)


def setLogLevel(level: int, targetLogger: Optional[logging.Logger] = None) -> None:
    """
    Set logging level for the specified logger.
    """
    if targetLogger is None:
        targetLogger = _getLogger()

    targetLogger.setLevel(level)
    levelName = logging.getLevelName(level)
    if isinstance(targetLogger, _OrganiseLoggerAdapter):
        targetLogger.done(f"logging level changed to: {levelName}")
    else:
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
        rawLogger = logger.logger if isinstance(logger, logging.LoggerAdapter) else logger
        for outLine in output_lines:
            rawLogger.info(outLine)
    else:
        for outLine in output_lines:
            print(outLine)
