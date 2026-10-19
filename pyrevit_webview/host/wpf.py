# -*- coding: utf-8 -*-
"""WPF WebView2 control and the dispatcher that owns it."""

from __future__ import print_function, division

from pyrevit_webview.loader import load_bin

load_bin()

from Microsoft.Web.WebView2.Wpf import WebView2  # noqa: E402
from System.Windows import RoutedEventArgs  # noqa: E402
from System.Windows.Threading import DispatcherObject  # noqa: E402

from pyrevit_webview.compat import Callable
from pyrevit_webview.host.invoke import UiThread
from pyrevit_webview.log import debug_trace

__all__ = ["WebView2", "WpfUi"]


class WpfUi(UiThread):
    """Dispatcher of a WPF window and the ``Loaded`` gate of its WebView2."""

    def __init__(self, window, webview):
        # type: (DispatcherObject, WebView2) -> None
        self._dispatcher = window.Dispatcher
        self._webview = webview

    def post(self, action):
        # type: (Callable[[], None]) -> None
        from System import Action
        from System.Windows.Threading import DispatcherPriority

        debug_trace("WpfUi.post", "BeginInvoke")
        self._dispatcher.BeginInvoke(DispatcherPriority.Normal, Action(action))

    def on_thread(self):
        # type: () -> bool
        return self._dispatcher.CheckAccess()

    def after_hosted(self, start):
        # type: (Callable[[], None]) -> Callable[[], None]
        webview = self._webview
        if webview.IsLoaded:
            start()
            return lambda: None

        armed = {"on": True}

        def on_loaded(sender, args):
            # type: (WebView2, RoutedEventArgs) -> None
            if not armed["on"]:
                return
            armed["on"] = False
            webview.Loaded -= on_loaded
            start()

        def cancel():
            # type: () -> None
            if not armed["on"]:
                return
            armed["on"] = False
            webview.Loaded -= on_loaded

        webview.Loaded += on_loaded
        return cancel
