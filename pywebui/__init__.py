# -*- coding: utf-8 -*-
"""WebView2 + Python bridge for pyRevit / IronPython / pythonnet.

Public surface (keep small)::

    from pywebui import Bindable, bridge_callable, MessageRouter
    from pywebui import CommandRequest, parse_request, response_message, event_message
    from pywebui.webview import WebViewControl, WebViewSession, PackagedContent
    from pywebui.webview.wpf import WebView2, WpfUi
    from pywebui.adapter.revit import REVIT_CONTEXT

Bridge uses ``postMessage`` / ``MessageRouter`` — no COM host objects.
"""

from __future__ import division, print_function

import os

from pywebui.bridge.binding import Bindable, bridge_callable
from pywebui.bridge.contract import (
    CommandRequest,
    EnvelopeField,
    EnvelopeKind,
    EventName,
    InvokeField,
    InvokeKind,
)
from pywebui.bridge.envelope import event_message, parse_request, response_message
from pywebui.bridge.message_router import RESPONSE_EVENT, MessageRouter
from pywebui.webview.control import WebViewControl
from pywebui.webview.session import (
    PackagedContent,
    RemoteContent,
    WebViewSession,
    WebViewSettings,
)

LIB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # type: str
VERSION = "0.6.0"

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
