# -*- coding: utf-8 -*-
"""Python / IronPython / CPython compatibility."""

from __future__ import print_function, division

import sys

import System

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
IRONPY = ".net" in sys.version.lower()
IRONPY2 = PY2 and IRONPY
IRONPY3 = PY3 and IRONPY
CPYTHON = PY3 and not IRONPY
NETCORE = System.Environment.Version.Major >= 8
NETFRAMEWORK = not NETCORE

if PY3:
    __builtins__["unicode"] = str

if PY2:
    import _winreg as winreg  # pyright: ignore[reportMissingImports]
    import ConfigParser as configparser  # pyright: ignore[reportMissingImports]
    from collections import Iterable, Callable  # pyright: ignore[reportAttributeAccessIssue]
    import urllib2  # pyright: ignore[reportMissingImports]
    from urlparse import urlparse  # pyright: ignore[reportMissingImports]
elif PY3:
    import winreg as winreg
    import configparser as configparser
    from collections.abc import Iterable, Callable
    import urllib.request as urllib_request
    from urllib.parse import urlparse

if CPYTHON:
    from typing import Any, Callable as TypingCallable, Dict, List, Optional, Union
else:
    Any = object
    TypingCallable = object
    Dict = dict
    List = list
    Optional = object
    Union = object

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
