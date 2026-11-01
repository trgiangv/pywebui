# -*- coding: utf-8 -*-
"""Browser transport: FastAPI on a loopback port.

Needs CPython with the packages in ``HTTP_REQUIREMENTS``, from ``packages_dir``
when it exists. Importing this package under IronPython, or without those
packages, raises at once.
"""

from __future__ import print_function, division

import os
import sys

from pywebui.compat import CPYTHON
from pywebui.errors import MissingDependencyError, UnsupportedRuntimeError
from pywebui.runtime import HTTP_REQUIREMENTS, packages_dir

if not CPYTHON:
    raise UnsupportedRuntimeError(
        "pywebui.http needs CPython. Start the script with '#! python3', "
        "or use pywebui.webview, which also runs on IronPython."
    )

_packages = packages_dir("cp{0}{1}".format(*sys.version_info[:2]))
if os.path.isdir(_packages):
    sys.path.insert(0, _packages)

from pywebui._check import unmet  # noqa: E402

_unmet = unmet(HTTP_REQUIREMENTS)
if _unmet:
    raise MissingDependencyError(
        "pywebui.http needs {0}. Install with: python -m pip install {1}".format(
            ", ".join(_unmet), " ".join('"{0}"'.format(spec) for spec in _unmet)
        )
    )

from pywebui.http.server import HttpSink, HttpTransport  # noqa: E402

__all__ = ["HttpSink", "HttpTransport"]
