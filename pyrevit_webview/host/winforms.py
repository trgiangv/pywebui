# -*- coding: utf-8 -*-
"""WinForms WebView2 control and the form thread that owns it."""

from __future__ import print_function, division

from pyrevit_webview.loader import load_bin

load_bin()

from Microsoft.Web.WebView2.WinForms import WebView2  # noqa: E402
from System import EventArgs  # noqa: E402
from System.Windows.Forms import Control  # noqa: E402

from pyrevit_webview.compat import Callable
from pyrevit_webview.host.invoke import UiThread
from pyrevit_webview.log import debug_trace

__all__ = ["WebView2", "WinFormsUi"]


class WinFormsUi(UiThread):
    """Form thread and the ``HandleCreated`` gate of its WebView2."""

    def __init__(self, form, webview):
        # type: (Control, WebView2) -> None
        self._form = form
        self._webview = webview

    def post(self, action):
        # type: (Callable[[], None]) -> None
        from System.Windows.Forms import MethodInvoker

        debug_trace("WinFormsUi.post", "BeginInvoke")
        self._form.BeginInvoke(MethodInvoker(action))

    def on_thread(self):
        # type: () -> bool
        return not self._form.InvokeRequired

    def after_hosted(self, start):
        # type: (Callable[[], None]) -> Callable[[], None]
        webview = self._webview
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
