import os
import datetime
import logging

from logging import getLogger
from pathlib import Path

# logging guidelines:
# all messages in lowercase
# "doing something..." - major action being taken
# "...something done" - above action completed
# "...message" - general update, doing this, transitory information
# "...message: value" - display some information
# ERROR messages should be in Sentence Case.

# Usage:
# from src.logUtils import logger
# logger.info("...message")


def setupLogging(title: str) -> logging.Logger:
    
    title = title.replace(" ", "")
    logger = getLogger(title)
    if not logger.handlers:
        logDir = Path(__file__).resolve().parent.parent / "logs"
        logDir.mkdir(parents=True, exist_ok=True)
        logDate = datetime.datetime.now().strftime("%Y%m%d")
        logFilePath = logDir / f"{title}.{logDate}.log"

        handler = logging.FileHandler(logFilePath)
        formatter = logging.Formatter('%(asctime)s [%(module)s] %(levelname)s %(message)s')
        handler.setFormatter(formatter)

        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

    return logger

# Global logger instance initialized at import time
logger = setupLogging("title")