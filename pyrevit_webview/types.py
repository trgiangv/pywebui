# -*- coding: utf-8 -*-
"""Shared type aliases — keep free of host/bridge import cycles."""

from __future__ import print_function, division

from pyrevit_webview.compat import Callable

InvokeOnUi = Callable[[Callable[[], None]], None]
