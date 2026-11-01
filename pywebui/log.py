# -*- coding: utf-8 -*-
"""One logger for the library.

The line format is ``[pywebui] message``. ``PYWEBUI_LOG``
selects the level and defaults to INFO. ``debug_trace`` writes DEBUG, so
those lines stay quiet until the level is lowered.
"""

from __future__ import print_function, division

import logging
import os
import sys

LOGGER_NAME = "pywebui"


class _FlushStreamHandler(logging.StreamHandler):
    """Stream handler that flushes so a host journal sees the line."""

    def emit(self, record):
        # type: (logging.LogRecord) -> None
        logging.StreamHandler.emit(self, record)
        self.flush()


def _level_from_env():
    # type: () -> int
    name = os.environ.get("PYWEBUI_LOG", "INFO").upper()
    level = getattr(logging, name, None)
    if isinstance(level, int):
        return level
    return logging.INFO


def _configure(logger):
    # type: (logging.Logger) -> logging.Logger
    if logger.handlers:
        return logger
    handler = _FlushStreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[pywebui] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(_level_from_env())
    logger.propagate = False
    return logger


def get_logger(name=LOGGER_NAME):
    # type: (str) -> logging.Logger
    logger = logging.getLogger(name)
    if name == LOGGER_NAME:
        _configure(logger)
    return logger


def _thread_tag():
    # type: () -> str
    """ManagedThreadId and Python thread name."""
    managed_id = "?"
    try:
        from System.Threading import Thread

        managed_id = str(Thread.CurrentThread.ManagedThreadId)
    except Exception:
        pass

    py_name = "?"
    try:
        import threading

        py_name = threading.current_thread().name
    except Exception:
        pass

    return "clr={0} py={1}".format(managed_id, py_name)


def debug_trace(where, detail=""):
    # type: (str, str) -> None
    """Record a diagnostic on the library logger at DEBUG."""
    extra = ""
    if detail not in (None, ""):
        extra = " | {0}".format(detail)
    get_logger().debug("{0} {1}{2}".format(_thread_tag(), where, extra))
