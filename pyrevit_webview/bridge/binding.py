# -*- coding: utf-8 -*-
"""Python binding base class and @bridge_callable decorator."""

from __future__ import print_function, division

from pyrevit_webview.compat import Callable, Dict, Optional, Union, cast
from pyrevit_webview.serialize import JsonValue

BridgeMethod = Callable[..., JsonValue]

BRIDGE_CALLABLE_ATTR = "__bridge_callable__"  # type: str
BRIDGE_CALLABLE_NAME_ATTR = "__bridge_callable_name__"  # type: str


def bridge_callable(method_name=None):
    # type: (Optional[Union[str, BridgeMethod]]) -> Union[BridgeMethod, Callable[[BridgeMethod], BridgeMethod]]
    """Mark a method as callable from the WebView frontend.

    Usage::

        @bridge_callable("GetGreeting")
        def get_greeting(self):
            return {"message": "Hello"}
    """

    def decorator(fn):
        # type: (BridgeMethod) -> BridgeMethod
        setattr(fn, BRIDGE_CALLABLE_ATTR, True)
        if method_name is not None:
            setattr(fn, BRIDGE_CALLABLE_NAME_ATTR, method_name)
        return fn

    if callable(method_name):
        fn = method_name  # type: ignore[assignment]
        setattr(fn, BRIDGE_CALLABLE_ATTR, True)
        return fn

    return decorator


class Bindable(object):
    """Base class for handlers exposed to the frontend via ``postMessage``."""

    name = ""  # type: str
    parent = None  # type: Optional[Bindable]

    def binding_methods(self):
        # type: () -> Dict[str, BridgeMethod]
        """Return ``{frontendMethodName: callable}`` for decorated methods."""
        methods = {}  # type: Dict[str, BridgeMethod]
        for key in dir(self):
            if key.startswith("_"):
                continue
            member = getattr(self, key)
            if not callable(member):
                continue
            if not getattr(member, BRIDGE_CALLABLE_ATTR, False):
                continue
            frontend_name = getattr(member, BRIDGE_CALLABLE_NAME_ATTR, None)
            if frontend_name is None:
                frontend_name = key
            methods[frontend_name] = cast(BridgeMethod, member)
        return methods
