# -*- coding: utf-8 -*-
"""Command envelope shared by the page and the host.

A request is ``EnvelopeKind.REQUEST`` with command, id, and payload.
A response is ``EnvelopeKind.RESPONSE`` with payload or error.
An event is ``EnvelopeKind.EVENT`` and has no id.
Field names are ``EnvelopeField``.
"""

from __future__ import division, print_function

from pyrevit_webview.bridge.contract import (
    CommandRequest,
    EnvelopeField,
    EnvelopeKind,
)
from pyrevit_webview.compat import Dict, Optional, Union, cast
from pyrevit_webview.log import get_logger
from pyrevit_webview.serialize import JsonValue, deserialize

Envelope = Dict[str, Union[str, JsonValue]]


def parse_request(raw_json):
    # type: (str) -> Optional[CommandRequest]
    """Return a request, or ``None`` when the message is ignored.

    A request without ``id`` is ignored. ``payload`` defaults to an empty object.
    """
    try:
        message = deserialize(raw_json)
    except (ValueError, TypeError) as exc:
        get_logger().warning("envelope.parse_request | invalid JSON: {0}".format(exc))
        return None

    if not isinstance(message, dict):
        get_logger().warning("envelope.parse_request | ignored non-object message")
        return None

    kind = message.get(EnvelopeField.TYPE)
    if kind != EnvelopeKind.REQUEST:
        get_logger().warning(
            "envelope.parse_request | ignored message type: {0}".format(kind)
        )
        return None

    msg_id = message.get(EnvelopeField.ID)
    if msg_id is None or msg_id == "":
        get_logger().warning("envelope.parse_request | ignored request with no id")
        return None

    command = message.get(EnvelopeField.COMMAND)
    if command is None:
        command = ""
    else:
        command = str(command)

    payload = message.get(EnvelopeField.PAYLOAD)
    if not isinstance(payload, dict):
        payload = {}

    return CommandRequest(command, str(msg_id), payload)


def response_message(command, msg_id, payload=None, error=None):
    # type: (str, str, Optional[JsonValue], Optional[str]) -> Envelope
    """Build a response envelope. ``error`` replaces ``payload``."""
    message = {
        EnvelopeField.TYPE: EnvelopeKind.RESPONSE,
        EnvelopeField.COMMAND: command,
        EnvelopeField.ID: msg_id,
    }  # type: Envelope
    if error is not None:
        message[EnvelopeField.ERROR] = str(error)
    else:
        if payload is None:
            payload = {EnvelopeField.OK: True}
        message[EnvelopeField.PAYLOAD] = cast(JsonValue, payload)
    return message


def event_message(command, payload):
    # type: (str, JsonValue) -> Envelope
    """Build an event envelope. Events have no id."""
    return {
        EnvelopeField.TYPE: EnvelopeKind.EVENT,
        EnvelopeField.COMMAND: command,
        EnvelopeField.PAYLOAD: payload,
    }
