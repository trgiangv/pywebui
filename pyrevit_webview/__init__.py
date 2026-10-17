# -*- coding: utf-8 -*-
"""WebView2 + Python bridge for pyRevit / IronPython / pythonnet.

Public surface (keep small)::

    from pyrevit_webview import Bindable, bridge_callable, MessageRouter
    from pyrevit_webview.host import WebViewControl, WebViewSession, PackagedContent, wpf_invoke
    from pyrevit_webview.host.wpf import WebView2
    from pyrevit_webview.adapter.revit import initialize_revit_task, revit_invoke_sync

Bridge uses ``postMessage`` / ``MessageRouter`` — no COM host objects.
"""

from __future__ import print_function, division

import os

from pyrevit_webview.bridge.binding import Bindable, bridge_callable
from pyrevit_webview.bridge.message_router import MessageRouter, RESPONSE_EVENT
from pyrevit_webview.host.control import WebViewControl
from pyrevit_webview.host.session import (
    PackagedContent,
    RemoteContent,
    WebViewSession,
    WebViewSettings,
)

LIB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = "0.6.0"

__all__ = [
    "Bindable",
    "MessageRouter",
    "PackagedContent",
    "RemoteContent",
    "RESPONSE_EVENT",
    "WebViewControl",
    "WebViewSession",
    "WebViewSettings",
    "bridge_callable",
    "VERSION",
    "LIB_DIR",
]
