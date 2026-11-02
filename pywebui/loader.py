# -*- coding: utf-8 -*-
"""Load ``bin`` assemblies and the CLR types the host imports.

The CLR runtime is already running under IronPython or pythonnet. This module
registers DLLs and imports WebView2 / System types onto itself.
"""

from __future__ import print_function, division

import os
import types

from pywebui.compat import TYPE_CHECKING, Set, Type, cast

if TYPE_CHECKING:
    from Microsoft.Web.WebView2.Core import (
        CoreWebView2 as _CoreWebView2,
        CoreWebView2Environment as _CoreWebView2Environment,
        CoreWebView2EnvironmentOptions as _CoreWebView2EnvironmentOptions,
        CoreWebView2HostResourceAccessKind as _CoreWebView2HostResourceAccessKind,
        CoreWebView2InitializationCompletedEventArgs as _InitArgs,
        CoreWebView2NavigationCompletedEventArgs as _NavCompletedArgs,
        CoreWebView2NavigationStartingEventArgs as _NavStartingArgs,
    )
    from Microsoft.Web.WebView2.Wpf import WebView2 as _WpfWebView2
    from System import Action as _Action
    from System.Windows.Threading import DispatcherPriority as _DispatcherPriority

_BIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")  # type: str
_bin_loaded = False
_WPF_ASSEMBLIES = ("WindowsBase", "PresentationCore", "PresentationFramework")

Action = None
DispatcherPriority = None
CoreWebView2 = None
CoreWebView2Environment = None
CoreWebView2EnvironmentOptions = None
CoreWebView2HostResourceAccessKind = None
CoreWebView2InitializationCompletedEventArgs = None
CoreWebView2NavigationCompletedEventArgs = None
CoreWebView2NavigationStartingEventArgs = None
WebView2 = None
if TYPE_CHECKING:
    Action = cast(Type[_Action], Action)
    DispatcherPriority = cast(Type[_DispatcherPriority], DispatcherPriority)
    CoreWebView2 = cast(Type[_CoreWebView2], CoreWebView2)
    CoreWebView2Environment = cast(Type[_CoreWebView2Environment], CoreWebView2Environment)
    CoreWebView2EnvironmentOptions = cast(
        Type[_CoreWebView2EnvironmentOptions], CoreWebView2EnvironmentOptions
    )
    CoreWebView2HostResourceAccessKind = cast(
        Type[_CoreWebView2HostResourceAccessKind], CoreWebView2HostResourceAccessKind
    )
    CoreWebView2InitializationCompletedEventArgs = cast(
        Type[_InitArgs], CoreWebView2InitializationCompletedEventArgs
    )
    CoreWebView2NavigationCompletedEventArgs = cast(
        Type[_NavCompletedArgs], CoreWebView2NavigationCompletedEventArgs
    )
    CoreWebView2NavigationStartingEventArgs = cast(
        Type[_NavStartingArgs], CoreWebView2NavigationStartingEventArgs
    )
    WebView2 = cast(Type[_WpfWebView2], WebView2)


def _appdomain_names():
    # type: () -> Set[str]
    from System import AppDomain

    names = set()
    for assembly in AppDomain.CurrentDomain.GetAssemblies():
        if not assembly.IsDynamic:
            names.add(assembly.GetName().Name)
    return names


def _add_reference(clr, filename, loaded):
    # type: (types.ModuleType, str, Set[str]) -> None
    """Bind a ``bin`` DLL, or the AppDomain assembly when that name is already loaded."""
    from pywebui.compat import IRONPY

    assembly_name = os.path.splitext(filename)[0]
    if assembly_name in loaded:
        clr.AddReference(assembly_name)
        return

    path = os.path.abspath(os.path.join(_BIN_DIR, filename))
    add = clr.AddReferenceToFileAndPath if IRONPY else clr.AddReference
    add(path)


def load_bin():
    # type: () -> None
    """Register ``bin/*.dll`` with the CLR importer.

    A simple name already in the AppDomain is not loaded again. ``AddReference``
    still runs so IronPython can import the namespace.
    """
    global _bin_loaded
    if _bin_loaded:
        return
    if not os.path.isdir(_BIN_DIR):
        raise IOError("Extension bin folder not found: {0}".format(_BIN_DIR))

    import clr

    loaded = _appdomain_names()
    for name in sorted(os.listdir(_BIN_DIR)):
        if name.lower().endswith(".dll"):
            _add_reference(clr, name, loaded)
    _bin_loaded = True


def load_clr_types():
    # type: () -> None
    """Register ``bin`` DLLs, then import the CLR types stored on this module."""
    global Action, DispatcherPriority, CoreWebView2
    global CoreWebView2Environment
    global CoreWebView2EnvironmentOptions, CoreWebView2HostResourceAccessKind
    global CoreWebView2InitializationCompletedEventArgs
    global CoreWebView2NavigationCompletedEventArgs
    global CoreWebView2NavigationStartingEventArgs, WebView2

    if Action is not None:
        return

    load_bin()

    import clr

    for name in _WPF_ASSEMBLIES:
        clr.AddReference(name)

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
