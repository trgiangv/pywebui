# -*- coding: utf-8 -*-
"""JSON for the bridge.

CPython uses the standard ``json`` module. IronPython goes through Newtonsoft:
a dict passed straight to ``SerializeObject`` is reflected as a CLR object, and
that walk runs until the host looks stuck. Values are copied into ``Dictionary``
and ``List`` first. Reading uses ``JsonTextReader`` so a ``JToken`` dynamic
member is never touched.
"""

from __future__ import print_function, division

import json

from pywebui.compat import CPYTHON, Dict, List, Union

JsonValue = Union[None, bool, int, float, str, List["JsonValue"], Dict[str, "JsonValue"]]

_TRUNCATED_JSON = "truncated JSON"

_convert = None
_settings = None


def serialize(value):
    # type: (JsonValue) -> str
    if CPYTHON:
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"), default=str)
    convert, settings = _newtonsoft()
    return convert.SerializeObject(_clr(value), settings)  # pyright: ignore[reportCallIssue, reportArgumentType]


def deserialize(text):
    # type: (str) -> JsonValue
    if CPYTHON:
        return json.loads(text)
    _newtonsoft()
    from Newtonsoft.Json import DateParseHandling, JsonTextReader, JsonToken
    from System.IO import StringReader

    reader = JsonTextReader(StringReader(text))
    reader.DateParseHandling = getattr(DateParseHandling, "None")
    if not reader.Read():
        raise ValueError("empty JSON")
    return _read(reader, JsonToken)


def _newtonsoft():
    global _convert, _settings
    if _convert is None:
        from pywebui.loader import load_bin

        load_bin()
        from Newtonsoft.Json import JsonConvert, JsonSerializerSettings, StringEscapeHandling

        settings = JsonSerializerSettings()
        settings.StringEscapeHandling = StringEscapeHandling.EscapeNonAscii
        _convert = JsonConvert
        _settings = settings
    return _convert, _settings


def _clr(value):
    """Copy a JSON value into CLR collections Newtonsoft can serialize."""
    from System import Object, String
    from System.Collections.Generic import Dictionary, List

    if value is None or isinstance(value, (bool, int, float)):
        return value
    if type(value).__name__ == "long":
        return value
    if isinstance(value, dict):
        mapped = Dictionary[String, Object]()
        for key, item in value.items():
            mapped[String(str(key))] = _clr(item)
        return mapped
    if isinstance(value, (list, tuple)):
        mapped = List[Object]()
        for item in value:
            mapped.Add(_clr(item))
        return mapped
    if isinstance(value, str):
        return value
    return str(value)


def _is(token, kind):
    return bool(token.Equals(kind))  # pyright: ignore[reportAttributeAccessIssue]


def _read(reader, token_type):
    token = reader.TokenType
    if _is(token, token_type.Null):
        return None
    if _is(token, token_type.StartObject):
        return _read_object(reader, token_type)
    if _is(token, token_type.StartArray):
        return _read_array(reader, token_type)
    return _read_scalar(reader, token, token_type)


def _read_object(reader, token_type):
    result = {}
    while reader.Read():
        if _is(reader.TokenType, token_type.EndObject):
            return result
        key = str(reader.Value)
        if not reader.Read():
            raise ValueError(_TRUNCATED_JSON)
        result[key] = _read(reader, token_type)
    raise ValueError(_TRUNCATED_JSON)


def _read_array(reader, token_type):
    items = []
    while reader.Read():
        if _is(reader.TokenType, token_type.EndArray):
            return items
        items.append(_read(reader, token_type))
    raise ValueError(_TRUNCATED_JSON)


def _read_scalar(reader, token, token_type):
    value = reader.Value
    if _is(token, token_type.Integer):
        return int(str(value))
    if _is(token, token_type.Float):
        return float(str(value))
    if _is(token, token_type.Boolean):
        return bool(value)
    return str(value)
