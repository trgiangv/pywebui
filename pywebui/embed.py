# -*- coding: utf-8 -*-
"""Run CPython inside a host that is not CPython, through pythonnet.

``start`` initializes the interpreter once per process and releases the GIL, so
threads started by CPython code keep running after ``run`` returns. Paths to the
pythonnet assembly and the CPython engine come from the caller.
"""

from __future__ import print_function, division

import os

import clr
from System import AppDomain

from pywebui.compat import IRONPY
from pywebui.errors import RuntimeAlreadyStartedError

_MARKER = "pywebui.embed.started"


_SETUP_SOURCE = """
import sys
import clr
for folder in reversed(folders.split("|")):
    if folder and folder not in sys.path:
        sys.path.insert(0, folder)
for assembly in references.split("|"):
    if assembly:
        clr.AddReference(assembly)
"""


def start(runtime_dll, python_dll, python_home, sys_path=(), references=()):
    # type: (str, str, str, tuple, tuple) -> None
    """Initialize pythonnet once per process.

    ``runtime_dll`` is the assembly that exposes ``Python.Runtime``, ``python_dll``
    the CPython engine DLL, ``python_home`` its folder. ``sys_path`` folders are
    put first on the interpreter's ``sys.path``, and the ``references`` assemblies
    are added with ``clr.AddReference`` so CPython code can import their namespaces.
    """
    # Every IronPython engine needs its own reference, also when the interpreter is already running.
    assembly_name = os.path.splitext(os.path.basename(runtime_dll))[0]
    if assembly_name in [
        a.GetName().Name for a in AppDomain.CurrentDomain.GetAssemblies()
    ]:
        clr.AddReference(assembly_name)
    else:
        add = clr.AddReferenceToFileAndPath if IRONPY else clr.AddReference
        add(runtime_dll)

    if AppDomain.CurrentDomain.GetData(_MARKER) is not None:
        run(_SETUP_SOURCE, folders="|".join(sys_path), references="|".join(references))
        return

    from Python.Runtime import PythonEngine, Runtime

    if PythonEngine.IsInitialized:
        raise RuntimeAlreadyStartedError(
            "Another tool already started CPython in this Revit session without releasing "
            "its GIL, so background threads would stall. Restart Revit and open this tool "
            "before any other CPython script."
        )

    Runtime.PythonDLL = python_dll
    PythonEngine.PythonHome = python_home
    PythonEngine.ProgramName = python_dll
    PythonEngine.Initialize()
    PythonEngine.BeginAllowThreads()
    AppDomain.CurrentDomain.SetData(_MARKER, True)
    run(_SETUP_SOURCE, folders="|".join(sys_path), references="|".join(references))


def run(source, **variables):
    # type: (str, **object) -> None
    """Execute CPython ``source`` in a fresh ``__main__`` scope.

    ``variables`` become globals of that scope. A Python error is raised as an
    exception whose message carries the Python traceback.
    """
    from Python.Runtime import Py, PythonException

    gil = Py.GIL()
    try:
        scope = Py.CreateScope("__main__")
        try:
            for name, value in variables.items():
                scope.Set(name, value)
            scope.Exec(source)
        except PythonException as error:
            raise RuntimeError(error.Format())
        finally:
            scope.Dispose()
    finally:
        gil.Dispose()
