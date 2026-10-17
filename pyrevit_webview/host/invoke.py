# -*- coding: utf-8 -*-
"""UI-thread invoke helpers for WinForms and WPF."""

from __future__ import print_function, division

from pyrevit_webview.compat import Any, Callable, Optional
from pyrevit_webview.types import InvokeOnUi
from pyrevit_webview.log import debug_trace


def winforms_invoke(form):
    # type: (Any) -> InvokeOnUi
    """Return invoke suitable for ``Form.BeginInvoke(MethodInvoker(...))``."""
    from System.Windows.Forms import MethodInvoker

    def invoke(action):
        # type: (Callable[[], None]) -> None
        debug_trace("winforms_invoke.BeginInvoke", "post")
        form.BeginInvoke(MethodInvoker(action))

    return invoke


def wpf_invoke(control):
    # type: (Any) -> InvokeOnUi
    """Return invoke suitable for ``Dispatcher.BeginInvoke(Action(...))``."""
    from System import Action
    from System.Windows.Threading import DispatcherPriority

    dispatcher = control.Dispatcher

    def invoke(action):
        # type: (Callable[[], None]) -> None
        debug_trace("wpf_invoke.BeginInvoke", "post")
        dispatcher.BeginInvoke(DispatcherPriority.Normal, Action(action))

    return invoke


def invoke_on_ui_sync(invoke_on_ui, action, dispatcher=None):
    # type: (InvokeOnUi, Callable[[], Any], Optional[Any]) -> Any
    """Run *action* on the UI thread and block until it completes.

    If already on the target Dispatcher (``CheckAccess``), runs inline — avoids
    deadlock when a sync host callback is already on the UI thread.
    """
    import threading

    if dispatcher is not None:
        try:
            if dispatcher.CheckAccess():
                debug_trace("invoke_on_ui_sync", "inline (CheckAccess)")
                return action()
        except Exception:
            pass

    gate = threading.Event()
    box = {"result": None, "error": None}  # type: dict

    def work():
        # type: () -> None
        debug_trace("invoke_on_ui_sync.work", "running on UI")
        try:
            box["result"] = action()
        except Exception as exc:
            debug_trace("invoke_on_ui_sync.work", "error: {0!r}".format(exc))
            box["error"] = exc
        finally:
            gate.set()

    debug_trace("invoke_on_ui_sync", "post + wait")
    invoke_on_ui(work)
    gate.wait()
    debug_trace(
        "invoke_on_ui_sync",
        "released error={0}".format(box["error"] is not None),
    )
    if box["error"] is not None:
        raise box["error"]
    return box["result"]
