# app/logging_config.py

import logging
import os
import sys
from contextvars import ContextVar, Token
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


# ============================================================
# REQUEST CONTEXT
# ============================================================

_request_id_context: ContextVar[str] = ContextVar(
    "request_id",
    default="-",
)


class RequestContextFilter(logging.Filter):
    """
    Add the current request ID to every ACT Rave log record.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id_context.get()
        return True


def set_request_id(request_id: str) -> Token:
    """
    Store the request ID for the current request context.
    """

    return _request_id_context.set(request_id)


def reset_request_id(token: Token) -> None:
    """
    Restore the previous request context.
    """

    _request_id_context.reset(token)


# ============================================================
# LOGGING SETTINGS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

LOG_DIR = Path(
    os.getenv(
        "RAVE_LOG_DIR",
        str(PROJECT_ROOT / "logs"),
    )
)

LOG_FILE = LOG_DIR / "rave_api.log"

LOG_LEVEL = os.getenv(
    "RAVE_LOG_LEVEL",
    "INFO",
).upper()

# Number of rotated daily log files to retain.
# Default = 30 days.
LOG_BACKUP_COUNT = int(
    os.getenv(
        "RAVE_LOG_BACKUP_COUNT",
        "30",
    )
)

LOGGER_NAME = "act_rave"

LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | "
    "request_id=%(request_id)s | %(message)s"
)

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


# ============================================================
# CONFIGURATION
# ============================================================

def configure_logging() -> None:
    """
    Configure ACT Rave application logging.

    Logs are written to:
    - stdout for Codespaces / container visibility
    - logs/rave_api.log for local persistence

    File rotation policy:
    - active file: rave_api.log
    - rotate once per day at 00:00 UTC
    - archived files: rave_api.log.YYYY-MM-DD
    - retain the configured number of daily backups
      (default: 30 days)
    """

    logger = logging.getLogger(LOGGER_NAME)

    # Avoid duplicate handlers when FastAPI reloads in development.
    if getattr(logger, "_act_rave_configured", False):
        return

    numeric_level = getattr(
        logging,
        LOG_LEVEL,
        logging.INFO,
    )

    logger.setLevel(numeric_level)
    logger.propagate = False

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    formatter = logging.Formatter(
        fmt=LOG_FORMAT,
        datefmt=DATE_FORMAT,
    )

    context_filter = RequestContextFilter()

    # --------------------------------------------------------
    # Console logging
    # --------------------------------------------------------

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(context_filter)

    # --------------------------------------------------------
    # Daily file logging
    # --------------------------------------------------------

    file_handler = TimedRotatingFileHandler(
        filename=LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
        utc=True,
        delay=False,
    )

    # Produces archived names such as:
    # rave_api.log.2026-08-16
    file_handler.suffix = "%Y-%m-%d"

    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(context_filter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger._act_rave_configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Return an ACT Rave child logger.
    """

    configure_logging()

    return logging.getLogger(
        f"{LOGGER_NAME}.{name}"
    )
