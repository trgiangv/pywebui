# -*- coding: utf-8 -*-
"""WPF WebView2 control — loads managed DLLs then re-exports the CLR type."""

from __future__ import print_function, division

from pyrevit_webview.dotnet import load_bin

load_bin()

from Microsoft.Web.WebView2.Wpf import WebView2  # noqa: E402
from System.Windows import RoutedEventArgs  # noqa: E402
from System.Windows.Threading import DispatcherObject  # noqa: E402

from pyrevit_webview.compat import Any, Callable
from pyrevit_webview.log import debug_trace
from pyrevit_webview.types import InvokeOnUi

__all__ = ["WebView2", "wpf_invoke", "wpf_invoke_sync", "wpf_when_ready"]


def wpf_invoke(control):
    # type: (DispatcherObject) -> InvokeOnUi
    """Return an invoke that posts through ``Dispatcher.BeginInvoke``."""
    from System import Action
    from System.Windows.Threading import DispatcherPriority

    dispatcher = control.Dispatcher

    def invoke(action):
        # type: (Callable[[], None]) -> None
        debug_trace("wpf_invoke.BeginInvoke", "post")
        dispatcher.BeginInvoke(DispatcherPriority.Normal, Action(action))

    return invoke


def wpf_invoke_sync(control, action):
    # type: (DispatcherObject, Callable[[], Any]) -> Any
    """Run ``action`` on the WPF dispatcher and wait.

    Runs inline when ``Dispatcher.CheckAccess`` is already true.
    """
    from pyrevit_webview.host.invoke import invoke_on_ui_sync

    if control.Dispatcher.CheckAccess():
        debug_trace("wpf_invoke_sync", "inline (CheckAccess)")
        return action()
    return invoke_on_ui_sync(wpf_invoke(control), action)


def wpf_when_ready(webview):
    # type: (WebView2) -> Callable[[Callable[[], None]], Callable[[], None]]
    """Return a scheduler that runs once the WPF control has a handle."""

    def when_ready(start):
        # type: (Callable[[], None]) -> Callable[[], None]
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

    return when_ready
