# -*- coding: utf-8 -*-
"""WinForms WebView2 control — loads managed DLLs then re-exports the CLR type."""

from __future__ import print_function, division

from pyrevit_webview.dotnet import load_bin

load_bin()

from Microsoft.Web.WebView2.WinForms import WebView2  # noqa: E402
from System import EventArgs  # noqa: E402
from System.Windows.Forms import Control  # noqa: E402

from pyrevit_webview.compat import Any, Callable
from pyrevit_webview.log import debug_trace
from pyrevit_webview.types import InvokeOnUi

__all__ = ["WebView2", "winforms_invoke", "winforms_invoke_sync", "winforms_when_ready"]


def winforms_invoke(form):
    # type: (Control) -> InvokeOnUi
    """Return an invoke that posts through ``Form.BeginInvoke``."""
    from System.Windows.Forms import MethodInvoker

    def invoke(action):
        # type: (Callable[[], None]) -> None
        debug_trace("winforms_invoke.BeginInvoke", "post")
        form.BeginInvoke(MethodInvoker(action))

    return invoke


def winforms_invoke_sync(form, action):
    # type: (Control, Callable[[], Any]) -> Any
    """Run ``action`` on the WinForms UI thread and wait.

    Runs inline when ``InvokeRequired`` is false.
    """
    from pyrevit_webview.host.invoke import invoke_on_ui_sync

    if not form.InvokeRequired:
        debug_trace("winforms_invoke_sync", "inline")
        return action()
    return invoke_on_ui_sync(winforms_invoke(form), action)


def winforms_when_ready(webview):
    # type: (WebView2) -> Callable[[Callable[[], None]], Callable[[], None]]
    """Return a scheduler that runs once the WinForms control has a handle."""

    def when_ready(start):
        # type: (Callable[[], None]) -> Callable[[], None]
        if webview.IsHandleCreated:
            start()
            return lambda: None

        armed = {"on": True}

        def on_handle(sender, args):
            # type: (WebView2, EventArgs) -> None
            if not armed["on"]:
                return
            armed["on"] = False
            webview.HandleCreated -= on_handle  # pyright: ignore[reportOperatorIssue]
            start()

        def cancel():
            # type: () -> None
            if not armed["on"]:
                return
            armed["on"] = False
            webview.HandleCreated -= on_handle  # pyright: ignore[reportOperatorIssue]

        webview.HandleCreated += on_handle  # pyright: ignore[reportOperatorIssue]
        return cancel

    return when_ready
