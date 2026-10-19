# -*- coding: utf-8 -*-
"""PostWebMessage router for WebView2 ↔ Python communication."""

from __future__ import print_function, division

from pyrevit_webview.bridge.contract import EventName, InvokeField
from pyrevit_webview.compat import TYPE_CHECKING, Callable, Dict, Optional, Union
from pyrevit_webview.serialize import JsonValue, deserialize, serialize
from pyrevit_webview.loader import load_clr_types

if TYPE_CHECKING:
    from Microsoft.Web.WebView2.Core import CoreWebView2
from pyrevit_webview.log import debug_trace

load_clr_types()

RESPONSE_EVENT = EventName.BRIDGE_RESPONSE  # type: str
_TRACE_HANDLE_RAW = "MessageRouter.handle_raw"  # type: str


class MessageRouter(object):
    """Registry-based dispatcher for ``WebMessageReceived`` / ``postMessage``."""

    def __init__(self, core, invoke_on_ui):
        # type: (CoreWebView2, Callable[[Callable[[], None]], None]) -> None
        self._core = core  # type: CoreWebView2
        self._invoke_on_ui = invoke_on_ui  # type: Callable[[Callable[[], None]], None]
        self._handlers = {}  # type: Dict[str, Callable[[Dict[str, JsonValue]], None]]

    def register(self, message_type, handler):
        # type: (str, Callable[[Dict[str, JsonValue]], None]) -> None
        self._handlers[message_type] = handler

    def handle_raw(self, raw_json):
        # type: (str) -> None
        """Parse JSON from ``WebMessageReceived`` and dispatch."""
        message = _parse_message(raw_json)
        if message is None:
            return
        self._dispatch_message(message)

    def respond(self, request_id, ok, data=None, error=None):
        # type: (str, bool, Optional[JsonValue], Optional[str]) -> None
        """Emit a request/response payload to the page."""
        payload = {
            InvokeField.ID: request_id,
            InvokeField.OK: ok,
        }  # type: Dict[str, Union[str, bool, JsonValue]]
        if ok:
            payload[InvokeField.DATA] = data
        else:
            payload[InvokeField.ERROR] = error or "Unknown error"
        self.emit(RESPONSE_EVENT, payload)

    def emit(self, event_name, detail):
        # type: (str, Dict[str, JsonValue]) -> None
        """Dispatch a ``CustomEvent`` to the frontend via ``ExecuteScriptAsync``."""
        encoded = serialize(detail)
        script = (
            "window.dispatchEvent(new CustomEvent('{0}',"
            "{{detail:JSON.parse({1})}}));"
        ).format(event_name, serialize(encoded))

        def run():
            # type: () -> None
            try:
                self._core.ExecuteScriptAsync(script)
            except Exception as exc:
                debug_trace("MessageRouter.emit", "FAILED: {0!r}".format(exc))

        self._invoke_on_ui(run)

    def _dispatch_message(self, message):
        # type: (Dict[str, JsonValue]) -> None
        msg_type = message.get(InvokeField.TYPE)
        # IronPython 2 str and unicode are different types.
        if not isinstance(msg_type, (str, type(u""))):
            debug_trace(
                _TRACE_HANDLE_RAW,
                "missing type: {0}".format(msg_type),
            )
            return
        handler = self._handlers.get(msg_type)
        if handler is None:
            debug_trace(_TRACE_HANDLE_RAW, "unknown type: {0}".format(msg_type))
            return

        try:
            handler(message)
        except Exception as exc:
            debug_trace(
                _TRACE_HANDLE_RAW,
                "handler error ({0}): {1!r}".format(msg_type, exc),
            )
            request_id = message.get(InvokeField.ID)
            if isinstance(request_id, str) and request_id:
                self.respond(request_id, ok=False, error=str(exc))


def _parse_message(raw_json):
    # type: (str) -> Optional[Dict[str, JsonValue]]
    try:
        message = deserialize(raw_json)
    except Exception as exc:
        debug_trace(_TRACE_HANDLE_RAW, "invalid JSON: {0!r}".format(exc))
        return None

    if not isinstance(message, dict):
        debug_trace(_TRACE_HANDLE_RAW, "message is not an object")
        return None
    return message
