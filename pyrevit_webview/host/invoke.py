# -*- coding: utf-8 -*-
"""Wait for a caller-supplied UI invoke. Framework dispatch lives elsewhere.

WPF: ``pyrevit_webview.host.wpf``. WinForms: ``pyrevit_webview.host.winforms``.
"""

from __future__ import print_function, division

from pyrevit_webview.compat import Any, Callable
from pyrevit_webview.types import InvokeOnUi
from pyrevit_webview.log import debug_trace


def invoke_on_ui_sync(invoke_on_ui, action):
    # type: (InvokeOnUi, Callable[[], Any]) -> Any
    """Post ``action`` through ``invoke_on_ui`` and block until it finishes.

    The caller must already be off the UI thread. WPF and WinForms sync helpers
    run inline when they are already on that thread.
    """
    import threading

    gate = threading.Event()  # type: Any
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
