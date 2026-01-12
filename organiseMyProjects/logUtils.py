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
) -> logging.Logger:
    """
    Convenience wrapper used by other scripts.
    """
    return setupLogging(name, logDir=logDir, level=level, includeConsole=includeConsole)


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
