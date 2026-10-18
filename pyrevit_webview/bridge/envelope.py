# -*- coding: utf-8 -*-
"""Command envelope shared by the page and the host.

A request is ``{type: "request", command, id, payload}``.
A response is ``{type: "response", command, id, payload|error}``.
An event is ``{type: "event", command, payload}``.
"""

from __future__ import division, print_function

from pyrevit_webview.compat import Any, Dict, Optional
from pyrevit_webview.log import debug_trace
from pyrevit_webview.serialize import deserialize

_PARSE = "envelope.parse_request"


def parse_request(raw_json):
    # type: (str) -> Optional[Dict[str, Any]]
    """Return ``{command, id, payload}`` or ``None`` when the message is ignored.

    A request without ``id`` is ignored. ``payload`` defaults to an empty object.
    """
    try:
        message = deserialize(raw_json)
    except (ValueError, TypeError) as exc:
        debug_trace(_PARSE, "invalid JSON: {0}".format(exc))
        return None

    if not isinstance(message, dict):
        debug_trace(_PARSE, "ignored non-object message")
        return None

    if message.get("type") != "request":
        debug_trace(_PARSE, "ignored message type: {0}".format(message.get("type")))
        return None

    msg_id = message.get("id")
    if msg_id is None or msg_id == "":
        debug_trace(_PARSE, "ignored request with no id")
        return None

    command = message.get("command")
    if command is None:
        command = ""
    else:
        command = str(command)

    payload = message.get("payload")
    if not isinstance(payload, dict):
        payload = {}

    return {
        "command": command,
        "id": msg_id,
        "payload": payload,
    }


def response_message(command, msg_id, payload=None, error=None):
    # type: (str, str, Any, Optional[str]) -> Dict[str, Any]
    """Build a response envelope. ``error`` replaces ``payload``."""
    message = {
        "type": "response",
        "command": command,
        "id": msg_id,
    }  # type: Dict[str, Any]
    if error is not None:
        message["error"] = str(error)
    else:
        message["payload"] = {"ok": True} if payload is None else payload
    return message


def event_message(command, payload):
    # type: (str, Any) -> Dict[str, Any]
    """Build an event envelope. Events have no id."""
    return {
        "type": "event",
        "command": command,
        "payload": payload,
    }
