# -*- coding: utf-8 -*-
"""Wire :class:`Bindable` instances to :class:`MessageRouter`."""

from __future__ import print_function, division

import inspect

from pyrevit_webview.bridge.binding import Bindable
from pyrevit_webview.bridge.message_router import MessageRouter
from pyrevit_webview.compat import Callable, Dict, List, Any
from pyrevit_webview.log import debug_trace


INVOKE_MESSAGE_TYPE = "invoke"  # type: str


def register_message_bindings(bindings, router):
    # type: (List[Bindable], MessageRouter) -> None
    """Register ``@bridge_callable`` methods on the message router."""
    methods = _collect_binding_methods(bindings)
    router.register(INVOKE_MESSAGE_TYPE, _make_invoke_handler(methods, router))
    debug_trace("register_message_bindings", "done count={0}".format(len(methods)))


def _collect_binding_methods(bindings):
    # type: (List[Bindable]) -> Dict[str, Callable]
    methods = {}  # type: Dict[str, Callable]
    for binding in bindings:
        for method_name, method in binding.binding_methods().items():
            if method_name in methods:
                raise ValueError(
                    "Duplicate bridge method '{0}' across bindings.".format(method_name)
                )
            methods[method_name] = method
            debug_trace("register_message_bindings", method_name)
    return methods


def _make_invoke_handler(methods, router):
    # type: (Dict[str, Callable], MessageRouter) -> Callable

    def handle_invoke(message):
        # type: (Dict[str, Any]) -> None
        request_id = message.get("id")
        method_name = message.get("method")
        params = _normalize_params(message.get("params"))

        if not request_id:
            debug_trace("handle_invoke", "missing id")
            return
        if not method_name:
            router.respond(request_id, ok=False, error="Missing method name.")
            return

        method = methods.get(method_name)
        if method is None:
            router.respond(
                request_id,
                ok=False,
                error="Unknown method: {0}".format(method_name),
            )
            return

        _invoke_binding_method(router, request_id, method, method_name, params)

    return handle_invoke


def _normalize_params(params):
    # type: (Any) -> List[Any]
    if params is None:
        return []
    if isinstance(params, list):
        return params
    return [params]


def _invoke_binding_method(router, request_id, method, method_name, params):
    # type: (MessageRouter, str, Callable, str, List[Any]) -> None
    label = getattr(method, "__name__", method_name)
    debug_trace("handle_invoke", "enter {0}".format(label))
    try:
        _validate_argument_count(method, method_name, params)
        result = method(*params)
        debug_trace("handle_invoke", "leave {0}".format(label))
        router.respond(request_id, ok=True, data=result)
    except Exception as exc:
        debug_trace("handle_invoke", "FAILED {0}: {1!r}".format(label, exc))
        router.respond(request_id, ok=False, error=str(exc))


def _validate_argument_count(method, method_name, params):
    # type: (Callable, str, List[Any]) -> None
    """Fail with a useful bridge error before invoking a method with bad arity.

    Some CLR callables and decorators do not expose an inspectable signature; those
    continue to rely on the invocation error, preserving support for those methods.
    """
    try:
        getargspec = getattr(inspect, "getfullargspec", None)
        if getargspec is None:
            getargspec = inspect.getargspec
        spec = getargspec(method)
    except (TypeError, ValueError, AttributeError):
        return

    args = list(spec.args)
    if getattr(method, "__self__", None) is not None and args:
        args.pop(0)
    defaults = spec.defaults or ()
    required = len(args) - len(defaults)
    maximum = None if spec.varargs else len(args)
    count = len(params)
    if count < required or (maximum is not None and count > maximum):
        if maximum is None:
            expected = "at least {0}".format(required)
        elif required == maximum:
            expected = str(required)
        else:
            expected = "{0} to {1}".format(required, maximum)
        raise TypeError(
            "Invalid arguments for '{0}': expected {1}, got {2}.".format(
                method_name, expected, count
            )
        )
