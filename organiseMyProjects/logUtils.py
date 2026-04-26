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

thisApplication: str | None = None
_applicationLogDir: Path | None = None

class _OrganiseLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter providing semantic log methods with optional dry-run prefixing."""

    def __init__(self, logger: logging.Logger, dryRun: bool = False):
        super().__init__(logger, {})
        self._dryRun = dryRun
        self._prefix = _DRY_RUN_PREFIX if dryRun else ""

    def process(
        self, msg: str, kwargs: MutableMapping[str, Any]
    ) -> tuple[str, MutableMapping[str, Any]]:
        """Pass through non-semantic calls (warning, error, debug) unchanged."""
        return msg, kwargs

    def info(self, message: str, *args, **kwargs) -> None:
        """Log general information: '...message'."""
        self.logger.info(f"...{message}", *args, **kwargs)

    def doing(self, message: str) -> None:
        """Log a major action being taken: 'message...'."""
        self.logger.info(f"{message}...")

    def done(self, message: str) -> None:
        """Log a completed action: '...message'."""
        self.logger.info(f"...{message}")

    def value(self, message: str, variable) -> None:
        """Log a name-value pair: '...message: variable'."""
        self.logger.info(f"...{message}: {variable}")

    def action(self, message: str, *args, **kwargs) -> None:
        """Log a dry-run-aware action: '...{prefix}message'."""
        self.logger.info(f"...{self._prefix}{message}", *args, **kwargs)


def setApplication(name: str, logDir: Optional[Path] = None) -> None:
    """Set the active application context for subsequent getLogger() calls."""
    global thisApplication, _applicationLogDir

    cleanedName = name.strip()
    if not cleanedName:
        raise ValueError("Application name must not be empty.")

    thisApplication = cleanedName
    _applicationLogDir = logDir or (Path.home() / ".local" / "state" / cleanedName)
    _applicationLogDir.mkdir(parents=True, exist_ok=True)


def getApplication() -> str:
    """Return the active application context or fail fast if it was not set."""
    if not thisApplication:
        raise RuntimeError(
            "Application logging context has not been set. "
            "Call setApplication(name) in the entry point before importing modules "
            "that call getLogger()."
        )
    return thisApplication


def getApplicationLogDir() -> Path:
    """Return the active application log directory or fail fast if unset."""
    if _applicationLogDir is None:
        raise RuntimeError("Application log directory has not been initialised.")
    return _applicationLogDir

def _resolveLoggerName(name: Optional[str]) -> str:
    """Resolve an explicit logger name or the active application context."""
    if name:
        return name
    return getApplication()


def _defaultLogDir() -> Path:
    """
    Default base log directory for shared tools.

    Prefer a stable per-user location:
      ~/.local/state

    Log files are stored under ~/.local/state/{name}/{name}-{date}.log.
    """
    return Path.home() / ".local" / "state"


def _setupLogging(
    name: str,
    logDir: Optional[Path] = None,
    level: int = logging.INFO,
    includeConsole: bool = False,
) -> logging.Logger:
    """Set up logging with file and optional console handlers."""
    logger = _getLogger(name)
    logger.setLevel(level)

    if logDir is None:
        if name == getApplication():
            logDir = getApplicationLogDir()
        else:
            logDir = _defaultLogDir() / name

    logDir.mkdir(parents=True, exist_ok=True)
    date = datetime.date.today().isoformat()
    logFile = logDir / f"{name}-{date}.log"

    if str(logFile) not in _initialized_log_files:
        fileHandler = logging.FileHandler(logFile, encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fileHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)
        _initialized_log_files.add(str(logFile))

    if includeConsole and not any(type(h) is logging.StreamHandler for h in logger.handlers):
        consoleHandler = logging.StreamHandler()
        consoleFormatter = logging.Formatter("%(levelname)s - %(message)s")
        consoleHandler.setFormatter(consoleFormatter)
        logger.addHandler(consoleHandler)

    return logger


def getLogger(
    name: Optional[str] = None,
    logDir: Optional[Path] = None,
    level: int = logging.INFO,
    includeConsole: bool = False,
    dryRun: bool = False,
) -> _OrganiseLoggerAdapter:
    """
    Convenience wrapper used by other scripts.

    If name is omitted, the active application context set by setApplication()
    is used. Passing name explicitly remains supported for specialised tools.

    Returns an _OrganiseLoggerAdapter with semantic log methods:
      doing(message)           – logs 'message...'
      done(message)            – logs '...message'
      info(message)            – logs '...message'
      value(message, variable) – logs '...message: variable'
      action(message)          – logs '...{prefix}message'
    Pass dryRun=True to insert '[] ' only for action.
    """
    loggerName = _resolveLoggerName(name)
    logger = _setupLogging(
        loggerName,
        logDir=logDir,
        level=level,
        includeConsole=includeConsole,
    )
    return _OrganiseLoggerAdapter(logger, dryRun=dryRun)


def setLogLevel(level: int, targetLogger: Optional[logging.Logger] = None) -> None:
    """Set logging level for the specified logger."""
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

    Returns (count_removed, list_of_removed_files).
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
            continue

    return removedCount, removedFiles


def drawBox(
    message: str,
    border_char: str = "─",
    corner_char: str = "+",
    side_char: str = "│",
    padding: int = 2,
    logger=None,
) -> None:
    """Print or log a formatted ASCII box around a message."""
    lines = message.splitlines()
    if not lines:
        lines = ["(empty message)"]

    contentWidth = max(len(line) for line in lines)
    innerWidth = contentWidth + padding * 2
    topBottom = corner_char + border_char * innerWidth + corner_char

    header = f"{lines[0]}"
    headerPadding = innerWidth - len(header) - padding
    headerLine = f"{side_char}{' ' * padding}{header}{' ' * headerPadding}{side_char}"

    bodyLines = []
    for line in lines[1:]:
        padRight = innerWidth - len(line) - padding
        bodyLines.append(f"{side_char}{' ' * padding}{line}{' ' * padRight}{side_char}")

    outputLines = [
        topBottom,
        headerLine,
        *(bodyLines if len(lines) > 1 else []),
        topBottom,
    ]

    if logger is not None:
        rawLogger = logger.logger if isinstance(logger, logging.LoggerAdapter) else logger
        for outLine in outputLines:
            rawLogger.info(outLine)
    else:
        for outLine in outputLines:
            print(outLine)
