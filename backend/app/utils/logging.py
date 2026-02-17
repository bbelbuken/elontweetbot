"""
Logging configuration and utilities.

This module sets up structured logging using structlog with JSON formatting
for better observability and log aggregation.
"""

import structlog
import logging
import sys
import os
from contextvars import ContextVar
from typing import Dict, Any

LOG_DIR = os.path.join(os.path.dirname(__file__), "..",
                       "logs")  # relative to app directory
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Context storage for request-scoped logging
_log_context: ContextVar[Dict[str, Any]] = ContextVar('log_context', default={})


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
            add_context_processor,  # Add context before rendering
            # Grafana / Loki için JSON renderer
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def add_context_processor(logger, method_name, event_dict):
    """
    Processor to add context variables to all log messages.
    This allows adding request_id, user_id, etc. to all logs within a context.
    """
    context = _log_context.get()
    if context:
        event_dict.update(context)
    return event_dict


def set_log_context(**kwargs):
    """
    Set context variables that will be added to all subsequent log messages.
    
    Example:
        set_log_context(request_id="abc123", user_id="user456")
        logger.info("Processing request")  # Will include request_id and user_id
    """
    current = _log_context.get()
    current.update(kwargs)
    _log_context.set(current)


def clear_log_context():
    """Clear all context variables."""
    _log_context.set({})


def get_logger(name: str = None):
    """Get a configured structlog logger instance."""
    return structlog.get_logger(name)

