# -*- coding: utf-8 -*-
"""WebView2 + Python bridge for pyRevit / IronPython / pythonnet.

Public surface (keep small)::

    from pyrevit_webview import Bindable, bridge_callable, MessageRouter
    from pyrevit_webview import CommandRequest, parse_request, response_message, event_message
    from pyrevit_webview.host import WebViewControl, WebViewSession, PackagedContent
    from pyrevit_webview.host.wpf import WebView2, WpfUi
    from pyrevit_webview.adapter.revit import REVIT_CONTEXT

Bridge uses ``postMessage`` / ``MessageRouter`` — no COM host objects.
"""

from __future__ import division, print_function

import os

from pyrevit_webview.bridge.binding import Bindable, bridge_callable
from pyrevit_webview.bridge.contract import (
    CommandRequest,
    EnvelopeField,
    EnvelopeKind,
    EventName,
    InvokeField,
    InvokeKind,
)
from pyrevit_webview.bridge.envelope import event_message, parse_request, response_message
from pyrevit_webview.bridge.message_router import RESPONSE_EVENT, MessageRouter
from pyrevit_webview.host.control import WebViewControl
from pyrevit_webview.host.session import (
    PackagedContent,
    RemoteContent,
    WebViewSession,
    WebViewSettings,
)

LIB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # type: str
VERSION = "0.6.0"  # type: str

__all__ = [
    "Bindable",
    "CommandRequest",
    "EnvelopeField",
    "EnvelopeKind",
    "EventName",
    "InvokeField",
    "InvokeKind",
    "MessageRouter",
    "PackagedContent",
    "RemoteContent",
    "RESPONSE_EVENT",
    "WebViewControl",
    "WebViewSession",
    "WebViewSettings",
    "bridge_callable",
    "event_message",
    "parse_request",
    "response_message",
    "VERSION",
    "LIB_DIR",
]
