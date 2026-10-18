# -*- coding: utf-8 -*-
"""JSON through Newtonsoft.

``load_bin`` registers ``bin/Newtonsoft.Json.dll``, or the assembly Revit
already loaded under that name. Callers receive Python objects.
"""

from __future__ import print_function, division

_convert = None
_jtoken = None


def serialize(value):
    # type: (object) -> str
    convert, _token = _newtonsoft()
    return convert.SerializeObject(value)


def deserialize(text):
    # type: (str) -> object
    _convert_type, token_type = _newtonsoft()
    try:
        token = token_type.Parse(text)
    except Exception as exc:
        raise ValueError(str(exc))
    return _pythonize(token)


def _newtonsoft():
    global _convert, _jtoken
    if _convert is None:
        from pyrevit_webview.dotnet import load_bin

        load_bin()
        from Newtonsoft.Json import JsonConvert
        from Newtonsoft.Json.Linq import JToken

        _convert = JsonConvert
        _jtoken = JToken
    return _convert, _jtoken


def _pythonize(token):
    if token is None:
        return None
    kind = str(token.Type)
    if kind == "Null":
        return None
    if kind == "Object":
        return _pythonize_object(token)
    if kind == "Array":
        return _pythonize_array(token)
    if kind == "Integer":
        return int(str(token))
    if kind == "Float":
        return float(str(token))
    if kind == "Boolean":
        return str(token) == "True"
    return str(token)


def _pythonize_object(token):
    result = {}
    for prop in token.Properties():
        result[str(prop.Name)] = _pythonize(prop.Value)
    return result


def _pythonize_array(token):
    items = []
    for item in token:
        items.append(_pythonize(item))
    return items
