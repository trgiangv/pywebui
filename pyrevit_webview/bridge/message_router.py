# -*- coding: utf-8 -*-
"""PostWebMessage router for WebView2 ↔ Python communication."""

from __future__ import print_function, division

import json

from pyrevit_webview.compat import Any, Callable, Dict, Optional
from pyrevit_webview.dotnet import bootstrap_clr
from pyrevit_webview.types import InvokeOnUi
from pyrevit_webview.log import debug_trace

bootstrap_clr()
from pyrevit_webview.dotnet import CoreWebView2

RESPONSE_EVENT = "bridge-response"


class MessageRouter(object):
    """Registry-based dispatcher for ``WebMessageReceived`` / ``postMessage``."""

    def __init__(self, core, invoke_on_ui):
        # type: (CoreWebView2, InvokeOnUi) -> None
        self._core = core
        self._invoke_on_ui = invoke_on_ui
        self._handlers = {}  # type: Dict[str, Callable]

    def register(self, message_type, handler):
        # type: (str, Callable) -> None
        self._handlers[message_type] = handler

    def handle_raw(self, raw_json):
        # type: (str) -> None
        """Parse JSON from ``WebMessageReceived`` and dispatch."""
        message = _parse_message(raw_json)
        if message is None:
            return
        self._dispatch_message(message)

    def respond(self, request_id, ok, data=None, error=None):
        # type: (str, bool, Any, Optional[str]) -> None
        """Emit a request/response payload to the page."""
        payload = {"id": request_id, "ok": ok}
        if ok:
            payload["data"] = data
        else:
            payload["error"] = error or "Unknown error"
        self.emit(RESPONSE_EVENT, payload)

    def emit(self, event_name, detail):
        # type: (str, dict) -> None
        """Dispatch a ``CustomEvent`` to the frontend via ``ExecuteScriptAsync``."""
        json_str = json.dumps(detail)
        script = (
            "window.dispatchEvent(new CustomEvent('{0}',"
            "{{detail:JSON.parse({1})}}));"
        ).format(event_name, json.dumps(json_str))

        def run():
            # type: () -> None
            try:
                self._core.ExecuteScriptAsync(script)
            except Exception as exc:
                debug_trace("MessageRouter.emit", "FAILED: {0!r}".format(exc))

        self._invoke_on_ui(run)

    def _dispatch_message(self, message):
        # type: (dict) -> None
        msg_type = message.get("type")
        handler = self._handlers.get(msg_type)
        if handler is None:
            debug_trace("MessageRouter.handle_raw", "unknown type: {0}".format(msg_type))
            return

        try:
            handler(message)
        except Exception as exc:
            debug_trace(
                "MessageRouter.handle_raw",
                "handler error ({0}): {1!r}".format(msg_type, exc),
            )
            request_id = message.get("id")
            if request_id:
                self.respond(request_id, ok=False, error=str(exc))


def _parse_message(raw_json):
    # type: (str) -> Optional[dict]
    try:
        message = json.loads(raw_json)
    except Exception as exc:
        debug_trace("MessageRouter.handle_raw", "invalid JSON: {0!r}".format(exc))
        return None

    if not isinstance(message, dict):
        debug_trace("MessageRouter.handle_raw", "message is not an object")
        return None
    return message
