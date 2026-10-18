# -*- coding: utf-8 -*-
"""Framework-neutral WebView2 host.

UI dispatch lives next to the toolkit that owns the window:

    from pyrevit_webview.host.wpf import WebView2, wpf_invoke, wpf_when_ready
    from pyrevit_webview.host.winforms import WebView2, winforms_invoke, winforms_when_ready

Revit thread dispatch lives in ``pyrevit_webview.adapter.revit``.
"""

from __future__ import print_function, division

from pyrevit_webview.host.control import WebViewControl
from pyrevit_webview.host.invoke import invoke_on_ui_sync
from pyrevit_webview.host.session import (
    PackagedContent,
    RemoteContent,
    WebViewSession,
    WebViewSettings,
)

__all__ = [
    "PackagedContent",
    "RemoteContent",
    "WebViewControl",
    "WebViewSession",
    "WebViewSettings",
    "invoke_on_ui_sync",
]
