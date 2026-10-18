# -*- coding: utf-8 -*-
"""Standard logging helpers (stdlib logging - IronPython 2.7 / CPython 3)."""

from __future__ import print_function, division

import logging
import sys

from pyrevit_webview.compat import Any

LOGGER_NAME = "pyrevit_webview"  # type: str

# Set True (or env PYREVIT_WEBVIEW_TRACE=1) to print thread-tagged diagnostics to stdout.
TRACE_ENABLED = True  # type: bool


def get_logger(name=LOGGER_NAME):
    # type: (str) -> logging.Logger
    return logging.getLogger(name)


def _trace_enabled():
    # type: () -> bool
    if TRACE_ENABLED:
        return True
    try:
        import os

        return os.environ.get("PYREVIT_WEBVIEW_TRACE", "").strip() in ("1", "true", "True")
    except Exception:
        return False


def _thread_tag():
    # type: () -> str
    """ManagedThreadId + Python thread name (best-effort under IronPython/pythonnet)."""
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
    """Print a one-line diagnostic; always flush so pyRevit journal/output sees it."""
    if not _trace_enabled():
        return
    extra = ""
    if detail not in (None, ""):
        extra = " | {0}".format(detail)
    line = "[pyWebview] [{0}] {1}{2}".format(_thread_tag(), where, extra)
    try:
        print(line)
        sys.stdout.flush()
    except Exception:
        pass
