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

if sys.version_info >= (3, 5):
    from typing import (
        TYPE_CHECKING,
        BinaryIO,
        Callable,
        Dict,
        List,
        Optional,
        Set,
        Tuple,
        Type,
        TypeVar,
        Union,
        cast,
    )
else:
    # IronPython 2.7 / 3.4 have no typing module. Subscript must succeed so
    # aliases like Callable[[], None] can be assigned at import.
    TYPE_CHECKING = False

    class _Type(object):
        def __getitem__(self, _item):
            return self

    class _TypeVar(object):
        def __init__(self, name, *args, **kwargs):
            self.__name__ = name

    BinaryIO = Callable = Dict = List = Optional = Set = Tuple = Type = Union = _Type()
    TypeVar = _TypeVar

    def cast(_typ, value):
        return value

safe_strtype = str
if PY2:
    safe_strtype = lambda x: unicode(x)  # type: ignore[name-defined]  # noqa: F821


def json_load_error_types():
    # type: () -> Tuple[Type[BaseException], ...]
    decode_error = ValueError
    if PY3:
        import json
        decode_error = json.JSONDecodeError
    return (decode_error, ValueError, TypeError)


def urlopen(url):
    # type: (str) -> BinaryIO
    if PY3:
        return urllib_request.urlopen(url)
    return urllib2.urlopen(url)


def make_request(url, headers, data):
    # type: (str, Dict[str, str], bytes) -> None
    if PY3:
        req = urllib_request.Request(url, data=data, headers=headers)
        urllib_request.urlopen(req).close()
        return
    req = urllib2.Request(url, data, headers)
    urllib2.urlopen(req).close()
