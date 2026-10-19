# -*- coding: utf-8 -*-
"""Framework-neutral WebView2 host.

UI dispatch lives next to the toolkit that owns the window:

    from pyrevit_webview.host.wpf import WebView2, WpfUi
    from pyrevit_webview.host.winforms import WebView2, WinFormsUi

Revit thread dispatch lives in ``pyrevit_webview.adapter.revit``.
"""

from __future__ import print_function, division

from pyrevit_webview.host.control import WebViewControl
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
]
