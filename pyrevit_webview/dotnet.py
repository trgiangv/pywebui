# -*- coding: utf-8 -*-
"""CLR types and assembly loader — WebView2 + Revit.Async fallbacks."""

from __future__ import print_function, division

import os

from pyrevit_webview.compat import Any

_BIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")  # type: str
_bin_loaded = False  # type: bool

# Populated by bootstrap_clr()
Action = None  # type: Any
DispatcherPriority = None  # type: Any
CoreWebView2 = None  # type: Any
CoreWebView2Environment = None  # type: Any
CoreWebView2EnvironmentOptions = None  # type: Any
CoreWebView2HostResourceAccessKind = None  # type: Any
CoreWebView2InitializationCompletedEventArgs = None  # type: Any
CoreWebView2NavigationCompletedEventArgs = None  # type: Any
CoreWebView2NavigationStartingEventArgs = None  # type: Any
WebView2 = None  # type: Any


def load_bin():
    # type: () -> None
    """Register every ``*.dll`` in extension ``bin/`` with the CLR importer.

    IronPython needs ``clr.AddReference`` even when the assembly is already in
    the AppDomain — otherwise ``from Namespace import Type`` fails.
    """
    global _bin_loaded
    if _bin_loaded:
        return
    if not os.path.isdir(_BIN_DIR):
        raise IOError("Extension bin folder not found: {0}".format(_BIN_DIR))

    import clr

    from pyrevit_webview.compat import IRONPY

    for name in sorted(os.listdir(_BIN_DIR)):
        if not name.lower().endswith(".dll"):
            continue

        stem = name[:-4]
        path = os.path.abspath(os.path.join(_BIN_DIR, name))

        try:
            clr.AddReference(stem)
            continue
        except Exception:
            pass

        try:
            if IRONPY:
                clr.AddReferenceToFileAndPath(path)
            else:
                clr.AddReference(path)
        except Exception:
            continue

    _bin_loaded = True


def bootstrap_clr():
    # type: () -> None
    """Load extension bin and import CLR types used by :mod:`pyrevit_webview.host`."""
    global Action, DispatcherPriority, CoreWebView2
    global CoreWebView2Environment
    global CoreWebView2EnvironmentOptions, CoreWebView2HostResourceAccessKind
    global CoreWebView2InitializationCompletedEventArgs
    global CoreWebView2NavigationCompletedEventArgs
    global CoreWebView2NavigationStartingEventArgs, WebView2

    if Action is not None:
        return

    load_bin()

    from Microsoft.Web.WebView2.Core import (
        CoreWebView2 as _CoreWebView2,
    )
    from Microsoft.Web.WebView2.Core import (
        CoreWebView2Environment as _CoreWebView2Environment,
    )
    from Microsoft.Web.WebView2.Core import (
        CoreWebView2EnvironmentOptions as _CoreWebView2EnvironmentOptions,
    )
    from Microsoft.Web.WebView2.Core import (
        CoreWebView2HostResourceAccessKind as _CoreWebView2HostResourceAccessKind,
    )
    from Microsoft.Web.WebView2.Core import (
        CoreWebView2InitializationCompletedEventArgs as _CoreWebView2InitializationCompletedEventArgs,
    )
    from Microsoft.Web.WebView2.Core import (
        CoreWebView2NavigationCompletedEventArgs as _CoreWebView2NavigationCompletedEventArgs,
    )
    from Microsoft.Web.WebView2.Core import (
        CoreWebView2NavigationStartingEventArgs as _CoreWebView2NavigationStartingEventArgs,
    )
    from Microsoft.Web.WebView2.Wpf import WebView2 as _WebView2
    from System import Action as _Action
    from System.Windows.Threading import DispatcherPriority as _DispatcherPriority

    Action = _Action
    DispatcherPriority = _DispatcherPriority
    CoreWebView2 = _CoreWebView2
    CoreWebView2Environment = _CoreWebView2Environment
    CoreWebView2EnvironmentOptions = _CoreWebView2EnvironmentOptions
    CoreWebView2HostResourceAccessKind = _CoreWebView2HostResourceAccessKind
    CoreWebView2InitializationCompletedEventArgs = (
        _CoreWebView2InitializationCompletedEventArgs
    )
    CoreWebView2NavigationCompletedEventArgs = _CoreWebView2NavigationCompletedEventArgs
    CoreWebView2NavigationStartingEventArgs = _CoreWebView2NavigationStartingEventArgs
    WebView2 = _WebView2
