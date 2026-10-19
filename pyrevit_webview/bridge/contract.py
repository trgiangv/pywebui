# -*- coding: utf-8 -*-
"""Wire names for the two page protocols.

Values are the JSON text. Use them as dict keys and as comparisons.
``CommandRequest`` is the parsed command-envelope request.
"""

from __future__ import division, print_function

from pyrevit_webview.compat import Dict
from pyrevit_webview.serialize import JsonValue


class EnvelopeKind(object):
    """``type`` values of the command envelope."""

    REQUEST = "request"  # type: str
    RESPONSE = "response"  # type: str
    EVENT = "event"  # type: str


class EnvelopeField(object):
    """Keys of a command-envelope object."""

    TYPE = "type"  # type: str
    COMMAND = "command"  # type: str
    ID = "id"  # type: str
    PAYLOAD = "payload"  # type: str
    ERROR = "error"  # type: str
    OK = "ok"  # type: str


class InvokeKind(object):
    """``type`` value of ``@bridge_callable``."""

    INVOKE = "invoke"  # type: str


class InvokeField(object):
    """Keys of an invoke message and of its ``bridge-response`` detail."""

    TYPE = "type"  # type: str
    ID = "id"  # type: str
    METHOD = "method"  # type: str
    PARAMS = "params"  # type: str
    OK = "ok"  # type: str
    DATA = "data"  # type: str
    ERROR = "error"  # type: str


class EventName(object):
    """``CustomEvent`` names the library dispatches."""

    BRIDGE_RESPONSE = "bridge-response"  # type: str


class CommandRequest(object):
    """One accepted command-envelope request."""

    def __init__(self, command, request_id, payload):
        # type: (str, str, Dict[str, JsonValue]) -> None
        self.command = command  # type: str
        self.id = request_id  # type: str
        self.payload = payload  # type: Dict[str, JsonValue]
