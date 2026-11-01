# -*- coding: utf-8 -*-
"""Framework-neutral WebView2 host.

UI dispatch lives next to the toolkit that owns the window:

    from pywebui.webview.wpf import WebView2, WpfUi
    from pywebui.webview.winforms import WebView2, WinFormsUi

Revit thread dispatch lives in ``pywebui.adapter.revit``.
"""

from __future__ import print_function, division

from pywebui.webview.control import WebViewControl
from pywebui.webview.session import (
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
