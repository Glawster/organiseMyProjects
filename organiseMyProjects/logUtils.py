import os
import datetime
import logging
from pathlib import Path

# logging guidelines:
# Logging format guide:
# all messages in lowercase
# "...message" - general update, doing this
# "message..." - done something
# "...message: value" - display some information
# ERROR messages should be in Sentence Case.

# Usage:
# from organiseMyUtils.logUtils import getLogger
# 
# logger = getLogger("program name")
# logger.info("...message")

def setupLogging(title: str) -> logging.Logger:
    title = title.replace(" ", "")
    logger = logging.getLogger(title)
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
def getLogger(name: str = "OrganiseMyProject") -> logging.Logger:
    """Returns the global logger, using setupLogging if not already initialized."""
    return setupLogging(name)
