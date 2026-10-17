# -*- coding: utf-8 -*-
"""Python / IronPython / CPython compatibility."""

from __future__ import print_function, division

import sys

import System

PY2 = sys.version_info[0] == 2  # type: bool
PY3 = sys.version_info[0] == 3  # type: bool
IRONPY = ".net" in sys.version.lower()  # type: bool
IRONPY2 = PY2 and IRONPY  # type: bool
IRONPY3 = PY3 and IRONPY  # type: bool
CPYTHON = PY3 and not IRONPY  # type: bool
NETCORE = System.Environment.Version.Major >= 8  # type: bool
NETFRAMEWORK = not NETCORE  # type: bool

if PY3:
    __builtins__["unicode"] = str

if PY2:
    import _winreg as winreg  # pyright: ignore[reportMissingImports]
    import ConfigParser as configparser  # pyright: ignore[reportMissingImports]
    import urllib2  # pyright: ignore[reportMissingImports]
    from urlparse import urlparse  # pyright: ignore[reportMissingImports]
elif PY3:
    import winreg as winreg
    import configparser as configparser
    import urllib.request as urllib_request
    from urllib.parse import urlparse

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, List, Optional, Union
else:
    # Runtime, including IronPython 2.7 / 3.4 (no typing module). Subscript
    # must succeed so aliases like Callable[[], None] can be assigned at import.
    class _Type(object):
        def __getitem__(self, _item):
            return self

    Any = Callable = Dict = List = Optional = Union = _Type()

safe_strtype = str
if PY2:
    safe_strtype = lambda x: unicode(x)  # type: ignore[name-defined]  # noqa: F821


def json_load_error_types():
    # type: () -> tuple
    if PY3:
        import json
        return (json.JSONDecodeError, ValueError, TypeError)
    return (ValueError, TypeError)


def urlopen(url):
    # type: (str) -> Any
    if PY3:
        return urllib_request.urlopen(url)
    return urllib2.urlopen(url)


def make_request(url, headers, data):
    # type: (str, dict, Any) -> None
    if PY3:
        req = urllib_request.Request(url, headers, data)
        urllib_request.urlopen(req).close()
        return
    req = urllib2.Request(url, headers, data)
    urllib2.urlopen(req).close()
