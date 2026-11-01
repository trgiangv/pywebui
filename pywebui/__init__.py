# -*- coding: utf-8 -*-
"""One page, two ways to host it: a WebView2 window or the default browser.

Public surface (keep small)::

    from pywebui import Mode, Site
    from pywebui import Bridge, CommandRequest, parse_request, response_message, event_message
    from pywebui.webview import WebViewControl, WebViewSession, RemoteContent
    from pywebui.webview.wpf import WebView2, WpfUi
    from pywebui.http import HttpSink, HttpTransport    # CPython + FastAPI only
    from pywebui.adapter.revit import REVIT_CONTEXT

``pywebui.webview`` runs on IronPython and CPython. ``pywebui.http`` raises on
import under IronPython or when FastAPI is missing.
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
from pywebui.bridge.commands import Bridge
from pywebui.bridge.envelope import event_message, parse_request, response_message
from pywebui.bridge.message_router import RESPONSE_EVENT, MessageRouter
from pywebui.bridge.sink import EnvelopeSink
from pywebui.site import Mode, Site
from pywebui.webview.control import WebViewControl
from pywebui.webview.session import (
    PackagedContent,
    RemoteContent,
    WebViewSession,
    WebViewSettings,
)

LIB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # type: str
VERSION = "0.7.0"

__all__ = [
    "Bindable",
    "Bridge",
    "CommandRequest",
    "EnvelopeSink",
    "EnvelopeField",
    "EnvelopeKind",
    "EventName",
    "InvokeField",
    "InvokeKind",
    "MessageRouter",
    "Mode",
    "PackagedContent",
    "RemoteContent",
    "RESPONSE_EVENT",
    "Site",
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
