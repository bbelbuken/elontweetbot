"""
Logging configuration and utilities.

This module sets up structured logging using structlog with JSON formatting
for better observability and log aggregation.
"""

import structlog
import logging
import sys
import os

LOG_DIR = os.path.join(os.path.dirname(__file__), "..",
                       "logs")  # relative to app directory
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")


def configure_logging():
    # Root logger stdout'a yönlendir
    logging.basicConfig(
        format="%(message)s",
        filename=LOG_FILE,
        level=logging.DEBUG,
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),

            # Grafana / Loki için JSON renderer
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None):
    """Get a configured structlog logger instance."""
    return structlog.get_logger(name)
