# -*- coding: utf-8 -*-
"""WPF WebView2 control — loads managed DLLs then re-exports the CLR type."""

from __future__ import print_function, division

from pyrevit_webview.dotnet import load_bin

load_bin()

from Microsoft.Web.WebView2.Wpf import WebView2  # noqa: E402

__all__ = ["WebView2"]
