# -*- coding: utf-8 -*-
"""Revit adapter — Revit.Async helpers for API calls from bridge handlers."""

from __future__ import print_function, division

from pyrevit_webview.compat import Any, Callable, Optional
from pyrevit_webview.dotnet import load_bin
from pyrevit_webview.log import debug_trace

_main_thread_id = None  # type: Optional[int]


def ensure_revit_adapter():
    # type: () -> None
    """Load extension ``bin/`` (includes ``Revit.Async`` fallback)."""
    load_bin()


def initialize_revit_task(application):
    # type: (Any) -> None
    """Initialize Revit.Async once (Revit main thread).

    Pass ``UIControlledApplication`` or ``UIApplication`` (pyRevit: ``__revit__``).
    """
    global _main_thread_id

    ensure_revit_adapter()
    from System.Threading import Thread
    from Revit.Async import RevitTask

    _main_thread_id = Thread.CurrentThread.ManagedThreadId
    RevitTask.Initialize(application)
    debug_trace(
        "initialize_revit_task",
        "main_thread_id={0}".format(_main_thread_id),
    )


def _on_revit_main_thread():
    # type: () -> bool
    from System.Threading import Thread

    return (
        _main_thread_id is not None
        and Thread.CurrentThread.ManagedThreadId == _main_thread_id
    )


def revit_invoke_sync(action):
    # type: (Callable[[], Any]) -> Any
    """Run *action* on Revit's main thread and block until it completes.

    Use inside ``@bridge_callable`` handlers that touch the Revit API from a
    ``WebMessageReceived`` callback thread. Requires :func:`initialize_revit_task`.

    If already on the Revit main thread, runs inline (avoids deadlock).
    """
    ensure_revit_adapter()

    if _on_revit_main_thread():
        debug_trace("revit_invoke_sync", "inline (already main)")
        return action()

    from System import Func
    from Revit.Async import RevitTask

    debug_trace("revit_invoke_sync", "marshal via RevitTask")
    box = {"result": None, "error": None}  # type: dict

    def run():
        # type: () -> Any
        debug_trace("revit_invoke_sync.run", "on main")
        try:
            box["result"] = action()
        except Exception as exc:
            box["error"] = exc
        return None

    # RunAsync(Action) is a method group on the stub and is not callable there.
    # The generic Func overload is the one the stub types, and its Task completes
    # only after the delegate returns. The Python result stays in box so it does
    # not have to cross the CLR boundary.
    RevitTask.RunAsync[object](Func[object](run)).GetAwaiter().GetResult()
    if box["error"] is not None:
        raise box["error"]
    return box["result"]
