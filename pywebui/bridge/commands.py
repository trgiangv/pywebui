# -*- coding: utf-8 -*-
"""Command registry shared by the WebView2 and HTTP transports."""

from __future__ import print_function, division

import traceback

from pywebui.bridge.contract import CommandRequest
from pywebui.bridge.envelope import Envelope, response_message
from pywebui.compat import Callable, Dict, Optional
from pywebui.log import get_logger
from pywebui.serialize import JsonValue

CommandHandler = Callable[[Dict[str, JsonValue]], Optional[JsonValue]]


class Bridge(object):
    """Maps a command name to a function that takes the request payload.

    Usage::

        bridge = Bridge()

        @bridge.command("Zoom")
        def zoom(payload):
            return {"ok": True}
    """

    def __init__(self):
        # type: () -> None
        self._commands = {}  # type: Dict[str, CommandHandler]

    def command(self, name=None):
        # type: (Optional[str]) -> Callable[[CommandHandler], CommandHandler]
        """Register the decorated function. The name defaults to the function name."""

        def decorator(handler):
            # type: (CommandHandler) -> CommandHandler
            self.add(name or handler.__name__, handler)
            return handler

        return decorator

    def add(self, name, handler):
        # type: (str, CommandHandler) -> None
        if name in self._commands:
            raise ValueError("Duplicate command '{0}'.".format(name))
        self._commands[name] = handler

    def run(self, request):
        # type: (CommandRequest) -> Envelope
        """Run the handler and return the response envelope. Never raises."""
        handler = self._commands.get(request.command)
        if handler is None:
            return response_message(
                request.command,
                request.id,
                error="Unknown command: {0}".format(request.command),
            )
        try:
            result = handler(request.payload)
        except Exception as exc:
            get_logger().error(
                "command {0} failed: {1}\n{2}".format(request.command, exc, traceback.format_exc())
            )
            return response_message(request.command, request.id, error=str(exc))
        return response_message(request.command, request.id, payload=result)
