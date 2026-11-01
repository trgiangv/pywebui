# -*- coding: utf-8 -*-
"""Wire names for the two page protocols.

Values are the JSON text. Use them as dict keys and as comparisons.
``CommandRequest`` is the parsed command-envelope request.
"""

from __future__ import division, print_function

from pywebui.compat import Dict
from pywebui.serialize import JsonValue


class EnvelopeKind(object):
    """``type`` values of the command envelope."""

    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"


class EnvelopeField(object):
    """Keys of a command-envelope object."""

    TYPE = "type"
    COMMAND = "command"
    ID = "id"
    PAYLOAD = "payload"
    ERROR = "error"
    OK = "ok"


class InvokeKind(object):
    """``type`` value of ``@bridge_callable``."""

    INVOKE = "invoke"


class InvokeField(object):
    """Keys of an invoke message and of its ``bridge-response`` detail."""

    TYPE = "type"
    ID = "id"
    METHOD = "method"
    PARAMS = "params"
    OK = "ok"
    DATA = "data"
    ERROR = "error"


class EventName(object):
    """``CustomEvent`` names the library dispatches."""

    BRIDGE_RESPONSE = "bridge-response"


class CommandRequest(object):
    """One accepted command-envelope request."""

    def __init__(self, command, request_id, payload):
        # type: (str, str, Dict[str, JsonValue]) -> None
        self.command = command  # type: str
        self.id = request_id  # type: str
        self.payload = payload  # type: Dict[str, JsonValue]
